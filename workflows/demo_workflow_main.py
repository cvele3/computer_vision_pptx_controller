import csv
import uuid
import openpyxl

import demo_workflow_specific as specific_flow
import demo_workflows_counting as counting_flow

EXCEL_FILE = "logs/user_performance.xlsx"
ERROR_LOG_FILE = "logs/error_log.csv"

def save_to_excel(user_uuid, results):
    """
    Save the results to the Excel file.
    """
    wb = openpyxl.load_workbook(EXCEL_FILE)
    ws = wb.active

    # Find the next available row
    row = ws.max_row + 1

    # Write the results to the Excel file
    ws.cell(row=row, column=1, value=str(user_uuid))
    for i, (elapsed_time, error_count) in enumerate(results):
        ws.cell(row=row, column=2 + i * 2, value=elapsed_time)
        ws.cell(row=row, column=3 + i * 2, value=error_count)

    wb.save(EXCEL_FILE)

def main():

    random_uuid = uuid.uuid4()
    results = []

    # Initialize error log
    with open(ERROR_LOG_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Gesture type", "Flow number", "Step", "Detected Gesture", "Expected Gesture"])

    for i, workflow in enumerate(specific_flow.WORKFLOWS):
        print(f"Processing workflow {i + 1}/{len(specific_flow.WORKFLOWS)}: {' -> '.join(workflow)}")
        try:
            elapsed_time, error_count = specific_flow.process_workflow(workflow, i + 1)
            results.append((elapsed_time, error_count))
        except Exception as e:
            print(f"Error processing workflow {i + 1}: {e}")

    for i, workflow in enumerate(counting_flow.WORKFLOWS):
        print(f"Processing workflow {i + 1}/{len(counting_flow.WORKFLOWS)}: {' -> '.join(workflow)}")
        try:
            elapsed_time, error_count = counting_flow.process_workflow(workflow, i + 1)
            results.append((elapsed_time, error_count))
        except Exception as e:
            print(f"Error processing workflow {i + 1}: {e}")
    save_to_excel(random_uuid, results)

if __name__ == "__main__":
    main()
