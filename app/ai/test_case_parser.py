import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL")
TEST_EMAIL = os.getenv("TEST_EMAIL")
TEST_PASSWORD = os.getenv("TEST_PASSWORD")


def find_latest_test_case_file():
    """
    Automatically find the latest JSON test-case file.

    Searches:
        output/test_cases/

    Returns:
        Path: Latest modified JSON test-case file.

    Raises:
        FileNotFoundError: If no JSON test-case files are found.
    """

    project_root = Path(__file__).resolve().parents[2]

    test_cases_dir = project_root / "output" / "test_cases"

    if not test_cases_dir.exists():
        raise FileNotFoundError(
            f"Test case directory not found: {test_cases_dir}"
        )

    json_files = list(test_cases_dir.glob("*.json"))

    if not json_files:
        raise FileNotFoundError(
            f"No JSON test case files found in: {test_cases_dir}"
        )

    # Select the most recently modified JSON file
    latest_file = max(
        json_files,
        key=lambda file: file.stat().st_mtime
    )

    return latest_file


def load_test_cases(file_path):
    """
    Load AI-generated test cases from JSON.
    """

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"Test case file not found: {file_path}"
        )

    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    if "test_cases" not in data:
        raise ValueError(
            "Invalid test case JSON: 'test_cases' field is missing."
        )

    return data["test_cases"]


def load_latest_test_cases():
    """
    Automatically find and load the latest AI-generated
    test-case JSON file.

    Returns:
        list: Test cases from the latest JSON file.
    """

    latest_file = find_latest_test_case_file()

    return load_test_cases(latest_file)


def normalize_value(value):
    """
    Replace supported AI-generated test-data placeholders
    with values from environment variables.

    Only TEST_EMAIL and TEST_PASSWORD are supported.
    """

    if not isinstance(value, str):
        return value

    test_data = {
        "{TEST_EMAIL}": TEST_EMAIL,
        "{{TEST_EMAIL}}": TEST_EMAIL,
        "{TEST_PASSWORD}": TEST_PASSWORD,
        "{{TEST_PASSWORD}}": TEST_PASSWORD,
    }

    for placeholder, actual_value in test_data.items():
        if actual_value is not None:
            value = value.replace(placeholder, actual_value)

    return value


def get_target(step):
    """
    Read the human-readable UI target.

    Supports both:
        target

    and:
        element

    This allows the parser to handle older AI-generated
    JSON as well as the newer schema.
    """

    target = step.get("target")

    if target is None:
        target = step.get("element", "")

    if target is None:
        target = ""

    return str(target).strip()


def get_value(step):
    """
    Read and normalize the step value.
    """

    value = step.get("value", "")

    if value is None:
        value = ""

    return normalize_value(value)


def parse_test_case(test_case):
    """
    Convert one AI-generated test case into
    normalized executable steps.

    The expected object is preserved so that
    AITestRunner / ActionEngine can perform
    step-level verification.
    """

    parsed_steps = []

    for step in test_case.get("steps", []):

        action = step.get("action", "").strip().lower()
        step_type = step.get("type", "").strip().lower()

        target = get_target(step)
        value = get_value(step)

        # -------------------------------------------------
        # EXPECTED RESULT
        # -------------------------------------------------
        expected = step.get("expected", {})

        if not isinstance(expected, dict):
            expected = {}

        expected_type = str(
            expected.get("type", "") or ""
        ).strip().lower()

        expected_value = expected.get("value", "")

        if expected_value is None:
            expected_value = ""

        expected_value = normalize_value(expected_value)

        normalized_expected = {
            "type": expected_type,
            "value": expected_value
        }

        # -------------------------------------------------
        # NAVIGATE
        # -------------------------------------------------
        if action == "navigate":

            url = value if value else BASE_URL

            if not url:
                raise ValueError(
                    f"No BASE_URL available for navigation in "
                    f"test case '{test_case.get('id', '')}'."
                )

            parsed_steps.append({
                "action": "navigate",
                "type": step_type or "navigation",
                "target": target,
                "url": url,
                "expected": normalized_expected
            })

        # -------------------------------------------------
        # PRESS
        # -------------------------------------------------
        elif action == "press":

            # New schema:
            # key = "Tab"
            #
            # Older Gemini output:
            # value = "Tab"

            key = step.get("key", "")

            if not key:
                key = value

            key = normalize_value(key)

            parsed_steps.append({
                "action": "press",
                "type": step_type or "keyboard",
                "target": target,
                "key": key,
                "expected": normalized_expected
            })

        # -------------------------------------------------
        # WAIT
        # -------------------------------------------------
        elif action == "wait":

            try:
                seconds = float(value)
            except (ValueError, TypeError):
                seconds = 1

            parsed_steps.append({
                "action": "wait",
                "type": step_type or "wait",
                "target": "",
                "seconds": seconds,
                "expected": normalized_expected
            })

        # -------------------------------------------------
        # ALL OTHER ACTIONS
        # -------------------------------------------------
        else:

            parsed_steps.append({
                "action": action,
                "type": step_type,
                "target": target,
                "value": value,
                "expected": normalized_expected
            })

    return {
        "id": test_case.get("id", ""),
        "title": test_case.get("title", ""),
        "type": test_case.get("type", ""),
        "priority": test_case.get("priority", ""),
        "steps": parsed_steps,
        "expected_result": test_case.get(
            "expected_result", ""
        )
    }

def parse_all_test_cases(file_path):
    """
    Load and normalize all AI-generated test cases
    from a specific JSON file.
    """

    test_cases = load_test_cases(file_path)

    return [
        parse_test_case(test_case)
        for test_case in test_cases
    ]


def load_latest_parsed_test_cases():
    """
    Automatically find, load, and parse the latest
    AI-generated test-case JSON file.

    Returns:
        list: Normalized executable test cases.
    """

    test_cases = load_latest_test_cases()

    return [
        parse_test_case(test_case)
        for test_case in test_cases
    ]


if __name__ == "__main__":

    latest_file = find_latest_test_case_file()

    print(f"\nUsing test case file:")
    print(latest_file)

    parsed_cases = parse_all_test_cases(latest_file)

    print(f"\nLoaded {len(parsed_cases)} test cases.")

    for test_case in parsed_cases[:2]:

        print("\n--------------------------------")
        print(test_case["id"])
        print(test_case["title"])

        for step in test_case["steps"]:
            print(step)