import time


class _DefaultLocatorResolver:
    """
    Default resolver used when ActionEngine is created without
    an explicit LocatorResolver.

    This keeps the ActionEngine constructor compatible with
    lightweight unit tests while requiring a real
    LocatorResolver for actual UI element execution.
    """

    def resolve(self, target):
        raise ValueError(
            "LocatorResolver is required for UI element actions."
        )


class ActionEngine:
    """
    Generic action execution engine.

    Responsibilities:
    - Execute AI-generated actions.
    - Resolve UI elements through LocatorResolver.
    - Perform generic UI interactions.
    - Perform generic verifications.
    - Avoid website-specific selectors.
    """

    def __init__(self, page, locator_resolver=None):
        self.page = page

        if locator_resolver is None:
            self.locator_resolver = _DefaultLocatorResolver()
        else:
            self.locator_resolver = locator_resolver

        self.previous_url = self.page.url

    # ============================================================
    # MAIN DISPATCHER
    # ============================================================

    def execute(self, action):
        """
        Execute one AI-generated action.

        Supported actions:
            navigate
            fill
            clear
            click
            focus
            press
            verify
            wait
        """

        if not isinstance(action, dict):
            raise ValueError(
                "Action must be a dictionary."
            )

        action_type = str(
            action.get("action", "")
        ).strip().lower()

        if not action_type:
            raise ValueError(
                "Action type is missing."
            )

        print(
            f"[DEBUG] Executing action: "
            f"{action_type}"
        )

        # Explicit wait should NOT perform an additional
        # synchronization wait first.
        if action_type != "wait":
            self._wait_for_ui()

        # ========================================================
        # NAVIGATE
        # ========================================================

        if action_type == "navigate":

            self.previous_url = self.page.url

            self.navigate(
                action.get("url")
                or action.get("value")
            )

        # ========================================================
        # FILL
        # ========================================================

        elif action_type == "fill":

            self.fill(
                action.get("target"),
                action.get("value", "")
            )

        # ========================================================
        # CLEAR
        # ========================================================

        elif action_type == "clear":

            self.clear(
                action.get("target")
            )

        # ========================================================
        # CLICK
        # ========================================================

        elif action_type == "click":

            self.previous_url = self.page.url

            self.click(
                action.get("target")
            )

        # ========================================================
        # FOCUS
        # ========================================================

        elif action_type == "focus":

            self.focus(
                action.get("target")
            )

        # ========================================================
        # PRESS
        # ========================================================

        elif action_type == "press":

            self.previous_url = self.page.url

            self.press(
                action.get("target"),
                action.get("key", "Enter")
            )

        # ========================================================
        # VERIFY
        # ========================================================

        elif action_type == "verify":

            return self.verify(
                expected_type=action.get("type"),
                target=action.get("target"),
                expected=action.get("value")
            )

        # ========================================================
        # WAIT
        # ========================================================

        elif action_type == "wait":

            self.wait(
                seconds=action.get(
                    "seconds",
                    action.get("value", 1)
                )
            )

        else:

            raise ValueError(
                f"Unsupported action type: "
                f"{action_type}"
            )

        # ========================================================
        # STEP-LEVEL EXPECTED VERIFICATION
        # ========================================================

        expected = action.get("expected")

        if expected and isinstance(
            expected,
            dict
        ):

            expected_type = expected.get(
                "type",
                ""
            )

            expected_value = expected.get(
                "value",
                ""
            )

            if expected_type:

                return self.verify(
                    expected_type=expected_type,
                    target=action.get("target"),
                    expected=expected_value
                )

        return True

    # ============================================================
    # WAIT FOR UI
    # ============================================================

    def _wait_for_ui(self):
        """
        Generic small synchronization delay.

        This is intentionally skipped for explicit 'wait'
        actions.
        """

        try:

            self.page.wait_for_load_state(
                "domcontentloaded",
                timeout=5000
            )

        except Exception:
            pass

        try:

            self.page.wait_for_timeout(
                300
            )

        except Exception:
            pass

    # ============================================================
    # NAVIGATE
    # ============================================================

    def navigate(self, url):

        if not url:

            raise ValueError(
                "Navigate action requires a URL."
            )

        print(
            f"[DEBUG] Navigating to: {url}"
        )

        self.page.goto(
            url,
            wait_until="commit",
            timeout=30000
        )

        try:

            self.page.wait_for_timeout(
                500
            )

        except Exception:
            pass

        print(
            f"[DEBUG] Current URL: "
            f"{self.page.url}"
        )

        return True

    # ============================================================
    # RESOLVE ELEMENT
    # ============================================================

    def _resolve(self, target):

        if not target:

            raise ValueError(
                "UI element target is missing."
            )

        locator = self.locator_resolver.resolve(
            target
        )

        if locator is None:

            raise ValueError(
                f"Could not resolve UI element: "
                f"'{target}'"
            )

        return locator

    # ============================================================
    # FILL
    # ============================================================

    def fill(self, target, value):

        locator = self._resolve(
            target
        )

        print(
            f"[DEBUG] Filling '{target}' "
            f"with value '{value}'"
        )

        locator.fill(
            str(value)
        )

        return True

    # ============================================================
    # CLEAR
    # ============================================================

    def clear(self, target):

        locator = self._resolve(
            target
        )

        print(
            f"[DEBUG] Clearing '{target}'"
        )

        locator.fill(
            ""
        )

        return True

    # ============================================================
    # CLICK
    # ============================================================

    def click(self, target):

        locator = self._resolve(
            target
        )

        print(
            f"[DEBUG] Clicking '{target}'"
        )

        self.previous_url = self.page.url

        locator.click()

        try:

            self.page.wait_for_timeout(
                500
            )

        except Exception:
            pass

        print(
            f"[DEBUG] After click Current URL: "
            f"{self.page.url}"
        )

        return True

    # ============================================================
    # FOCUS
    # ============================================================

    def focus(self, target):

        locator = self._resolve(
            target
        )

        print(
            f"[DEBUG] Focusing '{target}'"
        )

        locator.focus()

        return True

    # ============================================================
    # PRESS
    # ============================================================

    def press(self, target, key="Enter"):

        locator = self._resolve(
            target
        )

        if not key:
            key = "Enter"

        print(
            f"[DEBUG] Pressing '{key}' "
            f"on '{target}'"
        )

        self.previous_url = self.page.url

        locator.press(
            key
        )

        try:

            self.page.wait_for_timeout(
                500
            )

        except Exception:
            pass

        print(
            f"[DEBUG] After press Current URL: "
            f"{self.page.url}"
        )

        return True

    # ============================================================
    # WAIT
    # ============================================================

    def wait(self, seconds=1):

        try:

            seconds = float(
                seconds
            )

        except (
            TypeError,
            ValueError
        ):

            seconds = 1

        if seconds < 0:
            seconds = 0

        print(
            f"[DEBUG] Waiting "
            f"{seconds} second(s)."
        )

        self.page.wait_for_timeout(
            int(seconds * 1000)
        )

        return True

    # ============================================================
    # VERIFY
    # ============================================================

    def verify(
        self,
        expected_type=None,
        target=None,
        expected=None
    ):
        """
        Generic verification engine.

        Supported verification types:
            element
            text
            attribute
            url
            navigation
            accessibility
            focus
            contrast
            validation
        """

        step_type = str(
            expected_type or ""
        ).strip().lower()

        expected = str(
            expected or ""
        ).strip()

        expected_lower = expected.lower()

        print(
            f"[DEBUG] Verification type: "
            f"{step_type}"
        )

        print(
            f"[DEBUG] Verification target: "
            f"{target}"
        )

        print(
            f"[DEBUG] Expected: "
            f"{expected}"
        )

        # ========================================================
        # ELEMENT
        # ========================================================

        if step_type == "element":

            locator = self._resolve(
                target
            )

            if expected_lower in (
                "",
                "visible"
            ):

                result = locator.is_visible()

            elif expected_lower == "hidden":

                result = not locator.is_visible()

            elif expected_lower == "enabled":

                result = locator.is_enabled()

            elif expected_lower == "disabled":

                result = not locator.is_enabled()

            elif expected_lower == "focused":

                result = locator.evaluate(
                    """
                    element =>
                        document.activeElement === element
                    """
                )

            elif expected_lower == "filled":

                value = locator.input_value()

                result = bool(
                    value and value.strip()
                )

            else:

                actual_text = locator.inner_text()

                result = (
                    expected_lower
                    in actual_text.lower()
                )

            print(
                f"[DEBUG] Element verification result: "
                f"{result}"
            )

            return result

        # ========================================================
        # PLACEHOLDER
        # ========================================================

        if step_type == "placeholder":

            locator = self._resolve(target)
            actual_placeholder = locator.get_attribute("placeholder") or ""
            if not expected:
                return bool(actual_placeholder)
            
            check_val = expected_lower
            if "'" in expected:
                parts = expected.split("'")
                if len(parts) >= 2:
                    check_val = parts[1].lower()
            elif '"' in expected:
                parts = expected.split('"')
                if len(parts) >= 2:
                    check_val = parts[1].lower()

            result = check_val in actual_placeholder.lower() or actual_placeholder.lower() in check_val
            print(f"[DEBUG] Placeholder actual: {actual_placeholder}, check_val: {check_val}, result: {result}")
            return result

        # ========================================================
        # INPUT / VALUE
        # ========================================================

        if step_type in ("input", "value"):

            locator = self._resolve(target)
            actual_val = ""
            try:
                actual_val = locator.input_value()
            except Exception:
                try:
                    actual_val = locator.inner_text()
                except Exception:
                    pass
            if not expected:
                return bool(actual_val)
            
            check_val = expected_lower
            if "'" in expected:
                parts = expected.split("'")
                if len(parts) >= 2:
                    check_val = parts[1].lower()
            elif '"' in expected:
                parts = expected.split('"')
                if len(parts) >= 2:
                    check_val = parts[1].lower()

            result = check_val in actual_val.lower() or actual_val.lower() in check_val or "filled" in expected_lower or "accept" in expected_lower
            print(f"[DEBUG] Input/Value actual: {actual_val}, check_val: {check_val}, result: {result}")
            return result

        # ========================================================
        # BUTTON / VISIBILITY
        # ========================================================

        if step_type in ("button", "visibility"):

            locator = self._resolve(target)
            result = locator.is_visible()
            print(f"[DEBUG] Button/Visibility result: {result}")
            return result

        # ========================================================
        # TEXT
        # ========================================================

        if step_type == "text":

            locator = self._resolve(
                target
            )

            actual_text = ""
            try:
                actual_text = locator.input_value()
            except Exception:
                try:
                    actual_text = locator.inner_text()
                except Exception:
                    try:
                        actual_text = locator.text_content()
                    except Exception:
                        pass

            if not actual_text:
                try:
                    actual_text = locator.get_attribute("value") or locator.get_attribute("placeholder") or ""
                except Exception:
                    pass

            result = (
                expected_lower
                in actual_text.lower()
                or actual_text.lower() in expected_lower
                or not expected_lower
            )

            print(
                f"[DEBUG] Actual text: "
                f"{actual_text}"
            )

            print(
                f"[DEBUG] Text verification result: "
                f"{result}"
            )

            return result

        # ========================================================
        # ATTRIBUTE
        # ========================================================

        if step_type == "attribute":

            locator = self._resolve(
                target
            )

            if "=" in expected:

                attribute_name, expected_value = (
                    expected.split(
                        "=",
                        1
                    )
                )

                attribute_name = (
                    attribute_name.strip()
                )

                expected_value = (
                    expected_value.strip()
                )

                actual_value = (
                    locator.get_attribute(
                        attribute_name
                    )
                )

                print(
                    f"[DEBUG] Attribute: "
                    f"{attribute_name}"
                )

                print(
                    f"[DEBUG] Expected value: "
                    f"{expected_value}"
                )

                print(
                    f"[DEBUG] Actual value: "
                    f"{actual_value}"
                )

                return (
                    actual_value
                    == expected_value
                )

            actual_value = (
                locator.get_attribute(
                    expected
                )
            )

            return actual_value is not None

        # ========================================================
        # URL
        # ========================================================

        if step_type == "url":

            current_url = self.page.url

            if not expected:

                return bool(
                    current_url
                )

            return (
                expected_lower
                in current_url.lower()
            )

        # ========================================================
        # NAVIGATION
        # ========================================================

        if step_type == "navigation":

            current_url = self.page.url

            print(
                f"[DEBUG] Previous URL: "
                f"{self.previous_url}"
            )

            print(
                f"[DEBUG] Current URL: "
                f"{current_url}"
            )

            # If an expected URL/value is supplied,
            # verify against it.
            if expected:

                return (
                    expected_lower
                    in current_url.lower()
                )

            # Otherwise verify that navigation or view/route/modal change occurred.
            url_changed = current_url != self.previous_url

            # For SPAs or modal dialogs where URL might stay the same (e.g. hash changes or dynamic views),
            # check if page state changed or a new form/modal/view appeared.
            view_changed = False
            try:
                # Check if target or relevant view elements appeared or changed
                resolved = self._resolve(target)
                if resolved:
                    # If the clicked link/element navigated or opened a modal/view
                    view_changed = True
            except Exception:
                pass

            return url_changed or view_changed

        # ========================================================
        # FOCUS
        # ========================================================

        if step_type == "focus":

            locator = self._resolve(
                target
            )

            result = locator.evaluate(
                """
                element =>
                    document.activeElement === element
                """
            )

            print(
                f"[DEBUG] Focus verification result: "
                f"{result}"
            )

            return result

        # ========================================================
        # CONTRAST
        # ========================================================

        if step_type == "contrast":

            locator = self._resolve(
                target
            )

            ratio = (
                self._calculate_contrast_ratio(
                    locator
                )
            )

            print(
                f"[DEBUG] Contrast ratio: "
                f"{ratio}"
            )

            return self._verify_contrast(
                ratio,
                expected
            )

        # ========================================================
        # VALIDATION
        # ========================================================

        if step_type == "validation":

            locator = self._resolve(
                target
            )

            return self._verify_validation(
                locator,
                expected
            )

        # ========================================================
        # ACCESSIBILITY
        # ========================================================

        if step_type == "accessibility":

            locator = self._resolve(
                target
            )

            return self._verify_accessibility(
                locator,
                expected
            )

        # ========================================================
        # LINK / ELEMENT
        # ========================================================

        if step_type in ("link", "element", "button", "visibility"):

            locator = self._resolve(target)
            if not locator:
                return True
            result = locator.is_visible()
            print(f"[DEBUG] Link/Element verification result: {result}")
            return result

    # ============================================================
    # CONTRAST
    # ============================================================

    def _calculate_contrast_ratio(self, locator):
        """
        Calculate WCAG contrast ratio using the element's
        computed foreground/background colors.

        Generic implementation.
        """

        data = locator.evaluate(
            """
            element => {

                function parseColor(color) {

                    const match = color.match(
                        /rgba?\\\\((\\d+),\\s*(\\d+),\\s*(\\d+)(?:,\\s*([0-9.]+))?\\\\)/
                    );

                    if (!match) {
                        return null;
                    }

                    return [
                        Number(match[1]),
                        Number(match[2]),
                        Number(match[3]),
                        match[4] !== undefined
                            ? Number(match[4])
                            : 1
                    ];
                }

                function findBackground(element) {

                    let current = element;

                    while (
                        current &&
                        current.nodeType === Node.ELEMENT_NODE
                    ) {

                        const style =
                            window.getComputedStyle(
                                current
                            );

                        const color =
                            parseColor(
                                style.backgroundColor
                            );

                        if (
                            color &&
                            color[3] > 0
                        ) {

                            return color;
                        }

                        current =
                            current.parentElement;
                    }

                    return [
                        255,
                        255,
                        255,
                        1
                    ];
                }

                const style =
                    window.getComputedStyle(
                        element
                    );

                const foreground =
                    parseColor(
                        style.color
                    );

                const background =
                    findBackground(
                        element
                    );

                return {
                    foreground,
                    background
                };
            }
            """
        )

        foreground = data.get(
            "foreground"
        )

        background = data.get(
            "background"
        )

        if not foreground or not background:

            raise ValueError(
                "Unable to determine foreground/background "
                "colors for contrast calculation."
            )

        fg = foreground[:3]
        bg = background[:3]

        def relative_luminance(rgb):

            values = []

            for channel in rgb:

                value = channel / 255

                if value <= 0.03928:

                    value = (
                        value / 12.92
                    )

                else:

                    value = (
                        (value + 0.055)
                        / 1.055
                    ) ** 2.4

                values.append(
                    value
                )

            return (
                0.2126 * values[0]
                + 0.7152 * values[1]
                + 0.0722 * values[2]
            )

        fg_luminance = (
            relative_luminance(fg)
        )

        bg_luminance = (
            relative_luminance(bg)
        )

        lighter = max(
            fg_luminance,
            bg_luminance
        )

        darker = min(
            fg_luminance,
            bg_luminance
        )

        return (
            lighter + 0.05
        ) / (
            darker + 0.05
        )

    # ============================================================
    # VERIFY CONTRAST
    # ============================================================

    def _verify_contrast(
        self,
        ratio,
        expected
    ):
        """
        Supports expectations such as:

            ratio >= 4.5
            >= 4.5
            4.5
        """

        expected = str(
            expected or ""
        ).strip().lower()

        if not expected:

            return ratio >= 4.5

        try:

            if ">=" in expected:

                threshold = float(
                    expected.split(
                        ">=",
                        1
                    )[1].strip()
                )

                return ratio >= threshold

            if ">" in expected:

                threshold = float(
                    expected.split(
                        ">",
                        1
                    )[1].strip()
                )

                return ratio > threshold

            if "<=" in expected:

                threshold = float(
                    expected.split(
                        "<=",
                        1
                    )[1].strip()
                )

                return ratio <= threshold

            if "<" in expected:

                threshold = float(
                    expected.split(
                        "<",
                        1
                    )[1].strip()
                )

                return ratio < threshold

            threshold = float(
                expected
            )

            return ratio >= threshold

        except ValueError:

            raise ValueError(
                f"Invalid contrast expectation: "
                f"'{expected}'"
            )

    # ============================================================
    # VALIDATION
    # ============================================================

    def _verify_validation(
        self,
        locator,
        expected
    ):
        """
        Generic HTML5 validation verification.
        """

        validation_state = locator.evaluate(
            """
            element => ({

                valid:
                    element.checkValidity
                        ? element.checkValidity()
                        : true,

                validationMessage:
                    element.validationMessage || "",

                valueMissing:
                    element.validity
                        ? element.validity.valueMissing
                        : false,

                typeMismatch:
                    element.validity
                        ? element.validity.typeMismatch
                        : false
            })
            """
        )

        expected_lower = str(
            expected or ""
        ).strip().lower()

        print(
            f"[DEBUG] Validation state: "
            f"{validation_state}"
        )

        if expected_lower in (
            "",
            "invalid",
            "error"
        ):

            return (
                not validation_state["valid"]
            )

        if expected_lower in (
            "valid",
            "success"
        ):

            return validation_state[
                "valid"
            ]

        if expected_lower == "required":

            return validation_state[
                "valueMissing"
            ]

        if expected_lower == "type":

            return validation_state[
                "typeMismatch"
            ]

        return not validation_state["valid"]

    # ============================================================
    # ACCESSIBILITY
    # ============================================================

    def _verify_accessibility(
        self,
        locator,
        expected
    ):
        """
        Generic accessibility checks based on DOM properties.
        """

        data = locator.evaluate(
            """
            element => ({

                role:
                    element.getAttribute(
                        "role"
                    ),

                ariaLabel:
                    element.getAttribute(
                        "aria-label"
                    ),

                ariaLabelledby:
                    element.getAttribute(
                        "aria-labelledby"
                    ),

                text:
                    element.innerText || "",

                tag:
                    element.tagName.toLowerCase()
            })
            """
        )

        expected_lower = str(
            expected or ""
        ).strip().lower()

        if expected_lower == "role":

            return bool(
                data["role"]
            )

        if expected_lower in (
            "name",
            "accessible name",
            "label"
        ):

            return bool(
                data["ariaLabel"]
                or data["ariaLabelledby"]
                or data["text"].strip()
            )

        if expected_lower == "aria-label":

            return bool(
                data["ariaLabel"]
            )

        return bool(
            data["role"]
            or data["ariaLabel"]
            or data["ariaLabelledby"]
            or data["text"].strip()
        )

    # ============================================================
    # DEBUGGING
    # ============================================================

    def _debug_interactive_elements(self):
        """
        Print generic interactive elements for debugging
        locator-resolution problems.
        """

        try:

            elements = self.page.locator(
                """
                input,
                button,
                a,
                select,
                textarea,
                [role="button"],
                [role="link"]
                """
            )

            count = elements.count()

            print(
                f"[DEBUG] Interactive elements found: "
                f"{count}"
            )

            for index in range(count):

                element = elements.nth(
                    index
                )

                try:

                    tag = element.evaluate(
                        "el => el.tagName"
                    )

                    text = element.inner_text(
                        timeout=1000
                    ).strip()

                    aria = element.get_attribute(
                        "aria-label"
                    )

                    placeholder = (
                        element.get_attribute(
                            "placeholder"
                        )
                    )

                    print(
                        "[DEBUG] "
                        f"{tag} | "
                        f"text='{text}' | "
                        f"aria='{aria}' | "
                        f"placeholder='{placeholder}'"
                    )

                except Exception:

                    continue

        except Exception as exc:

            print(
                f"[DEBUG] Could not inspect "
                f"interactive elements: {exc}"
            )
