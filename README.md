# Teaching-Content-DB

A lightweight web app for storing, searching, and auto-categorising teaching materials (lesson plans, worksheets, assessments, etc.).  
It includes:

* **Backend** – Flask + SQLite  
* **Frontend** – Vanilla HTML/CSS/JS  
* **Smart auto-categorisation** – Optional local LLM (via Ollama) analyses uploads and suggests subject, content-type, grade level, difficulty and tags.

---

## 1. Quick Start (default / no LLM)

```bash
# clone your repo
git clone https://github.com/<you>/teaching-content-db.git
cd teaching-content-db

# create & activate virtual env  (Windows example)
python -m venv venv
venv\Scripts\activate

# install dependencies
pip install -r requirements.txt

# start the server
python start_server.py
```

* Open **http://127.0.0.1:5000** in your browser.  
* Upload files or paste text, fill the form, and save.  
* Search / filter by tags, subject or grade.

---

## 2. Optional – Enable Local LLM Auto-Categorisation

1. Install **[Ollama](https://ollama.ai/)** and run `ollama serve`.
2. Pull the model used by the analyser (e.g. `ollama pull qwen2.5:7b`).
3. Restart `start_server.py`.  
   You’ll now get automatic suggestions when you upload or drop files.

If Ollama isn’t running, the app falls back to keyword analysis.

---

## 3. Folder Structure (important parts)
backend/ Flask API, DB models, LLM analyser
frontend/ Static HTML/CSS/JS
uploads/ Saved user files
logs/ Runtime logs
docs/ Design & integration reports

---

## 4. Environment variables (optional)

| Variable                | Purpose                               | Default                  |
|-------------------------|---------------------------------------|--------------------------|
| `UPLOAD_FOLDER`         | Where files are stored                | `uploads/`               |
| `MAX_CONTENT_LENGTH`    | Max upload size (bytes)               | `16 * 1024 * 1024`       |
| `OLLAMA_MODEL`          | LLM model name for auto-processing    | `qwen2.5:7b`             |

---

## 5. Development Tips

* **Backend**: edit code in `backend/`, hot-reload by restarting `start_server.py`.
* **Frontend**: static files live in `frontend/`; reload browser to see changes.
* **Logs**: check `logs/teaching-content-db*.log` for errors or performance data.
* **Tests**: simplest test is uploading a small PDF or text file and confirming it appears in the dashboard.

---

## 6. License

MIT
