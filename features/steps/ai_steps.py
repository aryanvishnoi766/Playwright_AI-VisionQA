import time
from behave import given, when, then
from app.automation.action_engine import ActionEngine
from app.automation.locator_resolver import LocatorResolver


@given('I am on the target page')
@given('precondition: {precondition_text}')
def step_given_precondition(context, precondition_text=None):
    if context.base_url and context.page.url == "about:blank":
        context.page.goto(context.base_url, wait_until="domcontentloaded")
    print(f"\n[BDD] Precondition met / On target page: {context.page.url}")


@when('I navigate to {url}')
def step_navigate(context, url):
    if not url.startswith("http"):
        url = f"{context.base_url.rstrip('/')}/{url.lstrip('/')}"
    context.page.goto(url, wait_until="domcontentloaded")


@when('I click on "{target}"')
def step_click(context, target):
    engine = ActionEngine(context.page)
    # Construct standard step object for ActionEngine
    step_data = {
        "action": "click",
        "target": target,
        "step": f"Click on {target}"
    }
    engine.execute_step(step_data)


@when('I fill "{target}" with "{value}"')
def step_fill(context, target, value):
    engine = ActionEngine(context.page)
    step_data = {
        "action": "fill",
        "target": target,
        "value": value,
        "step": f"Fill {target} with {value}"
    }
    engine.execute_step(step_data)


@when('I clear "{target}"')
def step_clear(context, target):
    engine = ActionEngine(context.page)
    step_data = {
        "action": "clear",
        "target": target,
        "step": f"Clear {target}"
    }
    engine.execute_step(step_data)


@when('I press key "{key}" on "{target}"')
def step_press(context, key, target):
    engine = ActionEngine(context.page)
    step_data = {
        "action": "press",
        "target": target,
        "key": key,
        "step": f"Press {key} on {target}"
    }
    engine.execute_step(step_data)


@when('I focus on "{target}"')
def step_focus(context, target):
    engine = ActionEngine(context.page)
    step_data = {
        "action": "focus",
        "target": target,
        "step": f"Focus on {target}"
    }
    engine.execute_step(step_data)


@when('I wait for {seconds:d} seconds')
@when('I wait for {seconds:f} seconds')
def step_wait(context, seconds):
    time.sleep(float(seconds))


@then('I should verify {verify_type} equals "{expected_value}" on "{target}"')
def step_verify(context, verify_type, expected_value, target):
    engine = ActionEngine(context.page)
    step_data = {
        "action": "verify",
        "target": target,
        "expected": {
            "type": verify_type,
            "value": expected_value
        },
        "step": f"Verify {verify_type} equals {expected_value} on {target}"
    }
    engine.execute_step(step_data)


@when('{step_text}')
def step_fallback(context, step_text):
    print(f"\n[BDD] Fallback executing step: {step_text}")
