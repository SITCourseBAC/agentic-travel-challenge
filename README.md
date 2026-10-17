# Agentic Travel Challenge

A four-week, hands-on Python project for undergraduate students. Build a travel-planning workflow that combines real API searches, multi-agent coordination, tool use, payment authorization, and failure recovery.

**Each week starts in a Jupyter notebook.** Read the explanations and instructor demonstrations, implement the assigned tasks in the corresponding Python source files, then return to the notebook to verify your work and run the tests. Writing an answer only in a notebook cell does not complete the source-file task.

## Project Overview

The project uses a **configurable travel scenario**: retrieve flight and hotel offers, assemble a plan within a budget, and progressively add agent coordination, authorization, and simulated execution.

The initial settings provide an origin, destination, travel dates, traveller count, room allocation, and budget. These are starting parameters, not fixed assignment requirements. Review and adjust them in [`trip_scenario.py`](src/travel_challenge/config/trip_scenario.py) as directed by your instructor. Keep the configuration valid: room occupants must match the traveller count, the return date must follow departure, and the current classroom implementation supports SGD travel pricing only.

Each week builds on previous work:

```text
Week 1: REST offers -> normalization -> selection -> budget check
Week 2: Coordinator -> A2A specialists -> MCP tools -> reuse Week 1
Week 3: x402 paid-resource access + AP2 hotel purchase authorization
Week 4: Simulated execution -> retry / replan and reauthorize
```

By the end of the project, you should be able to:

- Convert external API responses into consistent internal data structures.
- Handle amounts, currencies, and budgets without double-counting prices.
- Distinguish A2A (Agent-to-Agent) coordination from MCP (Model Context Protocol) tool calls.
- Use the official x402 SDK for HTTP 402 responses, signing, and retries, and AP2 (Agent Payments Protocol) models to express purchase conditions.
- Explain explicit consent, authorization binding, idempotent execution, and reauthorization.
- Test successful paths, boundary conditions, and failure scenarios.

> **Real services vs. classroom simulation:** Flight and hotel searches use real Nuitee Sandbox REST requests. Weather data, settlement, and hotel payments are simulated: no bookings are made and no funds move. The x402 exercise uses a temporary, unfunded signing account. AP2 exercises use official models and local merchant signatures, not a complete production trust chain. Do not provide real card details, wallet private keys, or funds.

## Getting Started: No Existing Setup Required

**Recommended: GitHub Codespaces.** You only need a browser, a GitHub account, and an internet connection. No local Python, Git, Docker, or VS Code installation is required.

### Option 1: GitHub Codespaces (Recommended for Class)

