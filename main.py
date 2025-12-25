import cv2
import pandas as pd
from ultralytics import YOLO
from tracker import Tracker
import time
import os

model = YOLO('yolov8s.pt')

def RGB(event, x, y, flags, param):
    if event == cv2.EVENT_MOUSEMOVE:  
        colorsBGR = [x, y]
        print(colorsBGR)

cv2.namedWindow('frames')
cv2.setMouseCallback('frames', RGB)

cap = cv2.VideoCapture('highway.mp4')

class_list = ['person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush']

count = 0
tracker = Tracker()

red_line_y = 198
blue_line_y = 268
offset = 6

down = {}
up = {}
counter_down = []
counter_up = []

# Two new dictionaries to save speed
speed_store_down = {}
speed_store_up = {}

if not os.path.exists('detected_frames'):
    os.makedirs('detected_frames')

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    count += 1
    frame = cv2.resize(frame, (1020, 500))

    results = model.predict(frame)
    a = results[0].boxes.data
    px = pd.DataFrame(a).astype("float")
    
    list = []
    
    for index, row in px.iterrows():
        x1 = int(row[0])
        y1 = int(row[1])
        x2 = int(row[2])
        y2 = int(row[3])
        d = int(row[5])
        c = class_list[d]
        
        if 'car' in c or 'bus' in c or 'truck' in c:
            list.append([x1, y1, x2, y2])
            
    bbox_id = tracker.update(list)
    
    for bbox in bbox_id:
        x3, y3, x4, y4, id = bbox
        cx = int(x3 + x4) // 2
        cy = int(y3 + y4) // 2

        # 1. Going DOWN
        if red_line_y < (cy + offset) and red_line_y > (cy - offset):
            down[id] = time.time()
        
        if id in down:
            if blue_line_y < (cy + offset) and blue_line_y > (cy - offset):
                elapsed_time = time.time() - down[id]
                
                if counter_down.count(id) == 0:
                    counter_down.append(id)
                    distance = 25 
                    a_speed_ms = distance / elapsed_time
                    a_speed_kh = a_speed_ms * 3.6
                    
                    # Speed ​​is saved in a dictionary.
                    speed_store_down[id] = int(a_speed_kh)

        # 2. Going UP
        if blue_line_y < (cy + offset) and blue_line_y > (cy - offset):
            up[id] = time.time()
            
        if id in up:
            if red_line_y < (cy + offset) and red_line_y > (cy - offset):
                elapsed1_time = time.time() - up[id]
                
                if counter_up.count(id) == 0:
                    counter_up.append(id)
                    distance1 = 25 
                    a_speed_ms1 = distance1 / elapsed1_time
                    a_speed_kh1 = a_speed_ms1 * 3.6
                    
                    # Speed ​​is saved in a dictionary.
                    speed_store_up[id] = int(a_speed_kh1)

        # --- Display Logic ---
        
        # Drawing Bounding Box (always visible)
        cv2.rectangle(frame, (x3, y3), (x4, y4), (0, 255, 0), 2)
        
        # Checks to see if the speed of vehicles going DOWN has been saved previously.
        if id in speed_store_down:
            speed = speed_store_down[id]
            cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)
            cv2.putText(frame, str(speed) + ' Km/h', (x4, y4), cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 255, 255), 1)
            
        # Checks to see if the speed of UP vehicles has been saved previously.
        if id in speed_store_up:
            speed = speed_store_up[id]
            cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)
            cv2.putText(frame, str(speed) + ' Km/h', (x4, y4), cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 255, 255), 1)


    cv2.line(frame, (172, 198), (774, 198), (0, 0, 255), 2)
    cv2.putText(frame, ('Red Line'), (172, 198), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

    cv2.line(frame, (8, 268), (927, 268), (255, 0, 0), 2)
    cv2.putText(frame, ('Blue Line'), (8, 268), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

    cv2.putText(frame, ('Going Down - ' + str(len(counter_down))), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
    cv2.putText(frame, ('Going Up - ' + str(len(counter_up))), (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

    # ------------------ Branding ------------------
    overlay = frame.copy()
    
   # Background Box on the left side
    cv2.rectangle(overlay, (10, 460), (350, 490), (0, 0, 0), -1)
    
   # Making the box transparent
    alpha = 0.6 
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

    
    cv2.putText(frame, 'Dev: Nishaka Mahesh Jayalath', (20, 480), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    
    # ---------------------------------------------------------

    cv2.imshow("frames", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()