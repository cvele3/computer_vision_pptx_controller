import time
import csv
import cv2
import mediapipe as mp
import pyautogui

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Define workflows for both specific and counting gestures
WORKFLOWS_SPECIFIC = [
    ["PRESENTATION_MODE_ON", "NEXT_SLIDE", "NEXT_SLIDE", "NEXT_SLIDE", "PREVIOUS_SLIDE", "NEXT_SLIDE", "NEXT_SLIDE", "PLAY_VIDEO", "STOP_VIDEO", "QUESTION_BLOCK", "QUESTION_BLOCK", "NEXT_SLIDE", "PRESENTATION_MODE_OFF"],
    ["PRESENTATION_MODE_ON", "NEXT_SLIDE", "PLAY_VIDEO", "STOP_VIDEO", "QUESTION_BLOCK", "QUESTION_BLOCK", "NEXT_SLIDE", "PREVIOUS_SLIDE", "QUESTION_BLOCK", "QUESTION_BLOCK", "NEXT_SLIDE", "NEXT_SLIDE", "NEXT_SLIDE" ,"PRESENTATION_MODE_OFF"],
    ["PRESENTATION_MODE_ON", "NEXT_SLIDE", "NEXT_SLIDE", "NEXT_SLIDE", "PREVIOUS_SLIDE", "NEXT_SLIDE", "NEXT_SLIDE", "PLAY_VIDEO", "STOP_VIDEO", "QUESTION_BLOCK", "QUESTION_BLOCK", "NEXT_SLIDE", "PRESENTATION_MODE_OFF"]
]

WORKFLOWS_COUNTING = [
    ["PRESENTATION_MODE_ON", "NEXT_SLIDE", "NEXT_SLIDE", "NEXT_SLIDE", "PREVIOUS_SLIDE", "NEXT_SLIDE", "NEXT_SLIDE", "PLAY_VIDEO", "STOP_VIDEO", "QUESTION_BLOCK", "QUESTION_BLOCK", "NEXT_SLIDE", "PRESENTATION_MODE_OFF"],
    ["PRESENTATION_MODE_ON", "NEXT_SLIDE", "PLAY_VIDEO", "STOP_VIDEO", "QUESTION_BLOCK", "QUESTION_BLOCK", "NEXT_SLIDE", "PREVIOUS_SLIDE", "QUESTION_BLOCK", "QUESTION_BLOCK", "NEXT_SLIDE", "NEXT_SLIDE", "NEXT_SLIDE" ,"PRESENTATION_MODE_OFF"],
    ["PRESENTATION_MODE_ON", "NEXT_SLIDE", "NEXT_SLIDE", "NEXT_SLIDE", "PREVIOUS_SLIDE", "NEXT_SLIDE", "NEXT_SLIDE", "PLAY_VIDEO", "STOP_VIDEO", "QUESTION_BLOCK", "QUESTION_BLOCK", "NEXT_SLIDE", "PRESENTATION_MODE_OFF"]
]

# CSV file for logging user performance
USER_PERFORMANCE_FILE = "user_performance.csv"

# Gesture Detection Functions
def count_fingers(hand_landmarks):
    """Count fingers based on hand landmarks and detect thumb extension."""
    FINGER_TIPS = [8, 12, 16, 20]  # Index, Middle, Ring, Pinky
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

def detect_gesture_specific(hand_landmarks):
    """Detect specific gestures based on finger count and thumb logic."""
    finger_count, finger_states = count_fingers(hand_landmarks)
    if finger_states == ["DOWN", "UP", "UP", "DOWN", "DOWN"]:
        return "QUESTION_BLOCK"
    elif finger_states == ["DOWN", "UP", "DOWN", "DOWN", "DOWN"]:
        return "NEXT_SLIDE"
    elif finger_states == ["DOWN", "DOWN", "DOWN", "DOWN", "UP"]:
        return "PREVIOUS_SLIDE"
    elif finger_states == ["DOWN", "DOWN", "UP", "UP", "UP"]:
        return "PLAY_VIDEO"
    elif finger_count == 4:
        return "STOP_VIDEO"
    elif finger_states == ["UP", "DOWN", "DOWN", "DOWN", "UP"]:
        return "PRESENTATION_MODE_ON"
    elif finger_states == ["UP", "UP", "DOWN", "DOWN", "DOWN"]:
        return "PRESENTATION_MODE_OFF"
    return "UNKNOWN"

