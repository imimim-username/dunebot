# Dune Discord Bot

A modular Discord bot written in Python that runs Dune Analytics queries on command and posts the results back into your server.

---

## Features

- **Slash commands** (`/dune`, `/dune_latest`, `/ping`) to interact with Dune Analytics
- **Direct query execution** by query ID — no configuration needed
- **Beautiful embeds** with formatted table output and automatic truncation
- **Async execution** with Discord's "thinking..." indicator for long-running queries
- **Environment-based configuration** using `.env`
- **Extensible architecture** for adding new commands and output formats

---

## Quick Start

### 1. Prerequisites

- Python 3.10 or newer
- A Discord Bot Token ([Discord Developer Portal](https://discord.com/developers/applications))
- A Dune API Key ([Dune Settings](https://dune.com/settings/api))

### 2. Clone and Install

```bash
git clone https://github.com/your-username/dune-discord-bot.git
cd dune-discord-bot

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```dotenv
DISCORD_BOT_TOKEN=your-discord-bot-token-here
DISCORD_GUILD_ID=your-server-id-for-fast-sync  # Optional
DUNE_API_KEY=your-dune-api-key-here
```

### 4. Run the Bot

```bash
python -m scripts.run_bot
```

---

## Commands

| Command | Description |
|---------|-------------|
| `/ping` | Health check — shows bot latency |
| `/dune <query_id>` | Execute a Dune query and display results |
| `/dune_latest <query_id>` | Get cached results without re-executing |

### Example Usage

```
/dune query_id:1234567
```

The bot will:
1. Show "thinking..." while the query executes
2. Display results in a formatted table embed
3. Handle errors gracefully with user-friendly messages

---

## Project Structure

```
dune-discord-bot/
├── bot/                           # Bot source code
│   ├── __init__.py
│   ├── client.py                  # Discord client / bot setup
│   ├── config.py                  # Settings loader (env + YAML)
│   ├── commands/
│   │   ├── __init__.py
│   │   └── dune_queries.py        # /dune command handlers
│   ├── services/
│   │   ├── __init__.py
│   │   └── dune_client.py         # Dune SDK wrapper
│   ├── formatters/
│   │   ├── __init__.py
│   │   └── discord_embeds.py      # Result → Discord embed formatting
│   └── utils/
│       ├── __init__.py
│       └── logging.py             # Logging setup
│
├── config/
│   ├── dune_queries.yaml          # Optional: query name → ID mapping
│   └── logging.yaml               # Logging configuration
│
├── scripts/
│   └── run_bot.py                 # Entry point
│
├── tests/                         # Test suite (58 tests)
│   ├── test_config.py
│   ├── test_dune_client.py
│   ├── test_formatters.py
│   └── test_logging.py
│
├── .env.example                   # Environment template
├── requirements.txt               # Python dependencies
├── pyproject.toml                 # Project metadata
└── README.md
```

---

## Tech Stack

- **Language:** Python 3.10+
- **Discord:** [discord.py](https://discordpy.readthedocs.io/) 2.3+
- **Dune:** [dune-client](https://docs.dune.com/api-reference/sdks/python) SDK
- **Config:** python-dotenv + PyYAML

---

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DISCORD_BOT_TOKEN` | Yes | Your Discord bot token |
| `DISCORD_GUILD_ID` | No | Server ID for faster command sync during development |
| `DUNE_API_KEY` | Yes | Your Dune Analytics API key |

### Optional: Query Name Mapping

You can create friendly aliases for queries in `config/dune_queries.yaml`:

```yaml
queries:
  tvl:
    id: 1234567
    description: "Show current TVL"
    result_type: "table"
```

*(Future feature: `/dune tvl` command support)*

---

## Development

### Running Tests

```bash
# Activate virtual environment
source .venv/bin/activate

# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=bot --cov-report=html
```

### Project Setup with uv (Alternative)

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create venv and install
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

---

## How It Works

1. User runs `/dune 1234567`
2. Bot defers response (shows "thinking...")
3. `DuneClient` executes query via official SDK
4. Results formatted into Discord embed with table layout
5. Large results automatically truncated to fit Discord limits
6. Bot sends formatted embed response

---

## Roadmap

- [x] **Phase 1:** Core MVP — `/dune <query_id>` execution
- [ ] **Phase 2:** UX enhancements — autocomplete, `/dune list`
- [ ] **Phase 3:** Advanced features — scheduling, charts, parameters

---

## License

MIT License — see [LICENSE](LICENSE) for details.
