<div align="center">

# 📍 CIVIC TRACE

### Snap it. We'll chase it.

**An AI agent that files civic complaints for you, and keeps following up until they're actually fixed.**

`Track 1 · Make MCP Matter` · Built by **Team Pablos** · Sapthagiri NPS University

[🎥 Demo Video](YOUTUBE_LINK_HERE) · [📊 Pitch Deck](DRIVE_LINK_HERE)

</div>

---

## 🚧 The problem

You see a pothole, an overflowing garbage bin or a broken streetlight. You report it. Then nothing happens.

- **Who handles this?** Roads, water, power and garbage are separate departments, so people guess and wrong guesses get dropped.
- **Portals are a maze.** Logins, long forms and a different website for every city.
- **Nobody follows up.** Once filed, complaints go silent. There are no reminders, no escalation and no record of who ignored them.

Filing a complaint takes five minutes. Getting it fixed takes persistence nobody has time for. **CIVIC TRACE is that persistence, automated.**

---

## ✨ What it does

| Step | What happens |
|---|---|
| 📸 **Snap** | Send a photo, voice note or text. Location is captured automatically. |
| 🧠 **Understand** | A vision model identifies the issue, rates its severity and finds the responsible department. |
| ✉️ **File** | The agent drafts a formal complaint and submits it **only after you approve it**. |
| 🔁 **Trace** | It tracks the reference number, sends reminders and escalates if the complaint is ignored. |

### What makes it different

- **🔗 Duplicate merging.** When 30 people report the same pothole, their reports are clustered (DBSCAN on location and issue type, plus photo similarity) into **one strong complaint** that shows the full count.
- **📊 Accountability board.** A live map of hotspots and a report card for each ward or department (average fix time, ignored complaints, escalations).
- **🛑 Human in control.** Nothing is sent in your name without explicit approval through the `ask_user_approval` tool.

---

## 🏗️ Architecture

```
 Citizen (Web / Telegram)
          │
          ▼
   AI Agent (LLM) ──── plans and calls tools ────┐
                                                 ▼
                         ┌──────── CIVIC TRACE MCP Server ────────┐
                         │ classify_issue     find_authority      │
                         │ check_duplicates   draft_complaint     │
                         │ ask_user_approval  file_complaint      │
                         │ track_status       escalate            │
                         └───────────────┬────────────────────────┘
                                         ▼
        Department email · Complaint portal (Playwright) · Maps · SQLite
```

### MCP tools

| Tool | Purpose |
|---|---|
| `classify_issue` | Reads the photo or text and returns the issue type, severity and a short description |
| `find_authority` | Maps the issue type and location to the responsible department and contact |
| `check_duplicates` | Finds existing reports of the same problem nearby and merges them |
| `draft_complaint` | Writes a formal complaint with photos, location and the report count |
| `ask_user_approval` | Shows the draft to the citizen and waits for approval |
| `file_complaint` | Submits by official email or fills in the complaint portal with Playwright |
| `track_status` | Stores the reference number and checks progress |
| `escalate` | Sends reminders and escalates to a senior officer after a deadline |

> **Note:** most civic portals have no public API, so complaints are filed by official email and by browser automation.

---

## 🛠️ Tech stack

| Layer | Tools |
|---|---|
| Agent | Claude / Gemini LLM, MCP Python SDK |
| Backend | FastAPI, SQLite (PostgreSQL + PostGIS for scale) |
| Vision | Multimodal LLM (no custom training) |
| Data science | scikit-learn (DBSCAN with haversine distance), pandas |
| Automation | Playwright, SMTP |
| Client | Any MCP client (e.g. Claude Desktop); dashboard with Leaflet maps |

---

## 📁 Project structure

```
civic-trace/
├── mcp_server/
│   ├── server.py        # MCP server with all 8 tools
│   └── db.py            # SQLite storage
├── analytics/
│   ├── duplicates.py    # DBSCAN duplicate clustering
│   └── ward_scores.py   # Ward accountability scores
├── automation/
│   ├── emailer.py       # Files complaints by email (dry-run by default)
│   └── portal_filer.py  # Fills the complaint portal with Playwright
├── backend/
│   └── main.py          # FastAPI: serves the dashboard and its data
├── dashboard/
│   └── index.html       # Live map, ward report card and complaint feed
├── scripts/
│   └── seed_demo.py     # Loads realistic demo complaints
├── demo_portal/
│   └── index.html       # Demo copy of a city grievance portal
├── data/
│   └── authorities.csv  # Department and contact directory (sample)
├── requirements.txt
└── .env.example
```

---

## 🚀 Getting started

### Prerequisites
- Python 3.10+
- An Anthropic API key (for photo classification)

### Setup

```bash
git clone https://github.com/swayamsrathod/civic-traces.git
cd civic-traces

python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium

cp .env.example .env              # then add your API key
```

### Run

```bash
# 1. The MCP server (connect it to Claude Desktop or any MCP client)
python -m mcp_server.server

# 2. The demo complaint portal (for portal filing)
python -m http.server 8080 --directory demo_portal

# 3. The dashboard (open http://localhost:8000)
uvicorn backend.main:app --reload
```

### Load demo data

To fill the dashboard with realistic sample complaints around Bengaluru:

```bash
python -m scripts.seed_demo --reset
```

The dashboard refreshes every 5 seconds, so a complaint filed through the agent appears on the map live.

### Connect to Claude Desktop

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "civic-trace": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/full/path/to/civic-traces"
    }
  }
}
```

Then try: *"Here's a photo of a pothole near Gate 2 of our college. Please report it."*

> Emails are **not sent** while `DRY_RUN=true` (the default). They're printed to the console instead. The addresses in `data/authorities.csv` are samples. Replace them with your city's real department contacts before going live.

---

## 📸 Screenshots

_Screenshots coming soon. Add them to the `docs/` folder._

---|---|---|
| ![Report](docs/report.png) | ![Draft](docs/draft.png) | ![Map](docs/map.png) |

---

## 🗺️ Roadmap

- [x] Photo → classify → draft → approve → file
- [x] Duplicate merging, follow-ups and escalation
- [x] Live accountability dashboard: hotspot map, ward report card, complaint feed
- [ ] Voice notes in regional languages
- [ ] WhatsApp support
- [ ] Auto-draft an RTI request when a complaint is ignored
- [ ] Open data export for city planners

---

## 👥 Team Pablos

Sapthagiri NPS University

- Swayam S Rathod
- Trishul G Urs
- Neeraj M
- Yashas Gowda

---|---|
| [Member 1] | MCP server and agent |
| [Member 2] | Data science and analytics |
| [Member 3] | Automation and backend |
| [Member 4] | Frontend and design |

---

<div align="center">

**Every complaint, traced.**

</div>
