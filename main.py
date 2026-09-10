import os
import json
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from app.ai.pipeline import run_pipeline
from app.ai.test_case_parser import load_latest_parsed_test_cases
from app.automation.testcase_runner import AITestRunner

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is not set in .env")


def save_test_report(results):
    project_root = Path(__file__).resolve().parent
    reports_dir = project_root / "output" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = reports_dir / f"test_execution_report_{timestamp}.json"

    passed = sum(1 for r in results if r['status'] == 'PASS')
    failed = sum(1 for r in results if r['status'] == 'FAIL')

    report_data = {
        "timestamp": datetime.now().isoformat(),
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "results": results
    }

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

    print(f"\n[INFO] Test execution report saved: {report_file}")


if __name__ == "__main__":
    print("==================================================")
    print("        AI UI TESTING AUTOMATION FRAMEWORK        ")
    print("==================================================")
    print("Select an option:")
    print("  1. Run Full Pipeline (AI Analysis & Test Generation) + Test Execution")
    print("  2. Run Test Execution Only (using latest generated test cases) [DEFAULT]")
    print("  3. Run Pipeline Only (AI Analysis & Test Generation)")

    choice = input("\nEnter your choice [1-3] (default: 2): ").strip()
    if not choice:
        choice = "2"

    if choice in ("1", "3"):
        print("\n=== Running AI Pipeline (Analysis & Test Case Generation) ===")
        run_pipeline()

    if choice in ("1", "2"):
        print("\n=== Executing Test Cases ===")
        test_cases = load_latest_parsed_test_cases()

        if not test_cases:
            print("No AI-generated test cases found to execute.")
        else:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=False)
                runner = AITestRunner(browser)
                results = runner.run_all(test_cases)
                browser.close()

            print("\n\n========== AI TEST EXECUTION SUMMARY ==========")

            passed = 0
            failed = 0

            for result in results:
                print(
                    f"{result['id']} | "
                    f"{result['title']} | "
                    f"{result['status']} | "
                    f"Steps: {result['steps_executed']}"
                )

                if result["status"] == "PASS":
                    passed += 1
                else:
                    failed += 1
                    print(f"  Error: {result['error']}")

            print("-----------------------------------------------")
            print(f"Total:  {len(results)}")
            print(f"Passed: {passed}")
            print(f"Failed: {failed}")
            print("===============================================")

            save_test_report(results)
