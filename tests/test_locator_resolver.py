from playwright.sync_api import sync_playwright

from app.automation.locator_resolver import LocatorResolver


URL = "https://rahulshettyacademy.com/client"


def test_locator_resolver():

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=False)

        page = browser.new_page()

        print("\nOpening login page...")

        page.goto(URL, wait_until="domcontentloaded", timeout=60000)

        resolver = LocatorResolver(page)

        # Test Email
        email = resolver.resolve("Email input")
        print("Email input found:", email.count() if email else 0)

        # Test Password
        password = resolver.resolve("Password input")
        print("Password input found:", password.count() if password else 0)

        # Test Login button
        login_button = resolver.resolve("Login button")
        print("Login button found:", login_button.count() if login_button else 0)

        browser.close()