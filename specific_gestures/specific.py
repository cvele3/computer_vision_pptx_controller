import cv2
import mediapipe as mp
import pyautogui

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Helper function to count fingers with updated thumb logic
def count_fingers(hand_landmarks):
    """
    Count fingers based on hand landmarks and detect thumb extension.
    """
    FINGER_TIPS = [8, 12, 16, 20]  # Index, Middle, Ring, Pinky
    finger_count = 0
    finger_states = []

    # Check index, middle, ring, pinky
    for tip_index in FINGER_TIPS:
        tip_y = hand_landmarks.landmark[tip_index].y
        pip_y = hand_landmarks.landmark[tip_index - 2].y
        if tip_y < pip_y:  # Finger is "up"
            finger_count += 1
            finger_states.append("UP")
        else:
            finger_states.append("DOWN")

    # Check thumb (horizontal extension)
    thumb_tip_x = hand_landmarks.landmark[4].x
    thumb_base_x = hand_landmarks.landmark[2].x
    if abs(thumb_tip_x - thumb_base_x) > 0.1:  # Thumb is extended outward
        finger_count += 1
        finger_states.insert(0, "UP")
    else:
        finger_states.insert(0, "DOWN")

    return finger_count, finger_states

# Helper function to detect gestures
def detect_gesture(hand_landmarks):
    """
    Detect gestures based on hand landmarks and thumb logic.
    """
    # Get finger count and states
    finger_count, finger_states = count_fingers(hand_landmarks)

    # Gesture classification
    if finger_states == ["DOWN", "UP", "UP", "DOWN", "DOWN"]:  # Peace Sign (Index and Middle Up)
        return "QUESTION_BLOCK"
    elif finger_states == ["DOWN", "UP", "DOWN", "DOWN", "DOWN"]:  # Index Finger Up
        return "NEXT_SLIDE"
    elif finger_states == ["DOWN", "DOWN", "DOWN", "DOWN", "UP"]:  # Pinky Finger Up
        return "PREVIOUS_SLIDE"
    elif finger_states == ["DOWN", "DOWN", "UP", "UP", "UP"]:  # OK Sign (Thumb touching Index)
        thumb_tip_x = hand_landmarks.landmark[4].x
        index_tip_x = hand_landmarks.landmark[8].x
        thumb_tip_y = hand_landmarks.landmark[4].y
        index_tip_y = hand_landmarks.landmark[8].y
        # Check proximity between thumb and index tip
        if abs(thumb_tip_x - index_tip_x) < 0.05 and abs(thumb_tip_y - index_tip_y) < 0.05:
            return "PLAY_VIDEO"
    elif finger_count == 4:  # Open Palm
        return "STOP_VIDEO"
    elif finger_states == ["UP", "DOWN", "DOWN", "DOWN", "UP"]:  # Phone Sign (Thumb and Pinky Extended)
        return "PRESENTATION_MODE_ON"
    elif finger_states == ["UP", "UP", "DOWN", "DOWN", "DOWN"]:  # Take the L Sign (Thumb and Index Extended)
        return "PRESENTATION_MODE_OFF"

    return "UNKNOWN"

# Map gestures to PowerPoint actions
def execute_action(action):
    if action == "PRESENTATION_MODE_ON":
        print("Presentation Mode On")
        pyautogui.press("f5")
    elif action == "PRESENTATION_MODE_OFF":
        print("Presentation Mode Off")
        pyautogui.press("esc")
    elif action == "QUESTION_BLOCK":
        print("Question Block (Blank Screen)")
        pyautogui.press("b")
    elif action == "STOP_VIDEO":
        print("Stop Video")
        pyautogui.press("space")
    elif action == "PLAY_VIDEO":
        print("Play Video")
        pyautogui.press("space")
    elif action == "NEXT_SLIDE":
        print("Next Slide")
        pyautogui.press("right")
    elif action == "PREVIOUS_SLIDE":
        print("Previous Slide")
        pyautogui.press("left")

# Main function
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
                    # Draw hand landmarks
                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                    # Detect gesture
                    gesture = detect_gesture(hand_landmarks)

                    # Display gesture on screen
                    cv2.putText(frame, f"Gesture: {gesture}", (10, 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                    # Execute PowerPoint action if gesture is not repeated
                    if gesture != "UNKNOWN" and gesture != last_gesture:
                        execute_action(gesture)
                        last_gesture = gesture
            else:
                # If no hand is detected, reset last_gesture
                last_gesture = "UNKNOWN"

            # Show the live frame
            cv2.imshow("Hand Gesture Control", frame)

            # Exit on 'q'
            if cv2.waitKey(5) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
