# Fix PyTorch installation for Windows
Write-Host "Removing virtual environment..." -ForegroundColor Yellow
Remove-Item -Path .venv -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "Clearing UV cache..." -ForegroundColor Yellow
uv cache clean

Write-Host "Reinstalling dependencies..." -ForegroundColor Green
uv sync

Write-Host "Done! Try running: uv run backend/api.py" -ForegroundColor Green
