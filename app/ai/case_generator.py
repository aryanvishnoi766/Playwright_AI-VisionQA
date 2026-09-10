import json
import os

from dotenv import load_dotenv
from google import genai


# ---------------------------------------------------------
# Environment
# ---------------------------------------------------------

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set in .env")


# ---------------------------------------------------------
# Gemini client
# ---------------------------------------------------------

client = genai.Client(api_key=GEMINI_API_KEY)

MODEL_NAME = os.getenv("GEMINI_MODEL")




# ---------------------------------------------------------
# Allowed values
# ---------------------------------------------------------

ALLOWED_ACTIONS = {
    "navigate",
    "click",
    "fill",
    "clear",
    "press",
    "focus",
    "verify",
    "wait",
}

ALLOWED_CATEGORIES = {
    "Functional",
    "Accessibility",
    "Visual",
    "Edge Case",
}

ALLOWED_PRIORITIES = {
    "High",
    "Medium",
    "Low",
}

ALLOWED_VERIFY_TYPES = {
    "text",
    "attribute",
    "placeholder",
    "focus",
    "contrast",
    "navigation",
    "visibility",
    "validation",
    "value",
    "element",
}


REQUIRED_TEST_CASE_FIELDS = {
    "id",
    "title",
    "description",
    "priority",
    "category",
    "preconditions",
    "steps",
    "expected_result",
    "evidence",
}

REQUIRED_STEP_FIELDS = {
    "step",
    "action",
    "type",
    "target",
    "value",
    "key",
    "expected",
}

REQUIRED_EXPECTED_FIELDS = {
    "type",
    "value",
}


# ---------------------------------------------------------
# AI output normalization
# ---------------------------------------------------------

def normalize_category(category):
    """
    Normalize harmless AI-generated category variations
    into the framework's canonical category values.

    This does NOT weaken the schema.

    Examples:
        Edge Cases -> Edge Case
        Edge-Case -> Edge Case
        EdgeCases -> Edge Case
        Functional Testing -> Functional
        Accessibility Testing -> Accessibility
        Visual Testing -> Visual
    """

    if not isinstance(category, str):
        return category

    normalized = category.strip()

    aliases = {
        "edge cases": "Edge Case",
        "edge-case": "Edge Case",
        "edge cases testing": "Edge Case",
        "edge case testing": "Edge Case",
        "edgecases": "Edge Case",

        "functional testing": "Functional",
        "functional test": "Functional",

        "accessibility testing": "Accessibility",
        "accessibility test": "Accessibility",

        "visual testing": "Visual",
        "visual test": "Visual",
    }

    return aliases.get(
        normalized.lower(),
        normalized,
    )


# ---------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------

def _require_dict(value, location):
    if not isinstance(value, dict):
        raise ValueError(
            f"{location} must be an object."
        )


def _require_string(value, location, allow_empty=False):
    if not isinstance(value, str):
        raise ValueError(
            f"{location} must be a string."
        )

    if not allow_empty and not value.strip():
        raise ValueError(
            f"{location} must not be empty."
        )


def _require_list(value, location):
    if not isinstance(value, list):
        raise ValueError(
            f"{location} must be a list."
        )


def _validate_expected(expected, location):
    _require_dict(expected, location)

    missing = (
        REQUIRED_EXPECTED_FIELDS
        - set(expected.keys())
    )

    if missing:
        raise ValueError(
            f"{location} is missing required fields: "
            f"{sorted(missing)}"
        )

    _require_string(
        expected["type"],
        f"{location}.type",
        allow_empty=True,
    )

    _require_string(
        expected["value"],
        f"{location}.value",
        allow_empty=True,
    )


# ---------------------------------------------------------
# Step validation
# ---------------------------------------------------------

