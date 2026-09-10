import re


class LocatorResolver:
    """
    Generic semantic UI locator resolver.

    Resolves AI-generated natural-language targets without
    relying on website-specific selectors.
    """

    def __init__(self, page):
        self.page = page

    # ============================================================
    # PUBLIC RESOLVE METHOD
    # ============================================================

    def resolve(self, target):
        """
        Resolve a natural-language UI description to a Playwright
        locator.
        """

        if not target:
            return None

        target = str(target).strip()

        if not target:
            return None

        print(f"[DEBUG] Resolving target: '{target}'")

        target_lower = target.lower()

        # --------------------------------------------------------
        # 1. Semantic specializations
        # --------------------------------------------------------

        if "email" in target_lower:
            locator = self._resolve_email(target)

            if locator:
                return locator

        if "password" in target_lower:
            locator = self._resolve_password(target)

            if locator:
                return locator

        if "login" in target_lower:
            locator = self._resolve_by_role_text(
                "button",
                ["login", "log in", "sign in"]
            )

            if locator:
                return locator

            # Some applications implement buttons as
            # input[type=submit] or other semantic controls.
            locator = self._resolve_button(target)

            if locator:
                return locator

        if "register" in target_lower:
            locator = self._resolve_by_text(
                ["register", "register here", "sign up"]
            )

            if locator:
                return locator

        if "forgot" in target_lower:
            locator = self._resolve_by_text(
                ["forgot password", "forgot password?"]
            )

            if locator:
                return locator

        # --------------------------------------------------------
        # 1.b Generic structural/banner/card resolution
        # --------------------------------------------------------

        if any(
            kw in target_lower
            for kw in (
                "banner",
                "header",
                "card",
                "container",
                "wrapper",
                "box",
                "section"
            )
        ):
            # Try finding semantic structural elements matching keywords
            words = self._keywords(target, remove_generic=True)
            if words:
                # Search common structural elements
                structural_candidates = self.page.locator(
                    "header, section, article, div, form, nav, aside"
                )
                best_loc = None
                best_score = 0
                count = structural_candidates.count()
                for i in range(min(count, 50)):
                    loc = structural_candidates.nth(i)
                    try:
                        if not loc.is_visible():
                            continue
                        text = loc.inner_text().lower()
                        score = sum(1 for w in words if w in text)
                        if score > best_score:
                            best_score = score
                            best_loc = loc
                    except Exception:
                        continue
                if best_loc and best_score > 0:
                    return best_loc

        # --------------------------------------------------------
        # 2. Generic input resolution
        # --------------------------------------------------------

        if any(
            keyword in target_lower
            for keyword in (
                "input",
                "field",
                "textbox",
                "text box",
                "textarea"
            )
        ):
            locator = self._resolve_input(target)

            if locator:
                return locator

        # --------------------------------------------------------
        # 3. Generic button resolution
        # --------------------------------------------------------

        if "button" in target_lower:
            locator = self._resolve_button(target)

            if locator:
                return locator

        # --------------------------------------------------------
        # 4. Generic link resolution
        # --------------------------------------------------------

        if "link" in target_lower:
            locator = self._resolve_link(target)

            if locator:
                return locator

        # --------------------------------------------------------
        # 5. Generic visible text resolution
        # --------------------------------------------------------

        locator = self._resolve_text_description(target)

        if locator:
            return locator

        # --------------------------------------------------------
        # 6. Generic semantic scan
        # --------------------------------------------------------

        locator = self._semantic_scan(target)

        if locator:
            return locator

        print(
            f"[DEBUG] Could not resolve target: '{target}'"
        )

        self._debug_page_elements()

        return None

    # ============================================================
    # EMAIL
    # ============================================================

    def _resolve_email(self, target):
        locators = [
            self.page.get_by_label(
                re.compile(r"email", re.I)
            ),

            self.page.locator(
                'input[type="email"]'
            ),

            self.page.locator(
                'input[autocomplete="email"]'
            ),

            self.page.locator(
                'input[name*="email" i]'
            )
        ]

        return self._first_visible(locators)

    # ============================================================
    # PASSWORD
    # ============================================================

    def _resolve_password(self, target):
        locators = [
            self.page.get_by_label(
                re.compile(r"password", re.I)
            ),

            self.page.locator(
                'input[type="password"]'
            ),

            self.page.locator(
                'input[autocomplete="current-password"]'
            ),

            self.page.locator(
                'input[name*="password" i]'
            )
        ]

        return self._first_visible(locators)

    # ============================================================
    # ROLE + TEXT
    # ============================================================

    def _resolve_by_role_text(self, role, texts):
        for text in texts:
            try:
                locator = self.page.get_by_role(
                    role,
                    name=re.compile(
                        re.escape(text),
                        re.I
                    )
                )

                if locator.count() > 0:
                    visible = self._first_visible([locator])

                    if visible:
                        return visible

            except Exception:
                continue

        return None

    # ============================================================
    # TEXT
    # ============================================================

    def _resolve_by_text(self, texts):
        for text in texts:

            # ----------------------------------------------------
            # Accessible/text based resolution
            # ----------------------------------------------------

            try:
                locator = self.page.get_by_text(
                    re.compile(
                        re.escape(text),
                        re.I
                    ),
                    exact=False
                )

                if locator.count() > 0:
                    visible = self._first_visible(
                        [locator]
                    )

                    if visible:
                        return visible

            except Exception:
                pass

            # ----------------------------------------------------
            # Generic link text
            # ----------------------------------------------------

            try:
                locator = self.page.locator(
                    "a"
                ).filter(
                    has_text=re.compile(
                        re.escape(text),
                        re.I
                    )
                )

                if locator.count() > 0:
                    visible = self._first_visible(
                        [locator]
                    )

                    if visible:
                        return visible

            except Exception:
                pass

        return None

    # ============================================================
    # INPUT
    # ============================================================

    def _resolve_input(self, target):
        words = self._keywords(target)

        candidates = self.page.locator(
            "input:not([type='hidden']):not([type='submit']):not([type='button']), textarea"
        )

        count = candidates.count()

        scored = []

        for index in range(count):

            locator = candidates.nth(index)

            try:
                if not locator.is_visible():
                    continue

                score = 0

                attributes = {
                    "placeholder":
                        locator.get_attribute(
                            "placeholder"
                        ),

                    "name":
                        locator.get_attribute(
                            "name"
                        ),

                    "id":
                        locator.get_attribute(
                            "id"
                        ),

                    "type":
                        locator.get_attribute(
                            "type"
                        ),

                    "aria-label":
                        locator.get_attribute(
                            "aria-label"
                        )
                }

                for value in attributes.values():

                    if not value:
                        continue

                    value_lower = value.lower()

                    for word in words:
                        if word in value_lower:
                            score += 2

                if score > 0:
                    scored.append(
                        (score, index)
                    )

            except Exception:
                continue

        if scored:
            scored.sort(
                key=lambda item: item[0],
                reverse=True
            )

            return candidates.nth(
                scored[0][1]
            )

        # Generic sequential fallback for standard login/form inputs:
        # If looking for email/username and multiple inputs exist, return the first visible input.
        # If looking for password, return the second visible input or password type input.
        target_lower = str(target).lower()
        visible_candidates = []
        for index in range(count):
            loc = candidates.nth(index)
            try:
                if loc.is_visible():
                    visible_candidates.append(loc)
            except Exception:
                continue

        if visible_candidates:
            if "email" in target_lower or "user" in target_lower or "username" in target_lower:
                return visible_candidates[0]
            if "password" in target_lower:
                for loc in visible_candidates:
                    try:
                        if loc.get_attribute("type") == "password":
                            return loc
                    except Exception:
                        pass
                if len(visible_candidates) > 1:
                    return visible_candidates[1]
            if count == 1:
                return candidates.first

        return None

    # ============================================================
    # BUTTON
    # ============================================================

    def _resolve_button(self, target):
        words = self._keywords(
            target,
            remove_generic=True
        )

        candidates = self.page.locator(
            """
            button,
            input[type="button"],
            input[type="submit"],
            [role="button"],
            a
            """
        )

        return self._resolve_textual_candidate(
            candidates,
            words
        )

    # ============================================================
    # LINK
    # ============================================================

    def _resolve_link(self, target):
        words = self._keywords(
            target,
            remove_generic=True
        )

        candidates = self.page.locator(
            """
            a,
            [role="link"]
            """
        )

        return self._resolve_textual_candidate(
            candidates,
            words
        )

    # ============================================================
    # GENERIC TEXT DESCRIPTION
    # ============================================================

    def _resolve_text_description(self, target):
        """
        Resolve non-interactive descriptive text.

        Example:

            "Card top instruction text"

        The resolver searches visible DOM text and scores
        candidates using meaningful words from the AI description.

        No website-specific selector, ID, class or URL is used.
        """

        words = self._keywords(
            target,
            remove_generic=True
        )

        if not words:
            return None

        # Prefer semantic text-bearing elements.
        candidates = self.page.locator(
            """
            p,
            span,
            div,
            label,
            h1,
            h2,
            h3,
            h4,
            h5,
            h6,
            li,
            td,
            th
            """
        )

        count = candidates.count()

        best_locator = None
        best_score = 0
        best_text_length = None

        for index in range(count):

            locator = candidates.nth(index)

            try:
                if not locator.is_visible():
                    continue

                text = locator.inner_text(
                    timeout=300
                ).strip()

                if not text:
                    continue

                # Ignore extremely large containers.
                if len(text) > 500:
                    continue

                text_lower = text.lower()

                score = 0
                matched_words = 0

                for word in words:
                    if word in text_lower:
                        score += 3
                        matched_words += 1

                if matched_words == 0:
                    continue

                # Reward candidates matching more words.
                if matched_words == len(words):
                    score += 5

                # Prefer shorter text because it is more likely
                # to represent the actual target rather than a
                # large parent container.
                text_length = len(text)

                if text_length <= 120:
                    score += 2

                if text_length <= 60:
                    score += 2

                # Prefer leaf-like elements.
                try:
                    child_count = locator.locator(
                        ":scope > *"
                    ).count()

                    if child_count == 0:
                        score += 4
                except Exception:
                    pass

                # Prefer the candidate with the highest score.
                # If scores tie, prefer shorter text.
                should_replace = False

                if score > best_score:
                    should_replace = True

                elif (
                    score == best_score
                    and (
                        best_text_length is None
                        or text_length < best_text_length
                    )
                ):
                    should_replace = True

                if should_replace:
                    best_score = score
                    best_locator = locator
                    best_text_length = text_length

            except Exception:
                continue

        if best_locator:
            print(
                "[DEBUG] Generic text resolver "
                f"matched '{target}' "
                f"with score {best_score}"
            )

        return best_locator

    # ============================================================
    # SEMANTIC SCAN
    # ============================================================

    def _semantic_scan(self, target):
        """
        Generic fallback using visible text, aria-label,
        placeholder, title and name.
        """

        words = self._keywords(
            target,
            remove_generic=True
        )

        if not words:
            return None

        candidates = self.page.locator(
            """
            input,
            textarea,
            select,
            button,
            a,
            [role],
            [aria-label],
            [title]
            """
        )

        count = candidates.count()

        best = None
        best_score = 0

        for index in range(count):

            locator = candidates.nth(index)

            try:
                if not locator.is_visible():
                    continue

                values = []

                text = locator.inner_text(
                    timeout=300
                ).strip()

                if text:
                    values.append(text)

                for attribute in (
                    "aria-label",
                    "placeholder",
                    "title",
                    "name"
                ):
                    value = locator.get_attribute(
                        attribute
                    )

                    if value:
                        values.append(value)

                combined = " ".join(
                    values
                ).lower()

                score = 0

                for word in words:
                    if word in combined:
                        score += 2

                if score > best_score:
                    best_score = score
                    best = locator

            except Exception:
                continue

        if best:
            print(
                f"[DEBUG] Semantic scan matched "
                f"'{target}' with score {best_score}"
            )

        return best

    # ============================================================
    # TEXTUAL CANDIDATE SCORING
    # ============================================================

    def _resolve_textual_candidate(
        self,
        candidates,
        words
    ):
        count = candidates.count()

        best = None
        best_score = 0

        for index in range(count):

            locator = candidates.nth(index)

            try:
                if not locator.is_visible():
                    continue

                values = []

                text = locator.inner_text(
                    timeout=300
                ).strip()

                if text:
                    values.append(text)

                for attribute in (
                    "aria-label",
                    "title",
                    "name"
                ):
                    value = locator.get_attribute(
                        attribute
                    )

                    if value:
                        values.append(value)

                combined = " ".join(
                    values
                ).lower()

                score = 0

                for word in words:
                    if word in combined:
                        score += 2

                # Reward exact/complete phrase matches.
                target_text = " ".join(words)

                if target_text and target_text in combined:
                    score += 5

                if score > best_score:
                    best_score = score
                    best = locator

            except Exception:
                continue

        if best:
            return best

        return None

    # ============================================================
    # KEYWORD EXTRACTION
    # ============================================================

    def _keywords(
        self,
        text,
        remove_generic=False
    ):
        words = re.findall(
            r"[a-zA-Z0-9]+",
            str(text).lower()
        )

        stop_words = {
            "the",
            "a",
            "an",
            "of",
            "to",
            "in",
            "on",
            "for",
            "with",
            "and",
            "or",
            "is",
            "are",
            "be",
            "this",
            "that"
        }

        generic_words = {
            "element",
            "field",
            "input",
            "button",
            "link",
            "text",
            "control",
            "ui",
            "user",
            "interface",
            "section",
            "area",
            "container"
        }

        result = []

        for word in words:

            if word in stop_words:
                continue

            if remove_generic and word in generic_words:
                continue

            if len(word) < 2:
                continue

            result.append(word)

        return result

    # ============================================================
    # FIRST VISIBLE
    # ============================================================

    def _first_visible(self, locators):

        for locator in locators:

            try:
                count = locator.count()

                for index in range(count):

                    candidate = locator.nth(index)

                    if candidate.is_visible():
                        return candidate

            except Exception:
                continue

        return None

    # ============================================================
    # DEBUG
    # ============================================================

    def _debug_page_elements(self):

        try:
            elements = self.page.locator(
                """
                input,
                textarea,
                button,
                a,
                [role],
                [aria-label],
                [title]
                """
            )

            count = elements.count()

            print(
                f"[DEBUG] Page semantic elements: "
                f"{count}"
            )

            for index in range(count):

                element = elements.nth(index)

                try:

                    tag = element.evaluate(
                        "el => el.tagName"
                    )

                    text = element.inner_text(
                        timeout=300
                    ).strip()

                    aria = element.get_attribute(
                        "aria-label"
                    )

                    placeholder = element.get_attribute(
                        "placeholder"
                    )

                    role = element.get_attribute(
                        "role"
                    )

                    print(
                        "[DEBUG] "
                        f"{tag} | "
                        f"text='{text}' | "
                        f"aria='{aria}' | "
                        f"placeholder='{placeholder}' | "
                        f"role='{role}'"
                    )

                except Exception:
                    continue

        except Exception as exc:

            print(
                f"[DEBUG] Could not debug page: "
                f"{exc}"
            )
