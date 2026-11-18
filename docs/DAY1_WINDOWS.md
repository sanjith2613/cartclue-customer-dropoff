# Day 1: CartClue on Windows — 2-hour guide

**Goal:** open the simulated demo dashboard, understand the first five KPIs, and run automated tests. **You do NOT need BigQuery, SQL, Google Cloud, Git or GitHub today.** This is a local app using free Python packages.

## 0–25 minutes: Get the prerequisites

1. On your Windows PC (not your phone), visit **https://www.python.org/downloads/windows/**.
2. Download the **Python 3.13.x Windows installer (64-bit)**; do not choose an embeddable ZIP. Run the `.exe`. If the installer offers **Add python.exe to PATH**, select it, and use **Install Now**. If you already have Python 3.13, skip this installation.
3. Visit **https://code.visualstudio.com/download**. Choose **Windows User Installer**, open the `.exe` and install VS Code.
4. In VS Code, open **Extensions** (left-side four-square icon), find **Python** by Microsoft, and install it.
5. To check Python, open a fresh **Command Prompt** (Start → type `cmd`) and type `py -3.13 --version`. You should see `Python 3.13.x`.

## 25–40 minutes: Unzip the CartClue project

1. Download `CartClue_Windows_Day1_Ready.zip` to your Windows PC.
2. Open **File Explorer → Downloads**.
3. Right-click the ZIP → **Extract All** → **Extract**.
4. Open the extracted folder, then the folder called **`cartclue_portfolio`**.
5. Check that this folder contains `app.py`, `requirements.txt`, `START_CARTCLUE_WINDOWS.cmd`, and folders named `data`, `scripts`, `cartclue`, `docs`.
6. Open **VS Code → File → Open Folder** → select `cartclue_portfolio` (the folder with `app.py`) → **Select Folder**.
7. If VS Code asks whether you trust the project, review the files and choose **Yes, I trust the authors** only if you trust the downloaded starter.

## 40–65 minutes: One-click automated setup

1. In **File Explorer**, double-click `START_CARTCLUE_WINDOWS.cmd` in `cartclue_portfolio`.
2. Windows may show a security prompt for downloaded script files. If you do not trust the source or the script, do not bypass security prompts; use the transparent manual steps below instead.
3. It will create `.venv`, install dependencies, create simulated session data, run pytest, generate a Markdown report and launch Streamlit.
4. Expected tests: **`12 passed`**. The test count may change if you change the code.
5. A browser should open. If it does not, type **http://localhost:8501** in Chrome or Edge while the terminal window remains open.
6. You should see **🛒 CartClue**, a **SIMULATED DEMO** warning and the six tabs **Overview**, **Journey**, **Segments**, **Anomalies**, **Decision lab**, **Data quality**.

### Manual backup (if the one-click setup fails)

In VS Code: **Terminal → New Terminal**. Click the dropdown arrow next to `+` → **Select Default Profile → Command Prompt** (not PowerShell), then open another terminal if necessary. Ensure the terminal path ends in `cartclue_portfolio`. Enter one line at a time:

```bat
py -3.13 --version
py -3.13 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe scripts\sprint.py demo
.venv\Scripts\python.exe scripts\sprint.py launch
```

You do not have to activate `.venv`, so this avoids PowerShell execution-policy errors. To stop the app, click the running terminal and press **Ctrl+C**. To reopen it, double-click `REOPEN_CARTCLUE_WINDOWS.cmd`, or run the last line in the terminal again.

## 65–105 minutes: Explore the app like a product analyst

1. Look at the four KPI boxes across the top. Write down session count, purchasing sessions, session conversion percentage and recorded revenue.
2. Calculate **session conversion rate** yourself: `(purchasing sessions / total sessions) × 100`. Compare with the app's displayed value.
3. Click **Overview**: inspect daily sessions and daily conversion charts.
4. Click **Journey**: read the ordered stages **Sessions → Product views → Added to cart → Checkout started → Purchased**.
5. Calculate **step drop-off** between `Added to cart` and `Checkout started`: `(add-to-cart sessions – checkout sessions) / add-to-cart sessions × 100`.
6. Click **Segments**: choose **Device** and compare **mobile**, **desktop** and **tablet** conversion rates.
7. Click **Anomalies**: inspect dates flagged as unusual. Remember: an anomaly is not an explanation.
8. Click **Decision lab**: move the what-if uplift slider. This is **simulated potential**, not real extra income.
9. Click **Data quality**: understand why the project checks missing identifiers, duplicates and funnel consistency.
10. In the sidebar, select just **mobile** in the **Device** filter. Observe how the KPIs and charts change. Restore the original selection afterward.

## 105–120 minutes: Save your Day 1 proof of work

1. In the browser, press **Windows + Shift + S** and capture the overview page and the Journey tab. Save screenshots in a folder on your desktop named `CartClue_Day1`. Keep the **SIMULATED DEMO** label visible.
2. In `cartclue_portfolio`, open `reports/demo_findings.md` in VS Code and skim the auto-generated report.
3. Create a text note containing: (a) today's conversion rate, (b) one step drop-off rate, (c) one question about mobile visitors, (d) why demo data cannot prove a real business problem.
4. **Day 1 success:** local dashboard works, tests passed, and you can explain two metrics without copying code.

## Common problems

- **`py` is not recognized / `Requested Python version not installed`:** install Python 3.13 64-bit, then close and reopen terminal / VS Code.
- **`requirements.txt` not found:** you are in the wrong folder; use the one containing `app.py`.
- **`No module named streamlit`:** rerun the `...pip install -r requirements.txt` command and make sure it finished without errors.
- **PowerShell says running scripts is disabled:** do not change global policy; use **Command Prompt** and direct `.venv\Scripts\python.exe` commands.
- **Browser doesn't open:** while the Streamlit command is running, visit **http://localhost:8501** manually.
- **Port 8501 already in use:** stop the prior Streamlit terminal with Ctrl+C, or run `.venv\Scripts\python.exe -m streamlit run app.py --server.port 8502` and visit `http://localhost:8502`.
- **SmartScreen/security warning:** only run software you trust. The manual commands are available so you can inspect each action.

**Tomorrow:** use the public Google GA4 dataset via BigQuery Sandbox; today all charts use deliberately **synthetic** events.