def _validate_step(
    step,
    test_case_id,
    expected_step_number,
):
    location = f"test case {test_case_id}, step"

    _require_dict(step, location)

    missing = (
        REQUIRED_STEP_FIELDS
        - set(step.keys())
    )

    if missing:
        raise ValueError(
            f"{location} is missing required fields: "
            f"{sorted(missing)}"
        )

    # -----------------------------------------------------
    # Step number
    # -----------------------------------------------------

    if not isinstance(step["step"], int):
        raise ValueError(
            f"{location}.step must be an integer."
        )

    if step["step"] != expected_step_number:
        raise ValueError(
            f"{location}.step must be "
            f"{expected_step_number}, "
            f"got {step['step']}."
        )

    # -----------------------------------------------------
    # Basic fields
    # -----------------------------------------------------

    _require_string(
        step["action"],
        f"{location}.action",
    )

    action = (
        step["action"]
        .strip()
        .lower()
    )

    if action not in ALLOWED_ACTIONS:
        raise ValueError(
            f"{location}.action '{action}' "
            f"is not allowed. "
            f"Allowed actions: "
            f"{sorted(ALLOWED_ACTIONS)}"
        )

    _require_string(
        step["type"],
        f"{location}.type",
        allow_empty=True,
    )

    _require_string(
        step["target"],
        f"{location}.target",
        allow_empty=True,
    )

    _require_string(
        step["value"],
        f"{location}.value",
        allow_empty=True,
    )

    _require_string(
        step["key"],
        f"{location}.key",
        allow_empty=True,
    )

    _validate_expected(
        step["expected"],
        f"{location}.expected",
    )

    # -----------------------------------------------------
    # Action-specific validation
    # -----------------------------------------------------

    if action in {
        "click",
        "fill",
        "clear",
        "press",
        "focus",
        "verify",
    }:
        if not step["target"].strip():
            raise ValueError(
                f"{location}.target cannot be empty "
                f"for action '{action}'."
            )

    # -----------------------------------------------------
    # Fill
    # -----------------------------------------------------

    if action == "fill":
        if not step.get("value") or not str(step["value"]).strip():
            step["value"] = "test_value"

    # -----------------------------------------------------
    # Press
    # -----------------------------------------------------

    if action == "press":
        if not step["key"].strip():
            raise ValueError(
                f"{location}.key cannot be empty "
                f"for a press action."
            )

    # -----------------------------------------------------
    # Verify
    # -----------------------------------------------------

    if action == "verify":

        verify_type = (
            step["type"]
            .strip()
            .lower()
        )

        if verify_type not in ALLOWED_VERIFY_TYPES:
            raise ValueError(
                f"{location}.type '{verify_type}' "
                f"is not allowed for verify action. "
                f"Allowed types: "
                f"{sorted(ALLOWED_VERIFY_TYPES)}"
            )

        expected_type = (
            step["expected"]["type"]
            .strip()
            .lower()
        )

        if expected_type != verify_type:
            raise ValueError(
                f"{location}.expected.type must match "
                f"step.type for verify actions. "
                f"Got type='{verify_type}', "
                f"expected.type='{expected_type}'."
            )

    # -----------------------------------------------------
    # Focus
    # -----------------------------------------------------

    if action == "focus":

        expected_type = (
            step["expected"]["type"]
            .strip()
            .lower()
        )

        if expected_type != "focus":
            raise ValueError(
                f"{location}.expected.type must be "
                f"'focus' for focus actions."
            )

    # -----------------------------------------------------
    # Clear
    # -----------------------------------------------------

    if action == "clear":

        expected_type = (
            step["expected"]["type"]
            .strip()
            .lower()
        )

        if expected_type not in {
            "",
            "element",
            "value",
        }:
            raise ValueError(
                f"{location}.expected.type is invalid "
                f"for clear action."
            )

    # -----------------------------------------------------
    # Wait
    # -----------------------------------------------------

    if action == "wait":

        if not step["value"].strip():
            raise ValueError(
                f"{location}.value must contain a wait "
                f"duration for wait actions."
            )


# ---------------------------------------------------------
# Test case validation
# ---------------------------------------------------------

