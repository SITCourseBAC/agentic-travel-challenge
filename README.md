# BAC3002 Agentic Travel Challenge

## Contents

- [Project overview](#project-overview)
- [Project structure](#project-structure)
- [Set up your environment](#set-up-your-environment)
- [Configure the Nuitee Sandbox key](#configure-the-nuitee-sandbox-key)
- [Work through the notebooks](#work-through-the-notebooks)
- [Run tests](#run-tests)
- [Troubleshooting](#troubleshooting)

## Project overview

This four-week Python project builds a travel-planning workflow that gathers flight and hotel offers, coordinates specialist agents, checks purchase authorization, and exercises simulated payment recovery. Flight and hotel searches use the Nuitee Sandbox API; the protocol exercises use the official A2A, MCP, x402, and AP2 SDKs. The notebooks guide you through 14 coding tasks implemented in Python source files, with pytest checks for the supplied infrastructure and your work. The shared travel scenario is configurable, and the exercises build on earlier weeks. No hotel or flight is booked, and no real payment or settlement occurs. Weather access and payment execution are classroom simulations.

| Week | Topic | Implementation |
|---|---|---|
| W1 | REST | Travel quotes, normalization, and a budgeted trip plan |
| W2 | MCP + A2A | Specialist agent coordination |
| W3 | x402 + AP2 | Paid API access and purchase authorization |
| W4 | Payment execution | Simulated payment, retry, idempotency, and replanning |

## Project structure

```text
notebooks/student/              Four guided weekly notebooks
src/travel_challenge/
  config/                       Shared travel scenario
  sdk_support/                  Instructor-provided protocol support
  week1/                          REST searches and travel planning
  week2/                          MCP tools and A2A agents
  week3/                          x402 weather and AP2 authorization
  week4/                          Simulated payment execution
tests/                          Scaffold and student pytest checks
.devcontainer/                  Codespaces environment and setup
.env.example                    Nuitee key placeholder
pyproject.toml                  Python requirements and test configuration
```

## Set up your environment

The project targets Python 3.11. Run commands from the project root—the directory containing `pyproject.toml`.

### Option 1: GitHub Codespaces (recommended)

1. Open this project in GitHub Codespaces and create a Codespace on `main`.
2. Wait for the devcontainer setup to finish. [`.devcontainer/devcontainer.json`](.devcontainer/devcontainer.json) selects the Python 3.11 image and the Python, Pylance, and Jupyter extensions. Its post-create script installs the project with its `protocols` extra, installs JupyterLab and `ipykernel`, and runs the scaffold tests.
3. In the integrated terminal, verify the environment and rerun the infrastructure checks:

   ```bash
   python --version
   python -m pytest -m scaffold -q
   ```

   Python should report 3.11.x. Resolve any setup or test error before continuing.
4. Open [`01_Week1_Contracts_and_Baseline.ipynb`](notebooks/student/01_Week1_Contracts_and_Baseline.ipynb). When prompted, select the Python 3.11 environment that was set up for the project as the notebook kernel.
5. Configure your Nuitee key, then run the notebook cells in order.

Stop a Codespace when you are finished; resume it later from Codespaces. Usage is subject to GitHub's current compute and storage quotas.

### Option 2: Local VS Code

Install [Python 3.11](https://www.python.org/downloads/), [Git](https://git-scm.com/downloads), and [VS Code](https://code.visualstudio.com/). In VS Code, install Microsoft's [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python) and [Jupyter](https://marketplace.visualstudio.com/items?itemName=ms-toolsai.jupyter) extensions. Open the project root folder and a terminal there. Check Python and Git versions:

**Windows PowerShell**

```powershell
py -3.11 --version
git --version
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python --version
python -m pip install --upgrade pip
python -m pip install -e '.[protocols]'
python -m pip install 'jupyterlab>=4,<5' 'ipykernel>=6,<7'
python -m pytest -m scaffold -q
```

If PowerShell blocks environment activation, allow it only for the current PowerShell process, then activate again. This does not change the machine's persistent execution policy:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

**macOS Terminal**

```bash
python3.11 --version
git --version
python3.11 -m venv .venv
source .venv/bin/activate
python --version
python -m pip install --upgrade pip
python -m pip install -e '.[protocols]'
python -m pip install 'jupyterlab>=4,<5' 'ipykernel>=6,<7'
python -m pytest -m scaffold -q
```

The `protocols` extra is defined in [`pyproject.toml`](pyproject.toml); it includes the official SDK dependencies, including AP2 installed from Git. After installation, use **Python: Select Interpreter** in VS Code and choose `.venv` (`.venv\Scripts\python.exe` on Windows or `.venv/bin/python` on macOS). Open a notebook and select that same `.venv` environment as its kernel.

Alternatively, start JupyterLab from the activated environment with `python -m jupyterlab`, open the URL it prints, and browse to `notebooks/student/`.

## Configure the Nuitee Sandbox key

Obtain a Nuitee Sandbox key through the instructor's announced process. In the project root, copy [`.env.example`](.env.example) to `.env` and replace the placeholder:

```dotenv
NUITEE_API_KEY=your_api_key_here
```

The Week 1 notebook's live flight or hotel search uses `NUITEE_API_KEY` to verify that the key works. The project loads `.env` when a Nuitee request runs; an environment variable with the same name takes precedence. Scaffold tests do not need a real key. `.env` is ignored by Git: never add it to source files, notebooks, screenshots, or shared output.

## Work through the notebooks

| Week | Notebook | Student-editable Python files |
|---|---|---|
| 1 | [`01_Week1_Contracts_and_Baseline.ipynb`](notebooks/student/01_Week1_Contracts_and_Baseline.ipynb) | [`week1/trip_planner.py`](src/travel_challenge/week1/trip_planner.py) |
| 2 | [`02_Week2_A2A_and_MCP.ipynb`](notebooks/student/02_Week2_A2A_and_MCP.ipynb) | [`week2/travel_agents.py`](src/travel_challenge/week2/travel_agents.py), [`week2/a2a_coordinator.py`](src/travel_challenge/week2/a2a_coordinator.py) |
| 3 | [`03_Week3_x402_and_AP2.ipynb`](notebooks/student/03_Week3_x402_and_AP2.ipynb) | [`week3/paid_weather.py`](src/travel_challenge/week3/paid_weather.py), [`week3/authorization.py`](src/travel_challenge/week3/authorization.py) |
| 4 | [`04_Week4_Replanning_and_Payment.ipynb`](notebooks/student/04_Week4_Replanning_and_Payment.ipynb) | [`week4/payment_execution.py`](src/travel_challenge/week4/payment_execution.py) |

Follow the notebook sequence: **Read notebook → implement the TODO in Python source → save → rerun cells → test.** Open `.ipynb` files in VS Code with the Jupyter extension (or in JupyterLab), not as plain text or raw JSON. Run a cell with **Shift+Enter**. `NotImplementedError` marks an unfinished task. If an edit is not reflected, save the `.py` file and rerun the notebook's module reload cell; otherwise restart the kernel and rerun setup cells. If you changed code used by a notebook-launched service, stop and restart that service with the notebook's shutdown/startup cells.

Week 2 reuses Week 1 planning functions. Weeks 3–4 use a generated `trip_plan.json`: Week 1 exports it, and Week 2 can overwrite it with its agent-built plan. It is generated automatically and ignored by Git, so do not create or upload it manually. In a fresh environment, rerun the Week 1 or Week 2 notebook's plan-export cells before the AP2 sections in Weeks 3–4. Week 3's standalone weather exercise does not depend on this file.

Travel prices are integer SGD cents. Flight quotes already cover all travellers and both directions; hotel rates already cover all requested rooms and nights. Do not multiply either total again. The separate x402 example uses 3000 USDC minor units (0.003 USDC), not SGD cents.

## Run tests

Run commands from the project root with the project environment active:

```bash
# Instructor-provided infrastructure (no real Nuitee key required)
python -m pytest -m scaffold -q

# Week 1 student tasks
python -m pytest tests/test_week1.py -m student -q

# Week 2 student tasks
python -m pytest tests/test_week2.py -m student -q

# Week 3 student tasks
python -m pytest tests/test_week3.py -m student -q

# Week 4 student tasks
python -m pytest tests/test_week4.py -m student -q
```

Scaffold tests check the supplied REST, SDK, and simulated execution infrastructure. Student tests exercise the TODO implementations and are expected to fail until the corresponding tasks are complete. To run all tests in one week, omit `-m student`; to run the entire suite after completing the tasks, use `python -m pytest -q`.

## Troubleshooting

| Problem | What to do |
|---|---|
| Codespaces setup fails | Read the setup error in the creation log. Reopen/rebuild the container after correcting the reported environment issue; the setup script must finish successfully. |
| Python 3.11 is missing or wrong | Install/select Python 3.11 and verify with `python --version` (`py -3.11 --version` on Windows before creating `.venv`). |
| Dependency installation fails | Activate `.venv`, check internet access and Git availability, then rerun the failed `python -m pip install` command from the project root. |
| PowerShell blocks activation | Use the process-scoped `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, then activate `.venv` again. |
| Notebook opens as JSON or text | Open it in VS Code with the Jupyter extension enabled, or open it from JupyterLab. |
| Notebook kernel is missing or incorrect | Install `ipykernel` in the project environment, then select `.venv` / Python 3.11 from **Select Kernel**. |
| `ModuleNotFoundError` | Select the same environment where you installed the project; from the project root, rerun `python -m pip install -e '.[protocols]'`. |
| Saved `.py` changes do not appear | Save the file, run the notebook's module reload cell, or restart the kernel. Restart any service process that imports the edited module. |
| `NotImplementedError` appears | Implement the function identified by the notebook task in its source file, save, then rerun the cell. |
| Nuitee key missing or rejected | Check the root `.env` spelling and `NUITEE_API_KEY` value. For HTTP 401/403, verify that the Sandbox key is valid and enabled for the requested API. |
| API request times out or returns no offers | Check internet access, dates, destination and scenario inputs; retry the live search. An empty offer list can occur and is not a reason to invent a quote. |
| Local service port is occupied | Run the notebook's shutdown cell for existing services before starting again. The notebooks use ports 8001, 8010, and 8020. |
| `trip_plan.json` is missing | Run the Week 1 or Week 2 plan-export cells. Weeks 3–4 read the generated file from the project root. |
