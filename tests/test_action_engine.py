from unittest.mock import MagicMock

from app.automation.action_engine import ActionEngine


def test_click_action():
    page = MagicMock()
    engine = ActionEngine(page)

    locator = MagicMock()
    engine.locator_resolver.resolve = MagicMock(return_value=locator)

    engine.execute({
        "action": "click",
        "target": "Login"
    })

    engine.locator_resolver.resolve.assert_called_once_with("Login")
    locator.click.assert_called_once()


def test_fill_action():
    page = MagicMock()
    engine = ActionEngine(page)

    locator = MagicMock()
    engine.locator_resolver.resolve = MagicMock(return_value=locator)

    engine.execute({
        "action": "fill",
        "target": "Username",
        "value": "Aryan"
    })

    engine.locator_resolver.resolve.assert_called_once_with("Username")
    locator.fill.assert_called_once_with("Aryan")


def test_navigate_action():
    page = MagicMock()
    engine = ActionEngine(page)

    engine.execute({
        "action": "navigate",
        "url": "https://example.com"
    })

    page.goto.assert_called_once_with(
        "https://example.com",
        wait_until="commit",
        timeout=30000
    )


def test_verify_action():
    page = MagicMock()
    engine = ActionEngine(page)

    locator = MagicMock()
    locator.is_visible.return_value = True

    engine.locator_resolver.resolve = MagicMock(return_value=locator)

    result = engine.execute({
        "action": "verify",
        "type": "element",
        "target": "Dashboard",
        "value": "Visible"
    })

    engine.locator_resolver.resolve.assert_called_once_with("Dashboard")
    assert result is True

def test_press_action():
    page = MagicMock()
    engine = ActionEngine(page)

    locator = MagicMock()
    engine.locator_resolver.resolve = MagicMock(return_value=locator)

    engine.execute({
        "action": "press",
        "target": "Username",
        "key": "Enter"
    })

    engine.locator_resolver.resolve.assert_called_once_with("Username")
    locator.press.assert_called_once_with("Enter")


def test_wait_action():
    page = MagicMock()
    engine = ActionEngine(page)

    engine.execute({
        "action": "wait",
        "seconds": 2
    })

    page.wait_for_timeout.assert_called_once_with(2000)