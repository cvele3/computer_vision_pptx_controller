import time
import csv
import cv2
import mediapipe as mp
import pyautogui

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Finger tips for index, middle, ring, pinky
FINGER_TIPS = [8, 12, 16, 20]

# Define predefined workflows
WORKFLOWS = [
    ["ENTER_PRESENTATION", "NEXT_SLIDE", "NEXT_SLIDE", "PREVIOUS_SLIDE", "NEXT_SLIDE", "EXIT_PRESENTATION"],
    ["ENTER_PRESENTATION", "PLAY_VIDEO", "STOP_VIDEO", "NEXT_SLIDE", "EXIT_PRESENTATION"],
    ["ENTER_PRESENTATION", "BLANK_SCREEN", "NEXT_SLIDE", "PREVIOUS_SLIDE", "STOP_VIDEO", "EXIT_PRESENTATION"]
]

# Initialize error log
ERROR_LOG_FILE = "error_log.csv"

def count_fingers(hand_landmarks):
    """
    Count fingers based on hand landmarks and detect thumb extension.
    """
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
    """
    Detect gestures based on finger count and states.
    """
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
    """
    Execute an action based on the detected gesture.
    """
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

                    finger_count, finger_states = count_fingers(hand_landmarks)
                    gesture = detect_gesture(finger_count, finger_states, frame)

            # Always display current gesture
            cv2.putText(frame, f"{gesture}", (10, 150),  # Current gesture
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

            # Only process gestures every cooldown_seconds
            if current_time - last_execution_time >= cooldown_seconds:
                if not workflow_started and gesture == "ENTER_PRESENTATION":
                    start_time = current_time
                    workflow_started = True

                if workflow_started:  # Only process gestures and log errors after workflow starts
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
