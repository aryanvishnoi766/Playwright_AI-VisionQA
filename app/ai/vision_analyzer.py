import os
import json
from pathlib import Path

from dotenv import load_dotenv
from google import genai


# Load environment variables
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is not set in .env")


# Create Gemini client
client = genai.Client(api_key=api_key)

MODEL_NAME = os.getenv("GEMINI_MODEL")


def analyze_screenshot(image_path):

    # Analyze a UI screenshot and return structured JSON.

    image_path = Path(image_path)

    if not image_path.exists():
        raise FileNotFoundError(f"Screenshot not found: {image_path}")

    # Read screenshot
    with open(image_path, "rb") as image_file:
        image_bytes = image_file.read()

    prompt = """
    You are an expert Manual QA Engineer, Accessibility Tester,
    and UI Analysis Engineer.

    Analyze the provided UI screenshot.

    Your job is to identify ONLY facts that can be visually observed
    or reliably identified from the screenshot.

    The screenshot is the ONLY source of truth.

    Do NOT assume application behavior that cannot be established
    from the screenshot.

    Return ONLY valid JSON.
    Do not use Markdown.
    Do not add explanations before or after the JSON.

    ============================================================
    REQUIRED JSON STRUCTURE
    ============================================================

    {
      "page_purpose": "",
      "ui_elements": [
        {
          "type": "",
          "name": "",
          "text": "",
          "placeholder": "",
          "visible": true,
          "identifiable": true,
          "evidence": ""
        }
      ],
      "interaction_evidence": [
        {
          "element": "",
          "supported_actions": [],
          "evidence": ""
        }
      ],
      "accessibility_evidence": [
        {
          "element": "",
          "property": "",
          "evidence": ""
        }
      ],
      "visual_evidence": [
        {
          "element": "",
          "property": "",
          "observation": ""
        }
      ],
      "functional_test_scenarios": [
        {
          "id": "",
          "title": "",
          "description": "",
          "evidence": ""
        }
      ],
      "accessibility_test_scenarios": [
        {
          "id": "",
          "title": "",
          "description": "",
          "evidence": ""
        }
      ],
      "edge_cases": [
        {
          "id": "",
          "title": "",
          "description": "",
          "evidence": ""
        }
      ],
      "potential_issues": [
        {
          "severity": "",
          "issue": "",
          "reason": "",
          "evidence": ""
        }
      ]
    }

    ============================================================
    UI ELEMENT IDENTIFICATION
    ============================================================

    Identify only elements that are actually visible or reliably
    identifiable.

    Allowed element types include:

    - input
    - button
    - link
    - checkbox
    - radio
    - heading
    - text
    - image
    - icon
    - select
    - textarea
    - other

    For every element provide:

    - type
    - name
    - visible
    - identifiable
    - evidence

    The "name" must be a stable human-readable description.

    Examples:

    "Email input"
    "Password input"
    "Login button"
    "Forgot password link"
    "Register link"

    Do NOT invent:

    - selectors
    - XPath
    - CSS
    - IDs
    - classes
    - DOM attributes that cannot be seen
    - URLs

    ============================================================
    ELEMENT TARGET QUALITY
    ============================================================

    An element is "identifiable": true only when an automation
    system could reasonably identify it from its visible text,
    role, label, placeholder, or another clearly observable property.

    Examples of strong targets:

    "Login button"
    "Email input"
    "Password input"
    "Forgot password link"
    "Register here link"

    Be careful with icon-only elements.

    For example:

    "Facebook Icon"

    may be visually identifiable, but its accessible name,
    ARIA label, destination URL, or DOM identity cannot be known
    from the screenshot.

    Therefore record the uncertainty in "evidence".

    Do NOT invent an accessible name for icon-only elements.

    ============================================================
    INTERACTION EVIDENCE
    ============================================================

    Record only actions that are visually supported.

    Examples:

    A visible button supports:

    ["click"]

    A visible text input supports:

    ["fill"]

    A visible link supports:

    ["click"]

    A visible input may support keyboard interaction, but the
    screenshot does NOT establish the actual keyboard focus order.

    Do NOT claim that clicking an element navigates to a particular
    page unless the screenshot explicitly provides evidence of the
    destination.

    For example:

    A visible "Forgot password?" link proves:

    "Forgot password link exists"

    It does NOT prove:

    "Clicking it navigates to the password recovery page"

    Therefore:

    supported_actions may contain:

    ["click"]

    but navigation behavior must remain UNKNOWN unless evidence
    exists.

    ============================================================
    NAVIGATION EVIDENCE
    ============================================================

    A screenshot alone normally cannot establish:

    - destination URL
    - redirect behavior
    - SPA route
    - navigation result
    - API behavior

    Do NOT invent navigation destinations.

    Only record a navigation destination if it is explicitly visible
    or provided as input data.

    Examples of valid evidence:

    "URL bar information is provided separately."

    "Navigation destination is explicitly shown in the analysis."

    Otherwise navigation behavior is UNKNOWN.

    ============================================================
    KEYBOARD AND FOCUS EVIDENCE
    ============================================================

    This is extremely important.

    A static screenshot cannot establish actual keyboard tab order.

    Do NOT infer:

    "First Tab focuses Email input."

    Do NOT infer:

    "Tab order is top-to-bottom."

    Do NOT infer:

    "Tab order is left-to-right."

    Do NOT infer the exact sequence of focusable elements.

    The screenshot may show that interactive elements exist,
    but actual keyboard focus behavior requires runtime testing.

    Therefore accessibility evidence may say:

    "Interactive controls are visible and keyboard accessibility
    should be tested."

    But it must NOT claim an exact focus order.

    ============================================================
    ACCESSIBILITY EVIDENCE
    ============================================================

    Only report accessibility properties that can actually be
    observed or reasonably evaluated from the screenshot.

    Possible visual evidence:

    - visible labels
    - visible text
    - visible focus indicator
    - visible contrast problem
    - visible control type
    - visible heading hierarchy

    Do NOT claim that an element has:

    - aria-label
    - aria-labelledby
    - role
    - accessible name
    - semantic HTML
    - label association

    unless this information is explicitly provided outside the
    screenshot.

    A screenshot cannot prove DOM accessibility attributes.

    Therefore:

    "Email input appears to have visible text nearby"

    is acceptable.

    "Email input has aria-label='Email'"

    is NOT acceptable unless explicitly provided.

    ============================================================
    CONTRAST EVIDENCE
    ============================================================

    Contrast may be visually suspicious from a screenshot.

    If poor contrast is visibly apparent, report it as an observation.

    Do NOT invent an exact contrast ratio.

    Do NOT claim WCAG compliance or non-compliance solely from
    visual appearance unless actual color information is available.

    Use language such as:

    "Text appears to have low contrast against the background."

    ============================================================
    VISUAL EVIDENCE
    ============================================================

    Record visually observable properties such as:

    - spelling
    - typography
    - alignment
    - overlap
    - clipping
    - truncation
    - spacing
    - contrast
    - inconsistent wording
    - visible layout problems

    Example:

    {
      "element": "Password input",
      "property": "placeholder",
      "observation": "Placeholder appears to contain a spelling error."
    }

    ============================================================
    FUNCTIONAL TEST SCENARIOS
    ============================================================

    Generate functional scenarios only when the visible UI provides
    a meaningful basis for the test.

    A visible button or input can justify testing its interaction.

    However, do NOT assume the result of an interaction.

    For example:

    Allowed:

    "Verify Login button can be activated."

    Not automatically allowed:

    "Verify Login redirects to dashboard."

    unless the destination is explicitly known from evidence.

    Do NOT invent:

    - success messages
    - error messages
    - redirect URLs
    - API behavior
    - backend behavior
    - authentication behavior

    ============================================================
    ACCESSIBILITY TEST SCENARIOS
    ============================================================

    Accessibility scenarios may be suggested when the screenshot
    contains relevant UI.

    However, clearly distinguish:

    OBSERVABLE:
    - visible labels
    - visible focus indicator
    - visible contrast
    - visible control types

    RUNTIME-DEPENDENT:
    - actual tab order
    - actual keyboard focus sequence
    - screen reader announcements
    - ARIA attributes
    - accessible name computation
    - label association

    Runtime-dependent behavior may be suggested as a test objective,
    but the expected result must NOT contain unsupported assumptions.

    For example:

    GOOD:

    "Verify keyboard users can move through interactive controls
    using Tab."

    BAD:

    "Press Tab once and verify Email input receives focus."

    unless focus order is explicitly provided.

    ============================================================
    EDGE CASES
    ============================================================

    Only generate edge cases that can be meaningfully executed
    using the visible UI.

    Good examples:

    - empty visible input
    - whitespace input
    - invalid format where an input clearly expects a format
    - keyboard interaction
    - boundary input when field constraints are explicitly known

    Do NOT generate tests for:

    - SQL injection
    - XSS
    - API failures
    - network failures
    - backend failures
    - duplicate API requests

    unless the supplied evidence specifically supports them.

    ============================================================
    RESPONSIVENESS
    ============================================================

    Do NOT call a test "responsive", "responsive design",
    or "viewport responsiveness" merely because the screenshot
    shows a UI layout.

    A responsiveness test requires a viewport/device condition
    to be changed.

    A static screenshot may identify a potential layout issue,
    but it does NOT prove responsive behavior.

    ============================================================
    POTENTIAL ISSUES
    ============================================================

    Report genuine visible issues.

    Examples:

    - spelling mistakes
    - incorrect wording
    - visible clipping
    - overlap
    - poor contrast
    - inconsistent labels
    - obvious alignment problems

    Do NOT invent issues that cannot be observed.

    For each issue provide evidence.

    ============================================================
    UNKNOWN BEHAVIOR
    ============================================================

    When information cannot be determined from the screenshot,
    explicitly treat it as UNKNOWN.

    Examples:

    - link destination
    - URL after clicking
    - actual keyboard focus order
    - screen reader output
    - ARIA attributes
    - DOM structure
    - backend behavior
    - API behavior
    - form submission result

    UNKNOWN information must NOT be converted into a factual claim.

    ============================================================
    EVIDENCE-FIRST RULE
    ============================================================

    Every scenario must contain evidence.

    Before generating a scenario ask:

    1. What visible evidence supports this test?
    2. Can the test be executed without inventing selectors?
    3. Can the expected result be determined without inventing
       application behavior?
    4. Is the target a real visible UI element?
    5. Is the behavior observable from the available evidence?

    If the answer is NO, do not generate the scenario.

    Evidence is more important than test-case quantity.

    ============================================================
    FINAL VALIDATION
    ============================================================

    Before returning JSON:

    1. Verify every UI element is visually supported.
    2. Verify every test scenario has evidence.
    3. Remove unsupported navigation assumptions.
    4. Remove unsupported focus-order assumptions.
    5. Remove unsupported screen-reader claims.
    6. Remove unsupported ARIA claims.
    7. Remove unsupported URLs.
    8. Remove unsupported error messages.
    9. Remove unsupported backend behavior.
    10. Remove unsupported responsiveness claims.
    11. Do not invent technical locators.
    12. Preserve genuine visible defects.
    13. Clearly identify uncertain or runtime-dependent behavior.
    14. Return ONLY valid JSON.
    """

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[
            prompt,
            genai.types.Part.from_bytes(
                data=image_bytes,
                mime_type="image/png"
            )
        ]
    )

    # Convert Gemini response into Python JSON
    text = response.text.strip()
    # Remove markdown code blocks if present
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
        if text.endswith("```"):
            text = text[:-3].strip()

    # Clean up accidental markdown list markers inside json (e.g. - "property": ...)
    import re
    text = re.sub(r'^\s*-\s*', '', text, flags=re.MULTILINE)

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Gemini did not return valid JSON: {e}\n\n"
            f"Gemini response:\n{response.text}"
        )
