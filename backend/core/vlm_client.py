import base64
from dataclasses import dataclass
from enum import Enum
from io import BytesIO
from typing import Any, Dict, Optional, Union

import httpx
import numpy as np
from loguru import logger
from PIL import Image


class VLMProvider(str, Enum):
    OPENAI = "openai"
    QWEN = "qwen"
    MOONSHOT = "moonshot"
    OLLAMA = "ollama"


DEFAULT_ENDPOINTS = {
    VLMProvider.OPENAI: "https://api.openai.com/v1/chat/completions",
    VLMProvider.QWEN: "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generate",
    VLMProvider.MOONSHOT: "https://api.moonshot.cn/v1/chat/completions",
    VLMProvider.OLLAMA: "http://localhost:11434/api/generate",
}


@dataclass
class VLMResponse:
    summary_text: str
    confidence: float
    raw_output: Dict[str, Any]


class VLMClient:
    """Unified client that wraps different VLM providers (API-first, optional Ollama)."""

    def __init__(
        self,
        provider: Union[VLMProvider, str],
        model: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 15.0,
        max_retries: int = 2,
    ) -> None:
        self.provider = VLMProvider(provider)
        self.model = model
        self.api_key = api_key
        self.endpoint = base_url or DEFAULT_ENDPOINTS[self.provider]
        self.timeout = timeout
        self.max_retries = max_retries
        self.client = httpx.Client(timeout=self.timeout)

        if self.provider != VLMProvider.OLLAMA and not self.api_key:
            raise ValueError(f"Provider {self.provider.value} requires api_key")

    def close(self) -> None:
        self.client.close()

    def generate_description(
        self,
        image: Union[np.ndarray, bytes, Image.Image, str],
        prompt: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> VLMResponse:
        from .logger import log_vlm_request

        metadata = metadata or {}
        payload = self._build_payload(image, prompt, metadata)
        headers = self._build_headers()

        # 使用美化的日志
        log_vlm_request(self.provider.value, self.model)

        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.post(self.endpoint, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                self._log_cost(data)
                return self._parse_response(data)
            except (httpx.TimeoutException, httpx.HTTPError) as exc:
                last_error = exc
                logger.warning(
                    "VLM call failed (provider=%s, attempt=%s/%s): %s",
                    self.provider.value,
                    attempt + 1,
                    self.max_retries + 1,
                    exc,
                )
        raise RuntimeError(f"VLM request failed after {self.max_retries + 1} attempts") from last_error

    def _build_headers(self) -> Dict[str, str]:
        if self.provider == VLMProvider.OLLAMA:
            return {"Content-Type": "application/json"}

        header_name = "Authorization"
        token_prefix = {
            VLMProvider.OPENAI: "Bearer",
            VLMProvider.QWEN: "Bearer",
            VLMProvider.MOONSHOT: "Bearer",
        }[self.provider]

        return {
            "Authorization": f"{token_prefix} {self.api_key}",
            "Content-Type": "application/json",
        }

    def _build_payload(
        self,
        image: Union[np.ndarray, bytes, Image.Image, str],
        prompt: str,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        image_base64 = self._encode_image(image)
        merged_prompt = self._compose_prompt(prompt, metadata)

        if self.provider == VLMProvider.OLLAMA:
            return {
                "model": self.model,
                "prompt": merged_prompt,
                "images": [image_base64],
                "stream": False,
            }

        if self.provider == VLMProvider.OPENAI or self.provider == VLMProvider.MOONSHOT:
            return {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a safety monitoring assistant. Respond in Chinese when possible.",
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": merged_prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}},
                        ],
                    },
                ],
                "temperature": 0.2,
            }

        if self.provider == VLMProvider.QWEN:
            return {
                "model": self.model,
                "input": [
                    {
                        "role": "user",
                        "content": [
                            {"text": merged_prompt},
                            {"image": {"format": "png", "data": image_base64}},
                        ],
                    }
                ],
                "parameters": {"result_format": "message"},
            }

        raise NotImplementedError(f"Unsupported provider: {self.provider.value}")

    def _parse_response(self, data: Dict[str, Any]) -> VLMResponse:
        if self.provider == VLMProvider.OLLAMA:
            summary = data.get("response", "").strip()
            confidence = data.get("confidence", 0.0)
            return VLMResponse(summary, confidence, data)

        if self.provider in (VLMProvider.OPENAI, VLMProvider.MOONSHOT):
            choices = data.get("choices") or []
            summary = ""
            if choices:
                summary = choices[0].get("message", {}).get("content", "").strip()
            confidence = data.get("usage", {}).get("completion_tokens", 0) / 100.0
            return VLMResponse(summary, confidence, data)

        if self.provider == VLMProvider.QWEN:
            output = data.get("output") or {}
            summary = ""
            if "text" in output:
                summary = output["text"]
            elif "choices" in output:
                summary = output["choices"][0]["message"]["content"]
            confidence = output.get("confidence", 0.0)
            return VLMResponse(summary.strip(), confidence, data)

        raise NotImplementedError(f"Unsupported provider: {self.provider.value}")

    @staticmethod
    def _compose_prompt(prompt: str, metadata: Dict[str, Any]) -> str:
        if not metadata:
            return prompt

        meta_pairs = ", ".join(f"{key}={value}" for key, value in metadata.items())
        return f"{prompt}\n\nContext: {meta_pairs}"

    @staticmethod
    def _encode_image(image: Union[np.ndarray, bytes, Image.Image, str]) -> str:
        if isinstance(image, np.ndarray):
            image_obj = Image.fromarray(image)
        elif isinstance(image, Image.Image):
            image_obj = image
        elif isinstance(image, bytes):
            image_obj = Image.open(BytesIO(image))
        elif isinstance(image, str):
            image_obj = Image.open(image)
        else:
            raise TypeError("Unsupported image type for VLM client")

        buffer = BytesIO()
        image_obj.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def _log_cost(self, data: Dict[str, Any]) -> None:
        usage = data.get("usage")
        if not usage:
            return

        prompt_tokens = usage.get("prompt_tokens")
        completion_tokens = usage.get("completion_tokens")
        total_tokens = usage.get("total_tokens")
        logger.debug(
            "VLM usage (provider=%s, prompt_tokens=%s, completion_tokens=%s, total=%s)",
            self.provider.value,
            prompt_tokens,
            completion_tokens,
            total_tokens,
        )