1. Sign in to GitHub and open the [course repository](https://github.com/icrainbow/agentic-travel-challenge-student).
2. Select **Fork -> Create fork** to create your own copy. If your instructor uses GitHub Classroom, use your assigned repository instead.
3. In **your own repository**, select **Code -> Codespaces -> Create codespace on main**. Choose a 2-core machine if asked.
4. Wait for setup to finish. The [Dev Container configuration](.devcontainer/devcontainer.json) installs the project, protocol dependencies, Jupyter, and editor extensions, then runs infrastructure checks. The first launch may take several minutes. Resolve any setup errors before proceeding.
5. Open [`01_Week1_Contracts_and_Baseline.ipynb`](notebooks/student/01_Week1_Contracts_and_Baseline.ipynb) from the file explorer.
6. If prompted to **Select Kernel**, choose **Python Environments** and the Python 3.11 environment containing the installed project dependencies, usually the recommended environment.
7. Configure your Nuitee API key as described below. Read and run the notebook one cell at a time.

#### Free Usage and Cost Awareness

Codespaces includes a monthly allowance, not unlimited free usage. GitHub Free personal accounts currently include **120 core-hours** (approximately **60 running hours on a 2-core machine**) and **15 GB-month of storage**. All Codespaces on your account share this allowance. Check the [official billing documentation](https://docs.github.com/en/billing/concepts/product-billing/github-codespaces) for current terms.

- After class, select **Stop codespace** at [github.com/codespaces](https://github.com/codespaces). Closing the browser does not stop it immediately.
- Stopped Codespaces still consume storage allowance.
- Changes are not automatically pushed to GitHub. Commit and push your work before deleting a Codespace.
- Without a valid payment method, usage is blocked when your allowance is exhausted. If you have a payment method, review your budgets and overage settings.
- Third-party API quotas and charges are separate from Codespaces usage.

### Option 2: Local VS Code

Choose this option for longer-term use or to avoid cloud compute limits.

First install:

- [Python 3.11](https://www.python.org/downloads/) to match the course container. On Windows, enable the installer option to add Python to PATH.
- [Git](https://git-scm.com/downloads).
- [VS Code](https://code.visualstudio.com/) with Microsoft's **Python** and **Jupyter** extensions.

Clone your own fork and enter the project directory. Replace `YOUR_USERNAME` with your GitHub username; Classroom users should use their assigned repository URL.

```bash
git clone https://github.com/YOUR_USERNAME/agentic-travel-challenge-student.git
cd agentic-travel-challenge-student
```

Create and activate a virtual environment:

**macOS / Linux**

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

**Windows PowerShell**

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, open Windows Command Prompt (cmd) in the project directory and run `.venv\Scripts\activate.bat` instead, then continue there.

With the environment activated, install the project and notebook tools:

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[protocols]"
python -m pip install "jupyterlab>=4,<5" "ipykernel>=6,<7"
python -m pytest -m scaffold -q
```

Installation requires internet access. The AP2 dependency is installed from GitHub, so Git must be available. The editable installation (`-e`) lets you modify project source files without reinstalling the package.

In VS Code, select **File -> Open Folder** and open the entire project directory, not just an individual notebook. Run **Python: Select Interpreter** from the Command Palette and select `.venv`. Open the Week 1 notebook and select the same virtual environment as its kernel.

### Option 3: Local JupyterLab

If you prefer a browser-based interface without VS Code, complete the Python, Git, cloning, virtual environment, and dependency installation steps in Option 2. VS Code and its extensions are not required for this option.

From the project root, with the virtual environment activated, run:

```bash
python -m jupyterlab
```

Open the local URL shown in the terminal, navigate to [`notebooks/student/`](notebooks/student), and open the current week's notebook. Use JupyterLab's text editor to edit the assigned Python files, save them, and return to the notebook to verify your changes.

### Reading on GitHub Without Running Code

Click any `.ipynb` file on GitHub to preview its instructions and code. **The normal GitHub file page cannot execute Python.** The github.dev editor opened by pressing `.` also does not provide the Python runtime required for this project. Use one of the options above to run the exercises.

## Configure Your Nuitee API Key

Real travel searches require a **Nuitee Sandbox API key**, provided by your instructor or obtained following their instructions.

In the project root, copy [`.env.example`](.env.example) to a new file named `.env`. Replace the placeholder with your own key:

```dotenv
NUITEE_API_KEY=your_api_key_here
```

- You can copy and edit the file using the file explorer in Codespaces, VS Code, or JupyterLab.
- `.env` is ignored by Git. Never paste real keys into source files, notebooks, screenshots, commits, or assignment reports.
- Infrastructure (`scaffold`) tests do not require a real API key. Live search cells require a valid key, internet access, and appropriate API permissions.
- If a search fails, investigate the error, credentials, quota, and request conditions. Do not fabricate prices to make later cells appear successful.

## Four-Week Learning Path

Each notebook is organized around an approximately 120-minute lab. Work through the weeks in order: Week 2 reuses Week 1 functions, while the hotel authorization and execution exercises use a plan produced earlier.

| Week | Start Here | Source Files to Modify | Main Tasks |
|---|---|---|---|
| **1: Real Offers and Budgeting** | [Contracts and Baseline](notebooks/student/01_Week1_Contracts_and_Baseline.ipynb) | [`week1/trip_planner.py`](src/travel_challenge/week1/trip_planner.py) | Build room occupancies; normalize flight and hotel responses; select the cheapest offers; assemble a plan and check its budget. |
| **2: Agents and Tools** | [A2A and MCP](notebooks/student/02_Week2_A2A_and_MCP.ipynb) | [`week2/travel_agents.py`](src/travel_challenge/week2/travel_agents.py), [`week2/a2a_coordinator.py`](src/travel_challenge/week2/a2a_coordinator.py) | Invoke the MCP flight tool; reuse hotel normalization and selection; construct an official A2A request for the coordinator to obtain specialist offers. |
| **3: Paid Access and Authorization** | [x402 and AP2](notebooks/student/03_Week3_x402_and_AP2.ipynb) | [`week3/paid_weather.py`](src/travel_challenge/week3/paid_weather.py), [`week3/authorization.py`](src/travel_challenge/week3/authorization.py) | Decode HTTP 402 requirements; sign and retry with the official SDK; construct AP2 mandates; validate purchase conditions against authorization. |
| **4: Execution and Recovery** | [Replanning and Payment](notebooks/student/04_Week4_Replanning_and_Payment.ipynb) | [`week4/payment_execution.py`](src/travel_challenge/week4/payment_execution.py) | Use previous receipts to prevent duplicate execution; distinguish retries from replanning; reuse Week 3 authorization after a price change. |

**Amount conventions:** Travel prices use integer SGD cents. Flight totals already cover all travellers and both directions. Hotel totals already cover all requested rooms and the entire stay. Do not multiply those totals again. In the separate x402 exercise, 3000 USDC minor units means 0.003 USDC, not SGD cents.

### Weekly Workflow

1. Open the week's notebook and read its objectives, prerequisites, and instructor-provided demonstrations.
2. Run setup and demonstration cells in order. Use the play button or **Shift + Enter** to execute a cell; do not start by running the entire unfinished notebook.
3. At each Task, open the corresponding source file. Implement the function using its docstring, input/output contract, and tests. Starter `NotImplementedError` exceptions deliberately mark unfinished exercises.
4. Save the source file, then rerun the relevant notebook verification cells. Key cells use `importlib.reload`; if stale behavior remains, restart the kernel and rerun preceding cells in order.
5. If you changed code used by a running service, run the notebook's **Shutdown** cell and restart the service. Reloading a module in the notebook does not update a separate service process.
6. Run the week's tests and fix failures before moving on. Do not delete tests, weaken assertions, or hard-code example outputs to bypass the task.
7. Before finishing, stop the notebook services, save your files, and commit and push your work to your own assignment repository.

Weeks 1 and 2 export a real travel plan to `trip_plan.json` in the project root for later AP2 and execution exercises. This generated file is ignored by Git; regenerate it when moving to a new environment. The standalone x402 section of Week 3 does not depend on this file.

## Testing and Completion Criteria

Run these commands from the **project root**, using the Python environment where you installed the dependencies.

Check instructor-provided infrastructure; these checks should pass before you implement the exercises:

```bash
python -m pytest -m scaffold -q
```

Check student tasks for one week (replace the filename for Weeks 2, 3, or 4):

```bash
python -m pytest tests/test_week1.py -m student -q
```

Run all checks for a week, or the full suite after completing all four weeks:

```bash
python -m pytest tests/test_week1.py -q
python -m pytest -q
```

- **`scaffold`** checks cover provided REST, protocol, and execution infrastructure.
- **`student`** checks cover your implementation tasks. These intentionally fail in the starter project; they are not evidence of a failed installation.
- A completed week includes implemented source-file tasks, verified notebook execution, passing weekly tests, and an explanation of the key design decisions.
- Fixed test inputs validate logic; they do not replace the notebook's real API searches.

## Repository Structure

```text
.devcontainer/                 Automatic Codespaces / Dev Containers setup
.env.example                   API key template without real credentials
notebooks/student/             Weekly instructions, demonstrations, and checks
src/travel_challenge/
  config/trip_scenario.py       Editable travel requirements
  sdk_support/                 Provided protocol adapters and signing helpers
  week1/                       REST searches and travel planning
  week2/                       A2A agents, coordinator, and MCP tools
  week3/                       x402 weather access and AP2 authorization
  week4/                       Simulated execution, retries, and reauthorization
tests/                         Infrastructure and student acceptance tests
pyproject.toml                 Dependencies, package, and test configuration
```

Focus on the task functions identified in each notebook. Unless instructed otherwise, do not rewrite the protocol adapters, provided execution skeletons, or tests.

## Troubleshooting

| Symptom | What to Check |
|---|---|
| Notebook displays but has no run button | You may be on GitHub's preview page. Open it in Codespaces, local VS Code, or JupyterLab. |
| `ModuleNotFoundError` | Ensure the kernel uses the environment where you ran `python -m pip install -e ".[protocols]"`. |
| `NotImplementedError` or failing student tests | Read the task instructions and implement the corresponding source-file function. |
| Missing key, HTTP 401/403, or network errors | Check the root `.env`, Sandbox key permissions, quota, and connectivity; contact your instructor if needed. |
| Source changes have no effect | Save and reload the module. For service code, run Shutdown and restart the service. |
| Port 8001, 8010, or 8020 is occupied | Shut down services from previous runs using the notebook's Shutdown cell before starting another instance. |
| Missing `trip_plan.json` in a later week | Complete the real search and plan export in Week 1 or Week 2. |
| Codespace cannot resume | Check compute and storage allowance. Wait for renewal or continue with a local setup. |

**Submission:** Save, commit, and push the notebooks, source changes, and explanations required by your instructor. Never submit API keys, real payment details, or virtual environments. Clear unnecessary notebook outputs before sharing, particularly outputs that might contain credentials or personal information.
