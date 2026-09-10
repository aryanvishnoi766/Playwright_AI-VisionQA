# AI UI Testing Automation Framework

An intelligent, AI-powered UI testing and test generation automation framework built with Python, Google Gemini, Playwright, and Behave (BDD). 

This project bridges visual UI inspection and robust test automation by automatically analyzing screenshots of web applications, generating structured test cases and Cucumber BDD feature files, resolving UI locators dynamically, and executing tests via Playwright.

---

## 🚀 Key Features

- **AI Vision Analysis**: Inspects UI screenshots using Google Gemini to identify interactive elements, layout structures, and component hierarchy.
- **Automated Test Case Generation**: Generates comprehensive QA test scenarios (positive, negative, and edge cases) from visual UI analysis.
- **BDD Export**: Automatically exports generated test cases into Gherkin feature files (`.feature`).
- **Playwright Test Execution**: Runs robust browser automation test scripts against target URLs with dynamic locator resolution.
- **Comprehensive Reporting**: Captures test execution results, execution summaries, error traces, and failure screenshots.

---

## 📁 Project Directory Structure

```text
AI_UI_Testing/
├── .env                      # Environment variables configuration (API keys, Base URL)
├── main.py                   # Main entry point for running the pipeline and test runner
├── requirments.txt           # Project dependencies
├── app/                      # Core application modules
│   ├── ai/                   # AI integration (Gemini, test case generation, BDD exporter)
│   └── automation/           # Playwright automation engine, locator resolver, and test runner
├── features/                 # Behave BDD features and step definitions
├── input/
│   └── screenshots/          # Source UI screenshots for analysis (e.g., Login_Page.png)
├── output/
│   ├── analysis/             # JSON analysis reports from Gemini Vision
│   ├── failures/             # Failure screenshots and logs
│   ├── reports/              # JSON execution reports and Allure reports
│   └── test_cases/           # Generated test case JSON files
└── tests/                    # Unit and integration tests for framework components
```

---

## 🛠️ Prerequisites

- **Python 3.10+**
- **Google Gemini API Key** (`GEMINI_API_KEY`)

---

## ⚙️ Installation & Setup

1. **Clone the repository / Navigate to project root**:
   ```bash
   cd E:\pythonProject\AI_UI_Testing
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirments.txt
   ```

4. **Install Playwright browser binaries**:
   ```bash
   playwright install
   ```

5. **Configure Environment Variables**:
   Create or update `.env` in the root directory with your settings:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   BASE_URL=https://your-target-website.com
   ```

---

## 🏃 Usage

Run the interactive framework runner:

```bash
python main.py
```

You will be prompted with three options:
1. **Run Full Pipeline (AI Analysis & Test Generation) + Test Execution**
2. **Run Test Execution Only** (using the latest generated test cases) *(Default)*
3. **Run Pipeline Only** (AI Analysis & Test Case Generation)

---

## 🧪 Running Unit Tests

To run the framework's internal test suite using `pytest`:

```bash
pytest
```

---

## 📄 License

This project is licensed under the MIT License.
