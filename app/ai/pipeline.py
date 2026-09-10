import json
from pathlib import Path

from app.ai.vision_analyzer import analyze_screenshot
from app.ai.case_generator import generate_test_cases
from app.ai.bdd_exporter import export_test_cases_to_feature


def get_screenshots():
    screenshots_dir = (
        Path(__file__).resolve().parents[2]
        / "input"
        / "screenshots"
    )

    supported_extensions = {".png", ".jpg", ".jpeg"}

    return [
        file
        for file in screenshots_dir.iterdir()
        if file.is_file()
        and file.suffix.lower() in supported_extensions
    ]


def run_pipeline():

    project_root = Path(__file__).resolve().parents[2]

    # Output directories
    analysis_dir = project_root / "output" / "analysis"
    test_cases_dir = project_root / "output" / "test_cases"

    analysis_dir.mkdir(parents=True, exist_ok=True)
    test_cases_dir.mkdir(parents=True, exist_ok=True)

    screenshots = get_screenshots()

    if not screenshots:
        print("No screenshots found.")
        return

    for screenshot in screenshots:

        print(f"\nProcessing: {screenshot.name}")

        # File names
        screenshot_name = screenshot.stem

        analysis_file = (
            analysis_dir / f"{screenshot_name}_analysis.json"
        )

        test_cases_file = (
            test_cases_dir / f"{screenshot_name}_test_cases.json"
        )

        # Step 1: Analyze screenshot

        print("\n[1] Analyzing screenshot with Gemini...")

        ui_analysis = analyze_screenshot(screenshot)

        print("UI analysis completed.")

        # Save UI analysis
        with open(analysis_file, "w", encoding="utf-8") as file:
            json.dump(
                ui_analysis,
                file,
                indent=2,
                ensure_ascii=False
            )

        print(f"Analysis saved: {analysis_file}")

        # Step 2: Generate test cases

        print("\n[2] Generating QA test cases...")

        test_cases = generate_test_cases(ui_analysis)

        print("Test case generation completed.")

        # Save test cases
        with open(test_cases_file, "w", encoding="utf-8") as file:
            json.dump(
                test_cases,
                file,
                indent=2,
                ensure_ascii=False
            )

        print(f"Test cases saved: {test_cases_file}")

        # Step 3: Export to Cucumber BDD Feature file
        print("\n[3] Exporting test cases to BDD Feature file...")
        export_test_cases_to_feature(test_cases_file)

        # Step 3: Display results

        print("\nUI ANALYSIS")
        print(json.dumps(ui_analysis, indent=2))

        print("\nGENERATED TEST CASES")
        print(json.dumps(test_cases, indent=2))

        print("\n----------------------------------------")
        print("Pipeline completed successfully.")
        print("----------------------------------------")


if __name__ == "__main__":
    run_pipeline()