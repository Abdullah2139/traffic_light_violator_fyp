import os
import cv2
import django
import numpy as np
from ultralytics import YOLO
import easyocr
from datetime import datetime

# 1. Setup Django so this script can talk to your Database
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'traffic_core.settings')
django.setup()
from monitor.models import Violation

# 2. Initialize the AI Models
model = YOLO('yolo8n.pt')
reader = easyocr.Reader(['en'])

def detect_traffic_light_color(frame):
    """
    Detect traffic light color in the frame
    Returns: 'RED', 'YELLOW', 'GREEN', or 'UNKNOWN'
    """
    height, width = frame.shape[:2]
    
    # Define traffic light ROI (Region of Interest)
    # For Kaggle video, traffic light is in top-right
    x1, y1 = int(width * 0.85), int(height * 0.02)
    x2, y2 = int(width * 0.98), int(height * 0.18)
    
    traffic_light_roi = frame[y1:y2, x1:x2]
    
    if traffic_light_roi.size == 0:
        return "UNKNOWN"
    
    # Convert to HSV for better color detection
    hsv = cv2.cvtColor(traffic_light_roi, cv2.COLOR_BGR2HSV)
    
    # Define color ranges
    # Red (two ranges because red wraps around in HSV)
    lower_red1 = np.array([0, 50, 50])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 50, 50])
    upper_red2 = np.array([180, 255, 255])
    
    # Green
    lower_green = np.array([40, 50, 50])
    upper_green = np.array([70, 255, 255])
    
    # Yellow
    lower_yellow = np.array([20, 50, 50])
    upper_yellow = np.array([35, 255, 255])
    
    # Create masks
    mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask_red = mask_red1 + mask_red2
    
    mask_green = cv2.inRange(hsv, lower_green, upper_green)
    mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
    
    # Count pixels
    red_pixels = cv2.countNonZero(mask_red)
    green_pixels = cv2.countNonZero(mask_green)
    yellow_pixels = cv2.countNonZero(mask_yellow)
    
    # Determine which color is most prominent
    max_pixels = max(red_pixels, green_pixels, yellow_pixels)
    
    if max_pixels == red_pixels and red_pixels > 100:
        return "RED"
    elif max_pixels == green_pixels and green_pixels > 100:
        return "GREEN"
    elif max_pixels == yellow_pixels and yellow_pixels > 100:
        return "YELLOW"
    else:
        return "UNKNOWN"


def run_traffic_system(video_path):
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)

    # Get video properties
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Video Resolution: {frame_width}x{frame_height}")
    
    # Stop line position for Kaggle video
    STOP_LINE_Y = int(frame_height * 0.65)
    VIOLATION_ZONE_Y = int(frame_height * 0.70)
    
    print(f"Stop Line Y: {STOP_LINE_Y}")
    print(f"Violation Zone Y: {VIOLATION_ZONE_Y}")
    print("AI Engine Started... Press 'q' to stop.")
    print("Traffic light detection: ENABLED")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.resize(frame, (1280, 720))
        # Detect traffic light color
        traffic_light_color = detect_traffic_light_color(frame)
        
        # Run YOLO Detection
        results = model(frame, classes=[2, 3, 5, 7], verbose=False)

        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                label = model.names[int(box.cls[0])]
                confidence = float(box.conf[0])
                
                if confidence < 0.5:
                    continue
                
                cx, cy = (x1 + x2) // 2, y2

                # CORRECTED VIOLATION LOGIC
                if cy > VIOLATION_ZONE_Y:
                    # Vehicle crossed the line - check if light is RED
                    if traffic_light_color == "RED":
                        # REAL VIOLATION!
                        color = (0, 0, 255)  # RED
                        thickness = 3
                        violation_text = "VIOLATION"
                        
                        # Capture plate and run OCR
                        plate_y_start = int(y1 + (y2 - y1) * 0.6)
                        plate_area = frame[plate_y_start:y2, x1:x2]
                        ocr_result = reader.readtext(plate_area)
                        plate_text = ocr_result[0][1] if ocr_result else "UNKNOWN"
                        
                        # Clean plate text
                        plate_text = ''.join(c for c in plate_text if c.isalnum())
                        if len(plate_text) < 3:
                            plate_text = "UNKNOWN"
                        
                        # Save to database with debouncing
                        if not Violation.objects.filter(
                            plate_number=plate_text, 
                            vehicle_type=label
                        ).exists():
                            Violation.objects.create(
                                plate_number=plate_text.upper(),
                                vehicle_type=label.capitalize(),
                                fine_amount=500
                            )
                            print(f"RED LIGHT VIOLATION: {label} - Plate: {plate_text} - Fine: Rs. 500")
                    else:
                        # Green or Yellow light = ALLOWED to cross
                        color = (0, 255, 0)  # GREEN
                        thickness = 2
                        violation_text = "OK"
                elif cy > STOP_LINE_Y:
                    color = (0, 255, 255)  # YELLOW
                    thickness = 2
                    violation_text = "APPROACHING"
                else:
                    color = (0, 255, 0)  # GREEN
                    thickness = 2
                    violation_text = "NORMAL"
                
                # Draw bounding box
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
                cv2.putText(frame, violation_text, (x1, y1 - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        # Draw stop line
        cv2.line(frame, (0, STOP_LINE_Y), (frame_width, STOP_LINE_Y), (255, 255, 255), 2)
        cv2.putText(frame, "STOP LINE", (10, STOP_LINE_Y - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Draw violation zone
        cv2.line(frame, (0, VIOLATION_ZONE_Y), (frame_width, VIOLATION_ZONE_Y), (0, 0, 255), 2)
        cv2.putText(frame, "VIOLATION ZONE", (10, VIOLATION_ZONE_Y + 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        # Show traffic light status
        status_color = (0, 255, 0) if traffic_light_color == "GREEN" else \
                      (0, 0, 255) if traffic_light_color == "RED" else \
                      (0, 255, 255) if traffic_light_color == "YELLOW" else (255, 255, 255)
        
        cv2.putText(frame, f"Signal: {traffic_light_color}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, status_color, 2)
        
        # Add legend
        cv2.putText(frame, "Green=Normal | Yellow=Approaching | Red=Violation", 
                   (10, frame_height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        cv2.imshow("Smart Traffic System - AI Feed", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    print("\n" + "="*50)
    print("   SMART TRAFFIC VIOLATION DETECTION SYSTEM")
    print("   With Traffic Light Detection")
    print("="*50)
    print("\n--- Select Video Source ---")
    print("1. Use Kaggle Video (traffic_video_modified.mp4)")
    print("2. Use Custom Video File")
    print("3. Use Wireless Phone Camera")
    
    choice = input("\nEnter choice (1/2/3): ")

    if choice == '1':
        source = "traffic_video_modified.mp4"
    elif choice == '2':
        source = input("Enter video file path: ")
    else:
        source = "http://10.135.21.212:8080/video"

    print(f"\nLoading video: {source}")
    print("Processing... Press 'q' to quit\n")
    run_traffic_system(source)