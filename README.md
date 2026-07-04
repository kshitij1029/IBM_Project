# ✈ Voyager — AI-Powered Travel Planner Agent

> An intelligent travel planning web application powered by **IBM Watsonx.ai Granite models**,
> built with **Python Flask** and a modern **Bootstrap 5** frontend.

---

## 🚀 Features

| Feature | Description |
|---|---|
| 🤖 **AI Chat Assistant** | Conversational travel planning with full session memory |
| 🗓 **Itinerary Generator** | Day-by-day AI travel plans with morning/afternoon/evening slots |
| 🌍 **Destination Explorer** | AI recommendations + 12 curated destinations with details |
| 💰 **Budget Planner** | Instant estimates + AI narrative breakdown + expense tracker |
| 🎒 **Packing Checklist** | AI-generated packing lists by destination, season & activities |
| 📄 **PDF Export** | Download full itinerary as a formatted PDF (via ReportLab) |
| 👨‍👩‍👧 **Family Trip Planner** | Child-friendly itineraries with age-specific activity recommendations |
| 💾 **Save Trips** | Session-based trip storage with favorites & countdown timers |
| 🌤 **Weather Info** | OpenWeatherMap integration with AI fallback |
| 🌙 **Dark/Light Mode** | Persistent theme toggle with system-level CSS variables |
| 📱 **Fully Responsive** | Mobile-first design with collapsible sidebar |

---

## 📁 Project Structure

```
travel_agent/
├── app.py                      ← Flask app entry point
├── requirements.txt
├── .env.example                ← Copy to .env and fill in credentials
│
├── config/
│   ├── __init__.py
│   └── settings.py             ← All config from environment variables
│
├── prompts/
│   ├── __init__.py
│   └── agent_instructions.py   ← ★ AGENT CUSTOMIZATION HUB ★
│
├── services/
│   ├── __init__.py
│   ├── watsonx_service.py      ← All IBM Watsonx.ai calls
│   ├── weather_service.py      ← OpenWeatherMap integration
│   └── budget_service.py       ← Client-side budget calculations
│
├── routes/
│   ├── __init__.py
│   ├── main.py                 ← Dashboard, profile, saved trips
│   ├── chat.py                 ← AI chat endpoint
│   ├── planner.py              ← Itinerary, tips, packing, PDF
│   ├── destinations.py         ← Recommendations, weather info
│   └── budget.py               ← Budget estimation
│
├── models/
│   ├── __init__.py
│   ├── trip.py                 ← Trip, BudgetBreakdown dataclasses
│   └── user_profile.py         ← UserProfile, ConversationTurn
│
├── utils/
│   ├── __init__.py
│   ├── helpers.py              ← Utility functions
│   └── pdf_export.py           ← ReportLab PDF generation
│
├── templates/
│   ├── base.html               ← Shared layout (sidebar, topbar, footer)
│   ├── index.html              ← Dashboard with hero & quick actions
│   ├── chat.html               ← AI chat interface
│   ├── planner.html            ← Trip planner form + results
│   ├── destinations.html       ← Destination cards + AI recommendations
│   ├── budget.html             ← Budget estimator + expense tracker
│   ├── saved_trips.html        ← Saved trips management
│   └── profile.html            ← User profile & emergency info
│
└── static/
    ├── css/style.css           ← Full design system (glassmorphism, dark mode)
    └── js/
        ├── main.js             ← Dark mode, sidebar, toasts, AI text formatter
        ├── chat.js             ← Chat interface
        ├── planner.js          ← Planner page
        └── budget.js           ← Budget charts & expense tracker
```

---

## ⚙️ Setup Instructions

### 1. Clone / Navigate to the project

```bash
cd travel_agent
```

### 2. Create a virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
IBM_API_KEY=your_ibm_cloud_api_key
WATSONX_PROJECT_ID=your_project_id
WATSONX_URL=https://us-south.ml.cloud.ibm.com
WATSONX_MODEL_ID=ibm/granite-13b-instruct-v2
SECRET_KEY=your-strong-random-key
OPENWEATHER_API_KEY=optional_for_live_weather
```

### 5. Run the application

```bash
python app.py
```

Open [http://localhost:5000](http://localhost:5000)

---

## 🔑 IBM Watsonx.ai Setup

1. Log in to [IBM Cloud](https://cloud.ibm.com)
2. Create a **Watsonx.ai** service instance
3. Go to **Manage → Access (IAM)** → Create an API Key
4. Copy the API Key and paste into `.env` as `IBM_API_KEY`
5. Open Watsonx.ai, create a project and copy the **Project ID**
6. Choose a Granite model ID (e.g. `ibm/granite-13b-instruct-v2`)

---

## 🎨 Agent Customization

All agent behavior is controlled from **one file**:

```
prompts/agent_instructions.py
```

Editable sections:

| Section | What you can change |
|---|---|
| `AGENT_NAME` | Name displayed in the UI |
| `AGENT_PERSONALITY` | Tone, backstory, expertise description |
| `AGENT_TONE` | Communication style rules |
| `TRAVEL_SPECIALIZATIONS` | List of travel niches the agent covers |
| `SAFETY_RULES` | Travel advisory and safety guardrails |
| `BUDGET_STRATEGY` | How the agent approaches cost optimization |
| `REGIONAL_EXPERTISE` | Which geographic regions the agent knows best |
| `RECOMMENDATION_STYLE` | How suggestions are presented and structured |

No changes required to routes, services, or templates.

---

## 🚢 Production Deployment

### Local Production

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### IBM Cloud Code Engine

```bash
# Build container
docker build -t voyager-travel-agent .
# Push to IBM Container Registry
ibmcloud cr push us.icr.io/<namespace>/voyager-travel-agent
# Deploy to Code Engine
ibmcloud ce app create --name voyager --image us.icr.io/<namespace>/voyager-travel-agent --port 5000
```

### Environment variables on IBM Cloud

Set via Code Engine → Application → Environment variables, mirroring all keys from `.env.example`.

---

## 📦 Key Dependencies

| Package | Purpose |
|---|---|
| `Flask` | Web framework |
| `Flask-Session` | Server-side session storage |
| `ibm-watsonx-ai` | IBM Granite model integration |
| `python-dotenv` | `.env` file loading |
| `reportlab` | PDF itinerary export |
| `requests` | OpenWeatherMap API calls |
| `gunicorn` | Production WSGI server |

---

## 🛡 Security Notes

- API keys are read from environment variables — never hardcoded
- Sessions use server-side filesystem storage with signed cookies
- All user inputs are sanitized with length limits before AI processing
- No financial data (card numbers, bank details) is ever requested or stored

---

*Made with ❤️ using IBM Watsonx.ai Granite models*
