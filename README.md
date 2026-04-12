# Recreating the AadhaarTrust Project Structure

This guide outlines the exact, step-by-step instructions needed to recreate the AadhaarTrust project structure from scratch. Follow this process if you are re-initializing the repository locally, setting up a fresh environment, or transferring the architecture to a new machine.

---

## 1. Root Project Initialization

First, create the main project folder and navigate into it:

```bash
mkdir Aadhaar_Trust_v1
cd Aadhaar_Trust_v1
```

Set up your root Python virtual environment (vital for separating global vs. project Python packages):

```bash
python -m venv venv

# Activate on Windows:
venv\Scripts\activate

# Activate on Linux/macOS:
source venv/bin/activate
```

Next, add your main dependency tracking files and entry points:
```bash
# On Windows
type nul > requirements.txt
type nul > requirements-dev.txt
type nul > requirements-optional.txt
type nul > main.py
type nul > aadhaar_trust.py
type nul > .gitignore
```
*(Note: If using Linux/macOS, substitute `type nul >` with `touch`)*

---

## 2. Core Python / ML Pipeline Setup

Create the primary directories intended for the Machine Learning inference, business logic, configuration, and data processing.

```bash
# Core logic and configuration
mkdir src config pipeline models notebooks logs

# Data and temporary processing buffers
mkdir data data\output data\input 
mkdir temp_input temp_output temp_processing output_new extracted_qr_raw debug_qr
```

Inside the `src/` folder, create the explicit module directories based on the application's computer vision and ML aspects:

```bash
mkdir src\forgery_detection src\noiseprint_creation src\qr_decrpytion
```

Make them recognizable as standard Python packages by adding `__init__.py` module descriptors:
```bash
type nul > src\__init__.py
type nul > src\forgery_detection\__init__.py
type nul > src\noiseprint_creation\__init__.py
type nul > src\qr_decrpytion\__init__.py
type nul > config\__init__.py
type nul > pipeline\__init__.py
```

---

## 3. Backend Implementation (FastAPI)

Now, initialize the Fast-API backend segment that wraps the ML pipeline logic inside a REST architectural style.

```bash
mkdir backend-api
cd backend-api

# Construct the core app structure
mkdir app app\api app\api\v1 app\core app\models app\services

# Add FastAPI configuration files
type nul > app\__init__.py
type nul > app\main.py
type nul > requirements.txt

# Return to root
cd ..
```
*(`backend-api/app/main.py` is the Uvicorn runtime entry point)*

---

## 4. Frontend Implementation (React + Vite + TailwindCSS)

Your frontend is a responsive Single Page Application bootstrapped with Vite, utilizing React 18 and Typescript.

```bash
# Scaffold the fundamental Vite TS-React structure (named 'frontend')
npm create vite@latest frontend -- --template react-ts

# Step into the generated folder
cd frontend

# Install default packages
npm install

# Install Tailwind CSS and associated peer-dependencies
npm install -D tailwindcss postcss autoprefixer

# Auto-generate the tailwind.config.js and postcss.config.js configurations
npx tailwindcss init -p
```

### Tailwind Configuration Details:

Navigate inside the frontend code and modify `tailwind.config.js` to parse your React components:

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

To complete styling setup, import Tailwind directives heavily into your `src/index.css`:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

Return to the main directory once complete:
```bash
cd ..
```

---

## 5. Standard Documentation & References

Finally, provision placeholder files for documentation (which is identical to what is populated today):

```bash
type nul > PROJECT_SUMMARY.md
type nul > QUICK_START.md
type nul > INSTALLATION.md
type nul > BUGFIXES.md
type nul > PATH_FIXES.md
type nul > Aadhaar\ Workflow.md
```

---

## Resulting Directory Scaffold

After completing the steps above, you will end up with this exact hierarchical map — fully replicating the AadhaarTrust workspace layout:

```text
Aadhaar_Trust_v1/
├── backend-api/          # FastAPI REST endpoints & wrappers
│   ├── app/
│   │   ├── api/          # Route handlers
│   │   ├── core/         # Configs (CORS, Application states)
│   │   ├── models/       # Pydantic schemas for data validation
│   │   ├── services/     # Business logic & Pipeline integrations
│   │   └── main.py       # Uvicorn FastAPI entrypoint
│   └── requirements.txt
├── frontend/             # Single-Page UI (React 18, TS, Vite, Tailwind)
│   ├── src/
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.ts
├── src/                  # Existing ML and Computer Vision Modules
│   ├── forgery_detection/
│   ├── noiseprint_creation/
│   └── qr_decrpytion/
├── pipeline/             # Primary Orchestrator invoking SRC modules
├── config/               # Application & Hardware configuration templates
├── models/               # Storage for Neural Network weights (e.g., .pt)
├── data/                 # Sample IO structures and testing fixtures
├── temp_*/               # Ephemeral storage during processing workflows
├── notebooks/            # Jupyter notebooks for sandbox exploration
├── logs/                 # Global application logs repository
├── requirements.txt      # Root AI Dependencies
├── main.py               # Alternative Pipeline trigger scripts
└── README.md             # This guide!
```

**Next Steps**: After re-constructing the filesystem, you can copy script definitions from your version control backup and execute `npm install` and `pip install -r requirements.txt` again to download actual code module dependencies.
