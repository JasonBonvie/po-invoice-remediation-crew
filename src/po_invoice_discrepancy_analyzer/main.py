#!/usr/bin/env python
import sys
from po_invoice_discrepancy_analyzer.crew import PoInvoiceDiscrepancyAnalyzerCrew

# This main file is intended to be a way for your to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the crew.
    """
    inputs = {
        'po_file_path': '/Users/bonvie/Desktop/Invoices/examplePO.png',  # Replace with your actual PO file path
        'invoice_file_path': '/Users/bonvie/Desktop/Invoices/sampleinvoice.pdf',  # Replace with your actual invoice file path
        'recipient_email': 'your-email@example.com'  # Replace with your actual email
    }
    PoInvoiceDiscrepancyAnalyzerCrew().crew().kickoff(inputs=inputs)


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        'po_file_path': 'sample_value',
        'invoice_file_path': 'sample_value',
        'recipient_email': 'sample_value'
    }
    try:
        PoInvoiceDiscrepancyAnalyzerCrew().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        PoInvoiceDiscrepancyAnalyzerCrew().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        'po_file_path': 'sample_value',
        'invoice_file_path': 'sample_value',
        'recipient_email': 'sample_value'
    }
    try:
        PoInvoiceDiscrepancyAnalyzerCrew().crew().test(n_iterations=int(sys.argv[1]), openai_model_name=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: main.py <command> [<args>]")
        sys.exit(1)

    command = sys.argv[1]
    if command == "run":
        run()
    elif command == "train":
        train()
    elif command == "replay":
        replay()
    elif command == "test":
        test()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
