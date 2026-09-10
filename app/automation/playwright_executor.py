from pathlib import Path
import os

from playwright.sync_api import sync_playwright


URL = "https://rahulshettyacademy.com/client"


def test_valid_login():

    project_root = Path(__file__).resolve().parents[2]

    # Folder for all failure screenshots
    failure_dir = project_root / "output" / "failures"
    failure_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            print(f"\nOpening {os.getenv('BASE_URL')}...")
            page.goto(os.getenv("BASE_URL"))

            from app.automation.locator_resolver import LocatorResolver
            resolver = LocatorResolver(page)

            print("Entering email...")
            resolver.resolve("Email input").fill(os.getenv("TEST_EMAIL"))

            print("Entering password...")
            resolver.resolve("Password input").fill(os.getenv("TEST_PASSWORD"))

            print("Clicking Login...")
            resolver.resolve("Login button").click()

            page.wait_for_load_state("networkidle")

            # Verify login success
            if "/dashboard" in page.url:

                print("\nTEST PASSED")
                print("User successfully logged in.")

            else:

                print("\nTEST FAILED")
                print("Login was not successful.")
                print("Current URL:", page.url)

                failure_screenshot = (
                    failure_dir / "login_failure.png"
                )

                page.screenshot(
                    path=str(failure_screenshot),
                    full_page=True
                )

                print(
                    f"Failure screenshot saved: {failure_screenshot}"
                )

        except Exception as error:

            print("\nTEST ERROR")
            print(error)

            error_screenshot = (
                failure_dir / "login_error.png"
            )

            page.screenshot(
                path=str(error_screenshot),
                full_page=True
            )

            print(
                f"Error screenshot saved: {error_screenshot}"
            )

            raise

        finally:
            browser.close()


if __name__ == "__main__":
    test_valid_login()