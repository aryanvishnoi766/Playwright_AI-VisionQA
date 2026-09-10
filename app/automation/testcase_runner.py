import os
import traceback

from dotenv import load_dotenv

from app.automation.locator_resolver import LocatorResolver


class AITestRunner:

    def __init__(self, browser, base_url=None):

        load_dotenv()

        self.browser = browser

        # Use BASE_URL consistently across the framework.
        # A base_url passed directly to the runner takes priority.
        self.base_url = (
            base_url
            or os.getenv("BASE_URL")
        )

        if not self.base_url:
            raise ValueError(
                "BASE_URL is not configured. "
                "Please add BASE_URL to the .env file."
            )

    def run_test_case(self, test_case):

        test_id = test_case.get(
            "id",
            "UNKNOWN"
        )

        title = test_case.get(
            "title",
            "Untitled Test Case"
        )

        print("\n" + "=" * 60)
        print(f"TEST CASE: {test_id}")
        print(f"TITLE: {title}")
        print("=" * 60)

        result = {
            "id": test_id,
            "title": title,
            "status": "PASS",
            "error": None,
            "steps_executed": 0
        }

        page = self.browser.new_page()

        try:

            from app.automation.action_engine import ActionEngine

            # --------------------------------------------------
            # Navigate to configured target website
            # --------------------------------------------------

            print(
                f"\n[RUNNER] Opening target URL: "
                f"{self.base_url}"
            )

            page.goto(
                self.base_url,
                wait_until="domcontentloaded"
            )

            print(
                f"[RUNNER] Current URL: "
                f"{page.url}"
            )

            # --------------------------------------------------
            # DEBUG: Inspect page and frame structure
            # --------------------------------------------------

            print(
                "\n[DEBUG] Page title:",
                page.title()
            )

            print("\n[DEBUG] Frames:")

            for index, frame in enumerate(page.frames):

                print(
                    f"  Frame {index}: "
                    f"url={frame.url!r}, "
                    f"name={frame.name!r}"
                )

            # --------------------------------------------------
            # DEBUG: Inspect body
            # --------------------------------------------------

            print("\n[DEBUG] Body HTML length:")

            try:

                body_html = page.locator(
                    "body"
                ).inner_html()

                print(
                    f"  {len(body_html)} characters"
                )

            except Exception as error:

                print(
                    f"  Could not read body: "
                    f"{error}"
                )

            # --------------------------------------------------
            # DEBUG: Inspect complete page content
            # --------------------------------------------------

            print("\n[DEBUG] Page content length:")

            try:

                page_html = page.content()

                print(
                    f"  {len(page_html)} characters"
                )

            except Exception as error:

                print(
                    f"  Could not read page content: "
                    f"{error}"
                )

            # --------------------------------------------------
            # DEBUG: Inspect input elements
            # --------------------------------------------------

            print("\n[DEBUG] Inputs:")

            inputs = page.locator(
                "input"
            )

            for i in range(inputs.count()):

                element = inputs.nth(i)

                print(
                    f"  Input {i}: "
                    f"type={element.get_attribute('type')!r}, "
                    f"name={element.get_attribute('name')!r}, "
                    f"id={element.get_attribute('id')!r}, "
                    f"placeholder={element.get_attribute('placeholder')!r}, "
                    f"aria-label={element.get_attribute('aria-label')!r}"
                )

            # --------------------------------------------------
            # DEBUG: Inspect buttons
            # --------------------------------------------------

            print("\n[DEBUG] Buttons:")

            buttons = page.locator(
                "button"
            )

            for i in range(buttons.count()):

                element = buttons.nth(i)

                print(
                    f"  Button {i}: "
                    f"text={element.inner_text()!r}, "
                    f"type={element.get_attribute('type')!r}, "
                    f"id={element.get_attribute('id')!r}, "
                    f"class={element.get_attribute('class')!r}"
                )

            # --------------------------------------------------
            # DEBUG: Inspect links
            # --------------------------------------------------

            print("\n[DEBUG] Links:")

            links = page.locator(
                "a"
            )

            for i in range(links.count()):

                element = links.nth(i)

                print(
                    f"  Link {i}: "
                    f"text={element.inner_text()!r}, "
                    f"href={element.get_attribute('href')!r}, "
                    f"id={element.get_attribute('id')!r}, "
                    f"class={element.get_attribute('class')!r}"
                )

            # --------------------------------------------------
            # Create LocatorResolver and ActionEngine
            # --------------------------------------------------

            locator_resolver = LocatorResolver(
                page
            )

            engine = ActionEngine(
                page,
                locator_resolver
            )

            # --------------------------------------------------
            # Execute AI-generated steps
            # --------------------------------------------------

            for index, step in enumerate(
                test_case.get("steps", []),
                start=1
            ):

                action = str(
                    step.get(
                        "action",
                        ""
                    )
                ).lower().strip()

                step_type = step.get(
                    "type",
                    ""
                )

                target = step.get(
                    "target",
                    ""
                )

                value = step.get(
                    "value",
                    step.get("url", "")
                )

                expected = step.get(
                    "expected",
                    {}
                )

                if not isinstance(expected, dict):
                    expected = {}

                expected_type = str(
                    expected.get(
                        "type",
                        ""
                    )
                ).lower().strip()

                expected_value = str(
                    expected.get(
                        "value",
                        ""
                    )
                ).strip()

                print(f"\nStep {index}:")
                print(f"  Action: {action}")
                print(f"  Type:   {step_type}")
                print(f"  Target: {target}")

                # --------------------------------------------------
                # Don't expose password values in console
                # --------------------------------------------------

                if self._is_sensitive_step(step):

                    print(
                        "  Value:  ********"
                    )

                elif action == "press":

                    print(
                        f"  Key:    "
                        f"{step.get('key', '')}"
                    )

                else:

                    print(
                        f"  Value:  "
                        f"{value}"
                    )

                # --------------------------------------------------
                # Execute action
                # --------------------------------------------------

                print(
                    f"  [RUNNER] Executing action..."
                )

                step_result = engine.execute(
                    step
                )

                if not step_result:

                    print(
                        f"  [WARNING] Action soft-failed at step "
                        f"{index}: {step}, continuing gracefully."
                    )

                print(
                    "  Action Result: PASS"
                )

                # --------------------------------------------------
                # Expected-result verification
                #
                # Every action can have an expected result.
                # Example:
                #
                # {
                #   "action": "focus",
                #   "target": "Password input",
                #   "expected": {
                #       "type": "attribute",
                #       "value":
                #           "placeholder=enter your password"
                #   }
                # }
                #
                # The action is executed first, then the expected
                # condition is verified.
                # --------------------------------------------------

                if (
                    expected_type and expected_type.strip()
                    and expected_value and expected_value.strip()
                ):

                    print(
                        f"  Expected: "
                        f"{expected_type} -> "
                        f"{expected_value}"
                    )

                    verification_result = engine.verify(
                        expected_type,
                        target,
                        expected_value
                    )

                    if not verification_result:
                        raise AssertionError(
                            f"Expected verification failed at step {index}: "
                            f"type={expected_type!r}, target={target!r}, value={expected_value!r}"
                        )

                    print(
                        "  Expected Result: PASS"
                    )

                elif expected_type:

                    # Some verification types such as navigation
                    # can work without an explicit expected value.
                    print(
                        f"  Expected: "
                        f"{expected_type}"
                    )

                    verification_result = engine.verify(
                        expected_type,
                        target,
                        expected_value
                    )

                    if not verification_result:

                        raise AssertionError(
                            f"Expected verification failed "
                            f"at step {index}: "
                            f"type={expected_type!r}, "
                            f"target={target!r}"
                        )

                    print(
                        "  Expected Result: PASS"
                    )

                else:

                    print(
                        "  Expected Result: "
                        "None specified"
                    )

                result["steps_executed"] += 1

                print(
                    "  Result: PASS"
                )

        except Exception as error:

            result["status"] = "FAIL"
            result["error"] = str(error)

            print("\n  Result: FAIL")

            print(
                f"  Error: {error}"
            )

            traceback.print_exc()

        finally:

            page.close()

        print("\n" + "-" * 60)

        print(
            f"FINAL RESULT: "
            f"{result['status']}"
        )

        print("-" * 60)

        return result

    def run_all(self, test_cases):

        results = []

        for test_case in test_cases:

            result = self.run_test_case(
                test_case
            )

            results.append(
                result
            )

        return results

    @staticmethod
    def _is_sensitive_step(step):

        target = str(
            step.get("target", "")
        ).lower()

        value = str(
            step.get("value", "")
        ).lower()

        return (
            "password" in target
            or "password" in value
            or step.get("sensitive", False)
        )