def detect_gesture_counting(hand_landmarks):
    """Detect counting gestures based on the number of raised fingers."""
    finger_count, _ = count_fingers(hand_landmarks)
    if finger_count == 0:
        return "EXIT_PRESENTATION"
    elif finger_count == 1:
        return "NEXT_SLIDE"
    elif finger_count == 2:
        return "PREVIOUS_SLIDE"
    elif finger_count == 3:
        return "PLAY_VIDEO"
    elif finger_count == 4:
        return "STOP_VIDEO"
    elif finger_count == 5:
        return "BLANK_SCREEN"
    return "UNKNOWN"

# Execute a gesture
def execute_action(action):
    """Execute an action based on the detected gesture."""
    if action == "PRESENTATION_MODE_ON":
        print("Entering Presentation Mode")
        pyautogui.press("f5")
    elif action == "PRESENTATION_MODE_OFF":
        print("Exiting Presentation Mode")
        pyautogui.press("esc")
    elif action == "QUESTION_BLOCK":
        print("Blank Screen")
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

# Log errors
def log_error(user, gesture_type, flow_index, error_count, error_types):
    """Log user performance into a CSV file."""
    with open(USER_PERFORMANCE_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([user, gesture_type, flow_index, error_count, ",".join(error_types)])

# Process workflow
def process_workflow(workflow, gesture_type, user, detect_gesture_func):
    """Process a single workflow."""
    cap = cv2.VideoCapture(0)
    step_index = 0
    errors = []
    start_time = time.time()

    with mp_hands.Hands(model_complexity=1, max_num_hands=1, min_detection_confidence=0.5, min_tracking_confidence=0.5) as hands:
        while step_index < len(workflow):
            success, frame = cap.read()
            if not success:
                continue

            frame = cv2.flip(frame, 1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(frame_rgb)
            detected_gesture = "UNKNOWN"

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    detected_gesture = detect_gesture_func(hand_landmarks)

            # Process gesture
            if detected_gesture == workflow[step_index]:
                execute_action(detected_gesture)
                step_index += 1
            elif detected_gesture != "UNKNOWN":
                errors.append(detected_gesture)

            # Display frame
            cv2.putText(frame, f"Step: {step_index}/{len(workflow)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
            cv2.putText(frame, f"Gesture: {detected_gesture}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.imshow("Hand Gesture Workflow", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cap.release()
    cv2.destroyAllWindows()

    # Log errors
    elapsed_time = time.time() - start_time
    log_error(user, gesture_type, len(workflow), len(errors), errors)
    print(f"{gesture_type} Workflow {len(workflow)} completed in {elapsed_time:.2f} seconds.")

# Main Function
def main():
    user = input("Enter your name: ")

    # Initialize CSV
    with open(USER_PERFORMANCE_FILE, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["User", "Gesture Type", "Flow Index", "Error Count", "Error Types"])

    # Process Specific Gestures
    for i, workflow in enumerate(WORKFLOWS_SPECIFIC, start=1):
        print(f"Starting Specific Flow {i}...")
        process_workflow(workflow, "Specific", user, detect_gesture_specific)

    # Process Counting Gestures
    for i, workflow in enumerate(WORKFLOWS_COUNTING, start=1):
        print(f"Starting Counting Flow {i}...")
        process_workflow(workflow, "Counting", user, detect_gesture_counting)

if __name__ == "__main__":
    main()
