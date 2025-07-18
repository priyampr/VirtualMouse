import cv2
import mediapipe as mp
import pyautogui
import time

# Initialize camera
cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

# Initialize mediapipe
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1,
                       min_detection_confidence=0.7,
                       min_tracking_confidence=0.7)
draw = mp.solutions.drawing_utils

# Screen dimensions
screen_w, screen_h = pyautogui.size()

# Gesture state
click_threshold = 40
drag_hold_duration = 1.0  # seconds
drag_start_time = 0
dragging = False
last_click_time = 0
click_delay = 1
smooth_x, smooth_y = 0, 0
smoothing_factor = 0.2  # For exponential smoothing

while True:
    success, frame = cap.read()
    if not success:
        continue

    frame = cv2.flip(frame, 1)
    frame_h, frame_w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    gesture_status = ""
    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            lm = hand_landmarks.landmark

            # Extract key finger tips
            index_tip = lm[8]
            thumb_tip = lm[4]
            middle_tip = lm[12]

            # Convert to screen coordinates
            cx = int(index_tip.x * screen_w)
            cy = int(index_tip.y * screen_h)
            tx = int(thumb_tip.x * screen_w)
            ty = int(thumb_tip.y * screen_h)
            mx = int(middle_tip.x * screen_w)
            my = int(middle_tip.y * screen_h)

            # Convert to camera frame coordinates (for drawing)
            ix = int(index_tip.x * frame_w)
            iy = int(index_tip.y * frame_h)
            tx_frame = int(thumb_tip.x * frame_w)
            ty_frame = int(thumb_tip.y * frame_h)
            mx_frame = int(middle_tip.x * frame_w)
            my_frame = int(middle_tip.y * frame_h)

            # Visual markers
            cv2.circle(frame, (ix, iy), 10, (0, 255, 255), cv2.FILLED)
            cv2.circle(frame, (tx_frame, ty_frame), 10, (0, 255, 0), cv2.FILLED)
            cv2.circle(frame, (mx_frame, my_frame), 10, (255, 0, 0), cv2.FILLED)

            # Exponential smoothing for mouse movement
            smooth_x = smooth_x + (cx - smooth_x) * smoothing_factor
            smooth_y = smooth_y + (cy - smooth_y) * smoothing_factor
            pyautogui.moveTo(int(smooth_x), int(smooth_y), duration=0)

            # Show coordinates
            cv2.putText(frame, f"X:{int(smooth_x)} Y:{int(smooth_y)}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

            # Check pinch distance
            distance = abs(ty - cy)

            # ---------------------
            # ✏️ Click Gesture
            # ---------------------
            if distance < click_threshold:
                if time.time() - last_click_time > click_delay and not dragging:
                    pyautogui.click()
                    last_click_time = time.time()
                    gesture_status = "Click"
            else:
                gesture_status = "Move"

            # ---------------------
            # 🛠 Drag Gesture
            # ---------------------
            if distance < click_threshold:
                if not dragging and time.time() - drag_start_time > drag_hold_duration:
                    pyautogui.mouseDown()
                    dragging = True
                    gesture_status = "Drag Start"
                elif dragging:
                    pyautogui.moveTo(int(smooth_x), int(smooth_y))
                    gesture_status = "Dragging"
            else:
                drag_start_time = time.time()
                if dragging:
                    pyautogui.mouseUp()
                    dragging = False
                    gesture_status = "Drag End"

            # ---------------------
            # 📜 Scroll Gesture
            # ---------------------
            scroll_diff = abs(my - cy)
            if scroll_diff < 30:
                pyautogui.scroll(-30 if cy < my else 30)
                gesture_status = "Scroll"

            # Show gesture
            if gesture_status:
                cv2.putText(frame, gesture_status, (10, 70),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

    # Show webcam feed
    cv2.imshow("Virtual Mouse+", frame)

    # Break on ESC
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
