import cv2
import mediapipe as mp
import pyautogui

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Finger tips for index, middle, ring, pinky
FINGER_TIPS = [8, 12, 16, 20]

def count_fingers(hand_landmarks):
    finger_count = 0
    finger_states = []

    # Check index, middle, ring, pinky
    for tip_index in FINGER_TIPS:
        tip_y = hand_landmarks.landmark[tip_index].y
        pip_y = hand_landmarks.landmark[tip_index - 2].y
        if tip_y < pip_y:
            finger_count += 1
            finger_states.append("UP")
        else:
            finger_states.append("DOWN")

    # Check thumb (horizontal extension)
    thumb_tip_x = hand_landmarks.landmark[4].x
    thumb_base_x = hand_landmarks.landmark[2].x
    if abs(thumb_tip_x - thumb_base_x) > 0.1:
        finger_count += 1
        finger_states.insert(0, "UP")
    else:
        finger_states.insert(0, "DOWN")

    return finger_count, finger_states

def detect_gesture(finger_count, finger_states, frame):
    if finger_states[0] == "UP" and finger_count == 1:
        gesture = "ENTER_PRESENTATION"
    elif finger_count == 1:
        gesture = "NEXT_SLIDE"
    elif finger_count == 2:
        gesture = "PREVIOUS_SLIDE"
    elif finger_count == 3:
        gesture = "PLAY_VIDEO"
    elif finger_count == 4:
        gesture = "STOP_VIDEO"
    elif finger_count == 5:
        gesture = "BLANK_SCREEN"
    elif finger_count == 0:
        gesture = "EXIT_PRESENTATION"
    else:
        gesture = "UNKNOWN"

    cv2.putText(frame, f"Gesture: {gesture}", (10, 100),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    return gesture

def execute_action(action):
    if action == "ENTER_PRESENTATION":
        print("Entering Presentation Mode")
        pyautogui.press("f5")
    elif action == "NEXT_SLIDE":
        print("Next Slide")
        pyautogui.press("right")
    elif action == "PREVIOUS_SLIDE":
        print("Previous Slide")
        pyautogui.press("left")
    elif action == "PLAY_VIDEO":
        print("Play Video")
        pyautogui.press("space")
    elif action == "STOP_VIDEO":
        print("Stop Video")
        pyautogui.press("space")
    elif action == "BLANK_SCREEN":
        print("Blank Screen")
        pyautogui.press("b")
    elif action == "EXIT_PRESENTATION":
        print("Exiting Presentation Mode")
        pyautogui.press("esc")

def main():
    cap = cv2.VideoCapture(0)

    # Track the last recognized gesture
    last_gesture = "UNKNOWN"

    with mp_hands.Hands(
        model_complexity=1,
        max_num_hands=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ) as hands:
        while True:
            success, frame = cap.read()
            if not success:
                continue

            frame = cv2.flip(frame, 1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(frame_rgb)

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(
                        frame,
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS,
                        mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=4),
                        mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2)
                    )

                    finger_count, finger_states = count_fingers(hand_landmarks)
                    
                    # Show finger count on the frame
                    cv2.putText(frame, f"Fingers: {finger_count}",
                                (10, 50),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                1, (0, 255, 0), 2)

                    # Detect gesture
                    gesture = detect_gesture(finger_count, finger_states, frame)

                    # === Only execute if gesture != last_gesture AND != "UNKNOWN" ===
                    if gesture != "UNKNOWN" and gesture != last_gesture:
                        execute_action(gesture)
                        last_gesture = gesture
            else:
                # If no hand is detected, reset last_gesture
                last_gesture = "UNKNOWN"

            cv2.imshow("Hand Gesture Control - Press Q to Quit", frame)
            if cv2.waitKey(5) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
