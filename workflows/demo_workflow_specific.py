import time
import csv
import cv2
import mediapipe as mp
import pyautogui

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Define predefined workflows
WORKFLOWS = [
    ["PRESENTATION_MODE_ON", "NEXT_SLIDE", "NEXT_SLIDE", "NEXT_SLIDE", "PREVIOUS_SLIDE", "NEXT_SLIDE", "NEXT_SLIDE", "PLAY_VIDEO", "STOP_VIDEO", "QUESTION_BLOCK", "QUESTION_BLOCK", "NEXT_SLIDE", "PRESENTATION_MODE_OFF"],
    ["PRESENTATION_MODE_ON", "NEXT_SLIDE", "PLAY_VIDEO", "STOP_VIDEO", "QUESTION_BLOCK", "QUESTION_BLOCK", "NEXT_SLIDE", "PREVIOUS_SLIDE", "QUESTION_BLOCK", "QUESTION_BLOCK", "NEXT_SLIDE", "NEXT_SLIDE", "NEXT_SLIDE" ,"PRESENTATION_MODE_OFF"],
    ["PRESENTATION_MODE_ON", "NEXT_SLIDE", "NEXT_SLIDE", "NEXT_SLIDE", "PREVIOUS_SLIDE", "NEXT_SLIDE", "NEXT_SLIDE", "PLAY_VIDEO", "STOP_VIDEO", "QUESTION_BLOCK", "QUESTION_BLOCK", "NEXT_SLIDE", "PRESENTATION_MODE_OFF"]
]

# Initialize error log
ERROR_LOG_FILE = "error_log.csv"

def detect_gesture(hand_landmarks):
    """
    Detect gestures based on hand landmarks and thumb logic.
    """
    # Finger tips
    FINGER_TIPS = [8, 12, 16, 20]
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

    # Gesture classification
    if finger_states == ["DOWN", "UP", "UP", "DOWN", "DOWN"]:
        return "QUESTION_BLOCK"
    elif finger_states == ["DOWN", "UP", "DOWN", "DOWN", "DOWN"]:
        return "NEXT_SLIDE"
    elif finger_states == ["DOWN", "DOWN", "DOWN", "DOWN", "UP"]:
        return "PREVIOUS_SLIDE"
    elif finger_states == ["DOWN", "DOWN", "UP", "UP", "UP"]:
        thumb_tip_x = hand_landmarks.landmark[4].x
        index_tip_x = hand_landmarks.landmark[8].x
        thumb_tip_y = hand_landmarks.landmark[4].y
        index_tip_y = hand_landmarks.landmark[8].y
        if abs(thumb_tip_x - index_tip_x) < 0.05 and abs(thumb_tip_y - index_tip_y) < 0.05:
            return "PLAY_VIDEO"
    elif finger_count == 4:
        return "STOP_VIDEO"
    elif finger_states == ["UP", "DOWN", "DOWN", "DOWN", "UP"]:
        return "PRESENTATION_MODE_ON"
    elif finger_states == ["UP", "UP", "DOWN", "DOWN", "DOWN"]:
        return "PRESENTATION_MODE_OFF"

    return "UNKNOWN"

def execute_action(action):
    """
    Execute an action based on the detected gesture.
    """
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

def log_error(step, expected, detected, error_type):
    """
    Log errors into a CSV file with error type.
    """
    with open(ERROR_LOG_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), step, detected, expected, error_type])

def process_workflow(workflow):
    """
    Process a single workflow, track time, and log errors.
    """
    cap = cv2.VideoCapture(0)

    step_index = 0
    start_time = None
    last_execution_time = 0
    cooldown_seconds = 2  # Cooldown between gesture detections
    workflow_started = False  # Flag to indicate workflow start

    with mp_hands.Hands(
        model_complexity=1,
        max_num_hands=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ) as hands:
        while step_index < len(workflow):
            success, frame = cap.read()
            if not success:
                continue

            frame = cv2.flip(frame, 1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(frame_rgb)

            current_time = time.time()
            gesture = "UNKNOWN"

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(
                        frame,
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS,
                        mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=4),
                        mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2)
                    )

                    gesture = detect_gesture(hand_landmarks)

            # Always display current gesture
            cv2.putText(frame, f"{gesture}", (10, 150), #current gesture
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

            # Only process gestures every cooldown_seconds
            if current_time - last_execution_time >= cooldown_seconds:
                if not workflow_started and gesture == "PRESENTATION_MODE_ON":
                    start_time = current_time
                    workflow_started = True

                if workflow_started:  # Only log errors and process gestures after workflow starts
                    if gesture == workflow[step_index]:
                        execute_action(gesture)
                        step_index += 1
                    else:
                        error_type = "Misclassification" if gesture != "UNKNOWN" else "False Negative"
                        if gesture != "UNKNOWN":
                            log_error(step_index + 1, workflow[step_index], gesture, error_type)
                        

                    last_execution_time = current_time  # Update last execution time

            # Display the frame
            cv2.putText(frame, f"Step: {step_index + 1}/{len(workflow)}", (10, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
            cv2.imshow("Hand Gesture Workflow - Press Q to Quit", frame)

            if cv2.waitKey(5) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

    if start_time:
        elapsed_time = time.time() - start_time
        print(f"Workflow completed in {elapsed_time:.2f} seconds.")
    else:
        print("Workflow was not started.")


def main():
    """
    Main function to select and execute a workflow.
    """
    print("Select a workflow:")
    for i, workflow in enumerate(WORKFLOWS):
        print(f"{i + 1}: {' -> '.join(workflow)}")

    choice = int(input("Enter the number of the workflow: ")) - 1
    if 0 <= choice < len(WORKFLOWS):
        process_workflow(WORKFLOWS[choice])
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    # Initialize error log
    with open(ERROR_LOG_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Step", "Detected Gesture", "Expected Gesture", "Error Type"])

    main()
