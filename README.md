# Dune Discord Bot

A modular Discord bot written in Python that runs Dune Analytics queries on command and posts the results back into your server.

---

## Features

- **Per-row embeds** — Each row from query results is displayed in a separate embed for better readability
- **Rate limit protection** — Configurable delay between embeds to avoid Discord rate limits
- **Scheduled execution** — Automatically execute queries every 24 hours at a specified time
- **24h ALCX summary** — Optional summary embed showing total USD bought/sold after scheduled query
- **Slash commands** (`/ping`, `/status`) for health checks and status monitoring
- **Beautiful embeds** with formatted field output (Block Time, ALCX Bought/Sold, Amount USD, Txn link)
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

**Basic Configuration:**
```dotenv
DISCORD_BOT_TOKEN=your-discord-bot-token-here
DISCORD_GUILD_ID=your-server-id-for-fast-sync  # Optional
DUNE_API_KEY=your-dune-api-key-here
EMBED_DELAY_SECONDS=10  # Optional: Delay between embeds (default: 10)
```

**Scheduled Execution (Optional):**
```dotenv
SCHEDULED_QUERY_ID=1234567  # Query ID to execute automatically
SCHEDULED_EXECUTION_TIME=14:30  # Local time in HH:MM format (24-hour)
DISCORD_CHANNEL_ID=999999999999999999  # Channel to post results to
ALCX_SUMS_QUERY_ID=7654321  # Optional: 24h totals query (alcx_bought_usd, alcx_sold_usd)
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
| `/status` | Bot status — shows uptime, scheduled query info, and next execution time |

### Scheduled Execution

When configured with scheduled execution settings, the bot will:
- Automatically execute a configured query every 24 hours at a specified time
- Post results to a specified Discord channel
- Each result row is displayed as a separate embed with: Block Time, ALCX Bought/Sold (conditional), Amount USD, and a clickable transaction link
- Use `/status` to check when the next execution will occur

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
│   │   └── dune_queries.py        # Query command handlers
│   ├── services/
│   │   ├── __init__.py
│   │   ├── dune_client.py         # Dune SDK wrapper
│   │   └── scheduler.py           # Scheduled query runner
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
├── tests/                         # Test suite (118 tests)
│   ├── test_config.py
│   ├── test_dune_client.py
│   ├── test_formatters.py
│   ├── test_logging.py
│   └── test_scheduler.py
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
| `EMBED_DELAY_SECONDS` | No | Delay in seconds between sending embeds (default: 10) |
| `SCHEDULED_QUERY_ID` | No* | Query ID to execute automatically (required for scheduled mode) |
| `SCHEDULED_EXECUTION_TIME` | No* | Local time in HH:MM format (24-hour, e.g., "14:30") (required for scheduled mode) |
| `DISCORD_CHANNEL_ID` | No* | Discord channel ID to post scheduled results to (required for scheduled mode) |
| `ALCX_SUMS_QUERY_ID` | No | Query ID for 24h ALCX buy/sell totals (displayed after scheduled embeds) |

\* Required only if using scheduled execution mode

### Optional: Query Name Mapping

You can create friendly aliases for queries in `config/dune_queries.yaml`:

```yaml
queries:
  tvl:
    id: 1234567
    description: "Show current TVL"
    result_type: "table"
```

*(Future feature: query name aliases)*

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

### Scheduled Query Execution

1. Bot starts and reads scheduled configuration from `.env`
2. Scheduler calculates next execution time based on `SCHEDULED_EXECUTION_TIME`
3. Bot waits until execution time
4. At scheduled time, bot executes the query automatically
5. Results are formatted into multiple Discord embeds (one per row)
6. Each embed displays: Block Time, ALCX Bought/Sold (conditional), Amount USD, and Txn link
7. Embeds are posted to the configured Discord channel with delay between each
8. If `ALCX_SUMS_QUERY_ID` is configured, executes the sums query and displays 24h totals (ALCX Bought USD, ALCX Sold USD)
9. Process repeats every 24 hours

---

## Roadmap

- [x] **Phase 1:** Core MVP — Dune query execution
- [x] **Phase 2:** Per-row embeds with rate limiting
- [x] **Phase 3:** Scheduled query execution
- [ ] **Phase 4:** UX enhancements — autocomplete, query parameters

---

## License

MIT License — see [LICENSE](LICENSE) for details.
