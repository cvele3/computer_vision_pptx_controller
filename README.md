# Hand Gesture Controlled PowerPoint Presentation

This project allows you to control PowerPoint presentations using hand gestures detected through a webcam. The gestures are recognized using MediaPipe and OpenCV, and actions are executed using PyAutoGUI.

## Setup

### Windows

1. Create a virtual environment:
    ```sh
    python -m venv env
    ```

2. Activate the virtual environment:
    ```sh
    env\Scripts\activate
    ```

3. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```

### Linux

1. Create a virtual environment:
    ```sh
    python3 -m venv env
    ```

2. Activate the virtual environment:
    ```sh
    source env/bin/activate
    ```

3. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```

## Usage

1. Ensure your webcam is connected and working.
2. Run the main script to start the gesture detection:
    ```sh
    python workflows/demo_workflow_main.py
    ```

## Project Structure

- [finger_counting](http://_vscodecontentref_/0): Contains the script for counting fingers and detecting gestures.
- [logs](http://_vscodecontentref_/1): Contains logs for errors and user performance.
- [pptx](http://_vscodecontentref_/2): Contains PowerPoint files used in the workflows.
- [scraps](http://_vscodecontentref_/3): Contains old and experimental scripts.
- [specific_gestures](http://_vscodecontentref_/4): Contains scripts and data for specific gestures.
- [workflows](http://_vscodecontentref_/5): Contains scripts for different workflows.