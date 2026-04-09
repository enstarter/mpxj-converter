# Project File Converter — powered by MPXJ

A free, hosted web app to convert project files between any format supported by MPXJ.

## Supported input formats
MPP, MPX, MSPDI, XER, PMXML, Asta PP/PPX, GanttProject, P3, SureTrak,
Synchro, Planner, Phoenix, FastTrack, ConceptDraw, TurboProject, SDEF,
Deltek BK3, Edraw EDPX, ProjectLibre, Merlin, Schedule Grid, Project Commander

## Supported output formats
- MS Project XML (.xml)
- MPX (.mpx)
- Primavera XER (.xer)
- Primavera P6 XML / PMXML (.xml)
- SDEF (.sdef)
- Planner (.xml)

---

## Deploy to Railway (free, step by step)

### Step 1 — Create a GitHub account
Go to https://github.com and sign up (free).

### Step 2 — Upload these files to GitHub
1. Click the **+** button → **New repository**
2. Name it: `mpxj-converter`
3. Click **Create repository**
4. Click **uploading an existing file**
5. Upload ALL files from this folder:
   - `app.py`
   - `requirements.txt`
   - `Procfile`
   - `nixpacks.toml`
   - `templates/index.html` (create a `templates` folder first)
6. Click **Commit changes**

### Step 3 — Deploy on Railway
1. Go to https://railway.app and sign up with your GitHub account
2. Click **New Project**
3. Choose **Deploy from GitHub repo**
4. Select your `mpxj-converter` repo
5. Railway detects everything automatically — just click **Deploy**
6. Wait ~3 minutes for it to build
7. Click **Settings** → **Networking** → **Generate Domain**
8. Your app is live at the URL Railway gives you!

### That's it!
Share the URL with anyone — they can convert project files directly in their browser,
no software needed.

---

## Running locally (optional)

```bash
pip install mpxj flask gunicorn
python app.py
```
Then open http://localhost:5000 in your browser.
