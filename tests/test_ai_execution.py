from playwright.sync_api import sync_playwright

from app.ai.test_case_parser import load_latest_parsed_test_cases
from app.automation.testcase_runner import AITestRunner


def test_execute_ai_test_cases():

    # Automatically discover, load, and parse
    # the latest AI-generated test-case JSON file.
    test_cases = load_latest_parsed_test_cases()

    assert test_cases, "No AI-generated test cases found."

    with sync_playwright() as playwright:

        browser = playwright.chromium.launch(
            headless=False
        )

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

    assert failed == 0, (
        f"{failed} AI-generated test case(s) failed."
    )


