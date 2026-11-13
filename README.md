# Voyager — AI-Powered Travel Planner

Voyager is an AI-assisted travel planning web application built with **Python, Flask, Bootstrap 5, and IBM watsonx.ai**.

## Features

- AI travel chat and day-by-day itinerary generation
- Destination discovery and recommendations
- Budget estimates and expense planning
- Packing and family-trip planning
- Itinerary PDF export
- Session-based saved trips and user profiles
- Weather integration and responsive dark/light UI

## Project structure

```text
IBM_Project/
├── backend/
│   ├── app.py                 # Flask application factory and entry point
│   ├── config/                # Environment-based application settings
│   ├── models/                # Trip and user-profile models
│   ├── prompts/               # watsonx.ai agent instructions
│   ├── routes/                # Flask blueprints and API endpoints
│   ├── services/              # watsonx.ai, weather and budget services
│   ├── utils/                 # Helpers and PDF export
│   ├── tests/                 # Backend tests
│   └── scripts/               # Developer utilities
├── frontend/
│   ├── templates/             # Jinja HTML templates
│   └── static/                # CSS and JavaScript assets
├── app.py                     # Backwards-compatible root launcher
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Getting started

### 1. Create and activate a virtual environment

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy `.env.example` to `.env` and add your own credentials:

```bash
# Windows PowerShell
Copy-Item .env.example .env
# macOS/Linux
cp .env.example .env
```

### 4. Run locally

From the repository root:

```bash
python app.py
```

Open http://localhost:5000.

### Production

The root launcher remains compatible with Gunicorn:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Developer utility

To list IBM watsonx.ai projects associated with your IBM account:

```bash
python backend/scripts/find_project_id.py
```

The utility reads credentials from the root `.env` file and does not print the API key.

## Tests

Run from the repository root:

```bash
python -m unittest discover -s backend/tests -v
```

## Technology

- **Backend:** Python, Flask, Flask-Session
- **AI:** IBM watsonx.ai
- **Frontend:** Jinja, Bootstrap 5, CSS, JavaScript
- **PDF:** ReportLab
- **Deployment:** Gunicorn

## Security

- Keep real credentials in the local `.env` file or deployment environment variables.
- Never commit `.env`, session files, local databases, caches or generated output.
- Use a strong, unique Flask `SECRET_KEY` in deployment.
