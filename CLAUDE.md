# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

This repository is **pre-implementation**. It currently contains only:
- `.llm/PDR.md` — the full product/requirements brief (in Portuguese)
- `README.md` — placeholder (`# bolao_copa`)
- `.claude/skills/` — Streamlit development and frontend design skills available for use

No application code, dependency manifests, Dockerfiles, or database schema exist yet. There are no build, lint, or test commands to run until the project scaffolding is created.

## What this project is

"Copa Insights" is a sports betting pool (bolão) and analytics web app for the 2026 World Cup. Registered users submit predictions (palpites) for match outcomes, scores are calculated automatically after official results are entered, and dashboards show rankings and statistics.

The full spec lives in `.llm/PDR.md` — read it before starting implementation work, since it defines the required architecture, data model, and deliverables in detail. Key points:

### Mandatory tech stack
- Python 3.12
- Streamlit (frontend)
- FastAPI (backend/API)
- PostgreSQL + SQLAlchemy ORM
- Alembic for migrations
- Passlib (bcrypt) for password hashing
- JWT for authentication
- Pandas for data processing, Plotly for dashboards
- Docker / docker-compose for containerization
- Deploy target: Render or Railway

### Architectural requirements
- Clear separation between frontend, backend, database, and service layers; modular structure; SOLID principles; full Python typing throughout.

### Domain modules
- **Users**: registration, login/logout, password recovery, profile, session control. Passwords stored only as bcrypt hashes.
- **Matches (jogos)**: teams, date/time, competition phase, official result, status (scheduled/in progress/finished).
- **Predictions (palpites)**: one prediction per user per match, locked once the match starts, with history and timestamps.
- **Scoring**: correct winner only = 1 point, exact score = 3 points, both wrong = 0 points. Ranking recalculates automatically whenever official results are updated.

### Roles
- **Administrador**: manage users and matches, enter official results, view all reports, plus a historical-correction area to retroactively register finished matches/results/predictions, recalculate the ranking, and view a change log of post-migration edits.
- **Participante**: submit predictions, view ranking, view dashboards.

### Dashboards required
General ranking, score evolution over time, accuracy percentage, prediction distribution per match, predicted win/draw/loss counts per participant, and overall pool statistics.

### Process note from the brief
Before writing code, the brief asks for the solution architecture, data model, ER diagram, component diagram, and directory structure to be presented for validation first — keep this in mind if picking up implementation from scratch.
