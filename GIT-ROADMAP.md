# Development Roadmap – Dune Discord Bot

## Branch Naming Convention

- Feature branches: `feature/<nn>-<short-name>`
- Bugfix branches: `fix/<short-name>`
- Docs branches: `docs/<short-name>`

Example: `feature/01-project-scaffold`

Each feature branch should be merged into `main` via PR after review.

---

# Phase Overview

1. Repo & Scaffolding  
2. Configuration & Logging  
3. Dune Client  
4. Discord Bot Core  
5. Dune Command Integration  
6. Formatting & UX  
7. Tests & CI  
8. Docs & Examples  
9. Quality-of-Life Improvements  

---

# 1. `feature/01-project-scaffold`

### Goal
Establish the base repository structure and minimal setup.

### Commits
1. `chore: initialize project structure`  
2. `chore: add README placeholder and LICENSE`  
3. `chore: add .gitignore for python and venv`  
4. `chore: add requirements.txt and pyproject.toml skeleton`  

---

# 2. `feature/02-config-and-env`

### Goal
Introduce configuration loading and environment management.

### Commits
1. `chore: add python-dotenv and pyyaml`  
2. `feat: add .env.example`  
3. `feat: implement config loader (Settings dataclass)`  
4. `chore: add placeholder dune_queries.yaml`  
5. `test: add basic config loading tests`  

---

# 3. `feature/03-logging-infrastructure`

### Goal
Provide standardized logging setup.

### Commits
1. `chore: add logging.yaml`  
2. `feat: add logging utility module`  
3. `chore: wire logging setup into run_bot.py`  
4. `test: add logging setup smoke test`  

---

# 4. `feature/04-dune-client-mvp`

### Goal
Create a minimal but functional Dune API client.

### Commits
1. `chore: add httpx dependency`  
2. `feat: add DuneClient skeleton`  
3. `feat: implement execute_query()`  
4. `feat: implement get_results()`  
5. `feat: add run_query_and_wait()`  
6. `test: add mocked DuneClient tests`  
7. `chore: add TODO markers for real endpoint wiring`  

---

# 5. `feature/05-discord-bot-bootstrap`

### Goal
Create the basic Discord bot with a working `/ping`.

### Commits
1. `chore: add discord.py dependency`  
2. `feat: add client.py with Discord bot setup`  
3. `feat: add /ping command`  
4. `chore: update run_bot.py to launch bot`  
5. `test: add basic ping command test`  

---

# 6. `feature/06-dune-command-handler`

### Goal
Implement generic `/dune <query>` command.

### Commits
1. `feat: add dune_queries command module`  
2. `feat: implement lookup from dune_queries.yaml`  
3. `feat: integrate DuneClient into command handler`  
4. `feat: add graceful handling of unknown queries`  
5. `feat: add /dune help command`  
6. `test: add dune command mapping tests`  

---

# 7. `feature/07-configurable-dune-queries`

### Goal
Allow user-defined mappings without modifying Python code.

### Commits
1. `chore: expand dune_queries.yaml with examples`  
2. `feat: support optional params in YAML config`  
3. `feat: add config validation on startup`  
4. `test: add config validation tests`  

---

# 8. `feature/08-discord-embeds-and-formatting`

### Goal
Add pretty embeds for tables and summaries.

### Commits
1. `feat: add discord_embeds formatter`  
2. `feat: implement basic table formatting`  
3. `feat: integrate formatter into /dune command`  
4. `feat: add error embeds`  
5. `test: add embed formatting tests`  

---

# 9. `feature/09-bot-lifecycle-and-error-handling`

### Goal
Improve bot robustness & error messaging.

### Commits
1. `feat: add startup/shutdown logs`  
2. `feat: add global command error handler`  
3. `feat: add optional rate limits`  
4. `test: add error handling tests`  

---

# 10. `feature/10-tests-and-ci-pipeline`

### Goal
Set up automated CI testing.

### Commits
1. `chore: add pytest configuration`  
2. `chore: add GitHub Actions CI workflow`  
3. `test: add coverage config`  
4. `docs: update README with testing instructions`  

---

# 11. `feature/11-docs-and-examples`

### Goal
Improve documentation.

### Commits
1. `docs: expand README with full setup instructions`  
2. `docs: add dune_queries.example.yaml`  
3. `docs: add CONTRIBUTING.md`  
4. `docs: add roadmap.md`  

---

# 12. `feature/12-quality-of-life-improvements`

### Goal
Add optional polish and UX improvements.

### Commits
1. `feat: add autocomplete for /dune query names`  
2. `feat: add /dune list`  
3. `feat: prepare structure for per-guild config overrides`  
4. `docs: update README with UX improvements`  

