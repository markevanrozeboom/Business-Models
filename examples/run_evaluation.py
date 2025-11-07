#!/usr/bin/env python3
"""
Example script for running a business evaluation.

This demonstrates how to use the Business Evaluation System to analyze
a business idea and generate a comprehensive report.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.workflow import BusinessEvaluationWorkflow


def run_example_evaluation():
    """Run an example business evaluation."""

    # Load example business submission
    example_file = os.path.join(
        os.path.dirname(__file__),
        "example_submission.txt"
    )

    with open(example_file, "r") as f:
        business_description = f.read()

    print("=" * 80)
    print("BUSINESS EVALUATION SYSTEM - EXAMPLE RUN")
    print("=" * 80)
    print(f"\nBusiness Description:\n{business_description[:200]}...\n")
    print("Starting evaluation workflow...\n")

    # Create workflow and run evaluation
    workflow = BusinessEvaluationWorkflow()

    try:
        result = workflow.evaluate_business(
            business_description=business_description,
            save_results=True
        )

        # Print summary
        workflow.print_summary(result)

        # Print additional details
        print("\nDETAILED RESULTS")
        print("=" * 80)

        summary = workflow.get_workflow_summary(result)

        print("\nWorkflow Summary:")
        for key, value in summary.items():
            print(f"  {key}: {value}")

        if result.final_report:
            print("\n--- EXECUTIVE SUMMARY ---")
            print(result.final_report.executive_summary)

            print("\n--- KEY FINDINGS ---")
            for i, finding in enumerate(result.final_report.key_findings, 1):
                print(f"{i}. {finding}")

            print("\n--- CRITICAL ASSUMPTIONS ---")
            for i, assumption in enumerate(result.final_report.critical_assumptions, 1):
                print(f"{i}. {assumption}")

            print("\n--- NEXT STEPS ---")
            for i, step in enumerate(result.final_report.next_steps, 1):
                print(f"{i}. {step}")

        if result.is_complete:
            print("\n✅ Evaluation completed successfully!")
            return 0
        elif result.requires_human_review:
            print("\n⚠️  Evaluation requires human review before proceeding.")
            return 2
        else:
            print("\n❌ Evaluation did not complete successfully.")
            return 1

    except Exception as e:
        print(f"\n❌ Error during evaluation: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = run_example_evaluation()
    sys.exit(exit_code)