def _validate_test_case(test_case, index):

    location = f"test_cases[{index}]"

    _require_dict(
        test_case,
        location,
    )

    missing = (
        REQUIRED_TEST_CASE_FIELDS
        - set(test_case.keys())
    )

    if missing:
        raise ValueError(
            f"{location} is missing required fields: "
            f"{sorted(missing)}"
        )

    # -----------------------------------------------------
    # Test case identity
    # -----------------------------------------------------

    _require_string(
        test_case["id"],
        f"{location}.id",
    )

    _require_string(
        test_case["title"],
        f"{location}.title",
    )

    _require_string(
        test_case["description"],
        f"{location}.description",
    )

    _require_string(
        test_case["expected_result"],
        f"{location}.expected_result",
    )

    _require_string(
        test_case["evidence"],
        f"{location}.evidence",
    )

    # -----------------------------------------------------
    # Priority
    # -----------------------------------------------------

    if test_case["priority"] not in ALLOWED_PRIORITIES:
        raise ValueError(
            f"{location}.priority "
            f"'{test_case['priority']}' is invalid. "
            f"Allowed values: "
            f"{sorted(ALLOWED_PRIORITIES)}"
        )

    # -----------------------------------------------------
    # Category normalization
    # -----------------------------------------------------

    original_category = test_case["category"]

    normalized_category = normalize_category(
        original_category
    )

    test_case["category"] = normalized_category

    if normalized_category not in ALLOWED_CATEGORIES:
        raise ValueError(
            f"{location}.category "
            f"'{original_category}' is invalid. "
            f"Allowed values: "
            f"{sorted(ALLOWED_CATEGORIES)}"
        )

    # -----------------------------------------------------
    # Preconditions
    # -----------------------------------------------------

    _require_list(
        test_case["preconditions"],
        f"{location}.preconditions",
    )

    for precondition_index, precondition in enumerate(
        test_case["preconditions"]
    ):
        _require_string(
            precondition,
            f"{location}.preconditions"
            f"[{precondition_index}]",
        )

    # -----------------------------------------------------
    # Steps
    # -----------------------------------------------------

    _require_list(
        test_case["steps"],
        f"{location}.steps",
    )

    if not test_case["steps"]:
        raise ValueError(
            f"{location}.steps cannot be empty."
        )

    for step_index, step in enumerate(
        test_case["steps"],
        start=1,
    ):
        _validate_step(
            step,
            test_case["id"],
            step_index,
        )


# ---------------------------------------------------------
# Validate complete Gemini response
# ---------------------------------------------------------

def validate_generated_test_cases(result):
    """
    Strictly validate Gemini-generated test cases.

    AI-generated category aliases are normalized before
    validation so natural language variations do not break
    the canonical framework schema.

    Raises ValueError when the generated structure does not
    conform to the framework schema.

    Returns the validated result.
    """

    # -----------------------------------------------------
    # Top-level object
    # -----------------------------------------------------

    _require_dict(
        result,
        "Generated test case result",
    )

    if set(result.keys()) != {"test_cases"}:
        raise ValueError(
            "Generated JSON must contain exactly one "
            "top-level field: 'test_cases'."
        )

    test_cases = result["test_cases"]

    _require_list(
        test_cases,
        "test_cases",
    )

    if not test_cases:
        raise ValueError(
            "Gemini generated zero test cases."
        )

    # -----------------------------------------------------
    # Validate every test case
    # -----------------------------------------------------

    seen_ids = set()

    for index, test_case in enumerate(test_cases):

        _validate_test_case(
            test_case,
            index,
        )

        test_id = (
            test_case["id"]
            .strip()
        )

        if test_id in seen_ids:
            raise ValueError(
                f"Duplicate test case ID detected: "
                f"{test_id}"
            )

        seen_ids.add(test_id)

    return result


# ---------------------------------------------------------
# Test Case Generator
# ---------------------------------------------------------

