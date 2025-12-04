# Dune Discord Bot

A modular Discord bot written in Python that runs Dune Analytics queries on command and posts the results back into your server.

---

## Features

- **Slash commands** (e.g. `/dune`) to trigger predefined Dune Analytics queries  
- **Config-driven Dune mapping**: associate Discord commands with specific Dune query IDs  
- **Simple, extensible architecture** for adding:
  - New commands
  - New Dune queries
  - New output formats (tables, charts, summaries)
- **Environment-based configuration** using `.env`  
- **Pluggable services layer** (e.g. swap `discord.py` for another framework later if desired)

---

## Project Structure

```bash
dune-discord-bot/
├── bot/                           # Bot source code
│   ├── __init__.py
│   ├── client.py                  # Discord client / bot setup
│   ├── config.py                  # Centralized config & settings loader
│   ├── commands/                  # Bot commands (slash / prefix)
│   │   ├── __init__.py
│   │   └── dune_queries.py        # Commands that trigger Dune queries
│   ├── services/                  # External service integrations
│   │   ├── __init__.py
│   │   └── dune_client.py         # Thin wrapper around Dune HTTP API
│   ├── formatters/                # Helpers for formatting output
│   │   ├── __init__.py
│   │   └── discord_embeds.py      # Turn query results into Discord embeds/messages
│   └── utils/                     # Shared utilities
│       ├── __init__.py
│       └── logging.py             # Standardized logging setup
│
├── config/                        # Static and user-editable config files
│   ├── dune_queries.yaml          # Map commands → Dune query IDs & metadata
│   └── logging.yaml               # Optional logging configuration
│
├── scripts/
│   └── run_bot.py                 # Entry point to launch the bot
│
├── tests/                         # Tests for services and commands
│   ├── __init__.py
│   ├── test_dune_client.py
│   └── test_dune_commands.py
│
├── .env.example                   # Example environment variables
├── requirements.txt               # Python dependencies (discord.py, requests, etc.)
├── pyproject.toml                 # Optional: modern Python project config
├── README.md                      # You are here
└── LICENSE                        # Project license
```

---

## Tech Stack

- **Language:** Python 3.10+  
- **Discord library:** `discord.py` (or compatible fork)  
- **HTTP client:** `requests` or `httpx`  
- **Config:** `python-dotenv` + YAML  

---

## Getting Started

### 1. Prerequisites

- Python 3.10 or newer
- A Discord account and a server where you can add bots
- A **Discord Bot Token** (from the Discord Developer Portal)
- A **Dune API Key** (from Dune Analytics)

### 2. Clone the Repository

```bash
git clone https://github.com/your-username/dune-discord-bot.git
cd dune-discord-bot
```

### 3. Create and Activate a Virtual Environment (recommended)

```bash
python -m venv .venv
source .venv/bin/activate      # On Windows: .venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Copy the example file and edit it:

```bash
cp .env.example .env
```

Update `.env` with your credentials:

```dotenv
DISCORD_BOT_TOKEN=your-discord-bot-token-here
DISCORD_GUILD_ID=your-discord-server-id-optional

DUNE_API_KEY=your-dune-api-key-here
DUNE_DEFAULT_QUERY_ID=1234567
DUNE_API_BASE_URL=https://api.dune.com/api/v1
```

### 6. Configure Dune Commands

Edit `config/dune_queries.yaml` to map commands to query IDs:

```yaml
queries:
  tvl:
    id: 1234567
    description: "Show current TVL for the protocol"
    result_type: "table"

  volume_24h:
    id: 2345678
    description: "Show last 24h volume"
    result_type: "table"

  custom_example:
    id: 3456789
    description: "Some custom Dune query"
    result_type: "summary"
```

---

## Running the Bot

```bash
python -m scripts.run_bot
```

---

## Usage

- `/ping` — health check  
- `/dune tvl` — runs the mapped TVL query  
- `/dune volume_24h` — runs the 24h volume query  

---

## How It Works

1. User triggers `/dune <name>`
2. Command looks up `<name>` in YAML mapping
3. `dune_client.py` executes the query
4. Formatter builds Discord embed
5. Bot replies with formatted data

---

## Extensibility

### Add a new Dune query

Update `config/dune_queries.yaml` — no code changes required.

### Add a new command

Create a new file in `bot/commands/` and register it.

---

## Roadmap

- **Phase 1:** Core MVP  
- **Phase 2:** UX enhancements  
- **Phase 3:** Scheduling, plotting, multi-workspace support  

---

## License

MIT License (or your choice)
