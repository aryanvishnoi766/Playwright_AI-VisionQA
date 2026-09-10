import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

def before_all(context):
    load_dotenv()
    context.base_url = os.getenv("BASE_URL")
    context.headless = os.getenv("HEADLESS", "true").lower() == "true"
    
    context.playwright = sync_playwright().start()
    context.browser = context.playwright.chromium.launch(headless=context.headless)

def before_scenario(context, scenario):
    context.page = context.browser.new_page()
    if context.base_url:
        context.page.goto(context.base_url, wait_until="domcontentloaded")

def after_scenario(context, scenario):
    if hasattr(context, "page") and context.page:
        context.page.close()

def after_all(context):
    if hasattr(context, "browser") and context.browser:
        context.browser.close()
    if hasattr(context, "playwright") and context.playwright:
        context.playwright.stop()
