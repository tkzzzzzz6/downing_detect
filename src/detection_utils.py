import cv2
import numpy as np

def draw_river_mask(frame, masks):
    height, width = frame.shape[:2]
    river_mask = np.zeros((height, width), dtype=np.uint8)
    
    for mask in masks:
        seg = mask.xy[0].astype(np.int32)
        if len(seg) > 0:
            cv2.fillPoly(river_mask, [seg], 255)
            
            alpha = 0.4
            overlay = frame.copy()
            cv2.fillPoly(overlay, [seg], (0, 0, 255))
            cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
            
            cv2.polylines(frame, [seg], True, (255, 255, 255), 2)
            
            label = "River"
            x, y, w, h = cv2.boundingRect(seg)
            text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)[0]
            text_x = x
            text_y = y + text_size[1] + 10
            cv2.rectangle(frame, (text_x, text_y - text_size[1] - 10), (text_x + text_size[0], text_y), (255, 255, 255), -1)
            cv2.putText(frame, label, (text_x, text_y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
    
    return river_mask

def draw_person_boxes(frame, boxes, river_mask):
    height, width = frame.shape[:2]
    person_detected = False
    max_overlap_ratio = 0
    
    for box in boxes:
        if int(box.cls) == 0:  # 假设 0 是 'person'
            b = box.xyxy[0].cpu().numpy().astype(int)
            track_id = box.id.int().cpu().item() if box.id is not None else None
            label = f"Person {track_id}" if track_id is not None else "Person"
            
            person_mask = np.zeros((height, width), dtype=np.uint8)
            cv2.rectangle(person_mask, (b[0], b[1]), (b[2], b[3]), 255, -1)
            
            overlap = cv2.bitwise_and(river_mask, person_mask)
            overlap_ratio = np.sum(overlap) / np.sum(person_mask) if np.sum(person_mask) > 0 else 0

            if overlap_ratio > 0.90:
                person_detected = True
                max_overlap_ratio = max(max_overlap_ratio, overlap_ratio)
            
            cv2.rectangle(frame, (b[0], b[1]), (b[2], b[3]), (0, 255, 0), 2)
            
            text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)[0]
            cv2.rectangle(frame, (b[0], b[1] - text_size[1] - 10), (b[0] + text_size[0], b[1]), (0, 255, 0), -1)
            cv2.putText(frame, label, (b[0], b[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
    
    return person_detected, max_overlap_ratio

def draw_warning(frame):
    height, width = frame.shape[:2]
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (width, height), (0, 0, 255), -1)
    cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)

    warning_text = "Warning: Drowning danger detected!"
    font_scale = 2.0
    thickness = 4
    text_size = cv2.getTextSize(warning_text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)[0]
    text_x = (width - text_size[0]) // 2
    text_y = (height + text_size[1]) // 2

    cv2.putText(frame, warning_text, (text_x+2, text_y+2), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), thickness*2)
    cv2.putText(frame, warning_text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), thickness)

def draw_info(frame, info_message):
    height, width = frame.shape[:2]
    font_scale = 1.0
    thickness = 2
    text_size = cv2.getTextSize(info_message, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)[0]
    text_x = 10
    text_y = height - 20

    cv2.rectangle(frame, (text_x, text_y - text_size[1] - 10), (text_x + text_size[0], text_y + 10), (0, 0, 0), -1)
    cv2.putText(frame, info_message, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), thickness)