def generate_test_cases(analysis):
    """
    Generate comprehensive, evidence-driven UI test cases.

    This function ONLY performs:

        analysis -> Gemini -> validated test cases

    It does NOT:

        - read screenshots
        - save files
        - create directories
        - call the vision analyzer
        - execute tests
        - use website-specific selectors
        - use website-specific URLs
    """

    if not isinstance(analysis, dict):
        raise TypeError(
            "analysis must be a dictionary"
        )

    analysis_json = json.dumps(
        analysis,
        indent=2,
        ensure_ascii=False,
    )

    prompt = """
You are a senior QA automation architect and manual testing expert.

Generate comprehensive, evidence-driven UI test cases from the
structured UI analysis below.

SOURCE OF TRUTH:

__ANALYSIS_JSON__

==========================================================
COVERAGE REQUIREMENTS
==========================================================

Systematically inspect:

1. ui_elements
2. interaction_evidence
3. accessibility_evidence
4. visual_evidence
5. functional_test_scenarios
6. accessibility_test_scenarios
7. edge_cases
8. potential_issues

Every meaningful interactive element must be considered.

Generate separate tests for logically different behaviors where useful.

Examples:

- input accepts data
- input can be cleared
- input receives focus
- visible placeholder/text verification
- button interaction
- link interaction
- navigation
- accessibility verification
- visual defect verification
- supported edge case

Do not arbitrarily limit the number of tests.

Generate as many meaningful tests as the evidence supports.

Do not generate duplicate tests.

==========================================================
STRICT EVIDENCE RULE
==========================================================

The analysis is the ONLY source of truth.

Never invent:

- selectors
- XPath
- CSS
- IDs
- classes
- URLs
- navigation destinations
- backend behavior
- API behavior
- validation rules
- error messages
- keyboard focus order
- responsive behavior
- hidden controls

If behavior is not supported by evidence, do not test it.

==========================================================
DEFECT RULE
==========================================================

If the analysis identifies a defect, test the intended correct state.

For example, if an observed UI text contains an apparent spelling
defect, the test should verify the intended correct spelling.

Do not invent defects that are not present in the analysis.

==========================================================
VERIFY TYPE CONSISTENCY — STRICT RULE
==========================================================

For every step with action "verify":

1. "step.type" describes exactly what is being verified.
2. "expected.type" MUST be exactly identical to "step.type".
3. Never use a different expected.type.

Examples:

CORRECT:

{
  "action": "verify",
  "type": "placeholder",
  "target": "input field",
  "value": "",
  "key": "",
  "expected": {
    "type": "placeholder",
    "value": "The input has the expected placeholder text."
  }
}

CORRECT:

{
  "action": "verify",
  "type": "text",
  "target": "button",
  "value": "",
  "key": "",
  "expected": {
    "type": "text",
    "value": "The button displays the expected text."
  }
}

CORRECT:

{
  "action": "verify",
  "type": "focus",
  "target": "input field",
  "value": "",
  "key": "",
  "expected": {
    "type": "focus",
    "value": "The input receives focus."
  }
}

INCORRECT:

{
  "action": "verify",
  "type": "placeholder",
  "target": "input field",
  "value": "",
  "key": "",
  "expected": {
    "type": "text",
    "value": "The input has the expected placeholder."
  }
}

The incorrect pattern MUST NEVER be generated.

==========================================================
STEP SCHEMA & FILL/EXPECTED RULE
==========================================================

Every step MUST contain exactly:

{
  "step": 1,
  "action": "",
  "type": "",
  "target": "",
  "value": "",
  "key": "",
  "expected": {
    "type": "",
    "value": ""
  }
}

STRICT FILL RULE:
If action is "fill", "value" MUST contain the non-empty text to be filled. Never leave "value" empty for a "fill" action.

STRICT EXPECTED RULE:
If "expected.type" is populated (not empty), "expected.value" MUST contain the precise expected substring, exact text, attribute value, or status (e.g. "visible", "email@example.com", "Log in") rather than a verbose natural language sentence. Never generate full explanatory sentences in expected.value.

==========================================================
SEMANTIC TARGETS
==========================================================

Targets must be human-readable semantic descriptions.

Good:

"Email input field"
"Password input field"
"Login button"
"Forgot password link"

Bad:

"#email"
".login-button"
"input[type=email]"
"//*[@id='email']"

Never generate CSS selectors, XPath, IDs, classes, or implementation
details.

==========================================================
INPUT TESTING
==========================================================

For each input, consider applicable evidence-supported tests:

- fill
- clear
- focus
- placeholder/text/attribute verification
- validation only when explicitly supported

Never assume:

- email validation
- password rules
- required fields
- HTML5 validation
- error messages

without evidence.

==========================================================
BUTTON TESTING
==========================================================

For each visible meaningful button:

Test interaction when supported.

Do not invent post-click behavior.

==========================================================
LINK TESTING
==========================================================

For each visible interactive link:

Test clicking it.

If navigation is supported, verify that navigation occurred.

Never invent a destination URL.

==========================================================
ACCESSIBILITY
==========================================================

Generate accessibility tests only from evidence.

Possible tests:

- focus
- contrast
- accessible naming evidence
- visible labels
- keyboard interaction

Do not invent keyboard focus order.

==========================================================
VISUAL DEFECTS
==========================================================

Potential issues such as:

- spelling
- wording
- clipping
- overlap
- contrast
- alignment

should become verification tests when they are executable.

==========================================================
CONTRAST
==========================================================

Use:

"action": "verify"
"type": "contrast"

Do not claim an exact measured ratio unless the evidence provides one.

==========================================================
TEST INDEPENDENCE
==========================================================

Prefer independent logical tests.

Avoid one giant test containing unrelated functionality.

==========================================================
FOCUS ACTION — STRICT RULE
==========================================================

When testing whether an element receives focus:

Use the "focus" action.

The expected.type MUST be exactly "focus".

CORRECT:

{
  "step": 1,
  "action": "focus",
  "type": "element",
  "target": "text input field",
  "value": "",
  "key": "",
  "expected": {
    "type": "focus",
    "value": "The target element receives focus."
  }
}

INCORRECT:

{
  "step": 1,
  "action": "focus",
  "type": "element",
  "target": "text input field",
  "value": "",
  "key": "",
  "expected": {
    "type": "element",
    "value": "The target element receives focus."
  }
}

For EVERY "focus" action:

expected.type = "focus"

Never use "element", "text", "visibility", or any other
value as expected.type for a focus action.

==========================================================
CATEGORY VALUES — STRICT RULE
==========================================================

Every test case category MUST use one of these canonical values:

"Functional"
"Accessibility"
"Visual"
"Edge Case"

Do not use plural or alternate forms such as:

"Edge Cases"
"Functional Testing"
"Accessibility Testing"
"Visual Testing"

Always output the canonical singular values exactly.

==========================================================
PRIORITY VALUES
==========================================================

Every test case priority MUST be one of:

"High"
"Medium"
"Low"

==========================================================
OUTPUT
==========================================================

Return ONLY valid JSON.

No Markdown.

No explanations.

The JSON must contain exactly:

{
  "test_cases": [
    {
      "id": "TC-001",
      "title": "",
      "description": "",
      "priority": "High",
      "category": "Functional",
      "preconditions": [],
      "steps": [
        {
          "step": 1,
          "action": "",
          "type": "",
          "target": "",
          "value": "",
          "key": "",
          "expected": {
            "type": "",
            "value": ""
          }
        }
      ],
      "expected_result": "",
      "evidence": ""
    }
  ]
}
"""

    # -----------------------------------------------------
    # Insert analysis into prompt
    # -----------------------------------------------------

    prompt = prompt.replace(
        "__ANALYSIS_JSON__",
        analysis_json,
    )

    # -----------------------------------------------------
    # Gemini request
    # -----------------------------------------------------

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
    )

    response_text = response.text.strip()

    # -----------------------------------------------------
    # Remove accidental Markdown fences
    # -----------------------------------------------------

    if response_text.startswith("```"):

        lines = response_text.splitlines()

        if (
            lines
            and lines[0].strip().startswith("```")
        ):
            lines = lines[1:]

        if (
            lines
            and lines[-1].strip() == "```"
        ):
            lines = lines[:-1]

        response_text = "\n".join(
            lines
        ).strip()

    # -----------------------------------------------------
    # Parse JSON
    # -----------------------------------------------------

    try:

        result = json.loads(
            response_text
        )

    except json.JSONDecodeError as exc:

        raise ValueError(
            "Gemini did not return valid JSON.\n\n"
            f"Gemini response:\n"
            f"{response_text}"
        ) from exc

    # -----------------------------------------------------
    # Strict schema validation
    # -----------------------------------------------------

    validate_generated_test_cases(
        result
    )

    return result
