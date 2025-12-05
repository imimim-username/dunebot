# Discord Bot Setup Guide

This guide walks you through setting up a Discord bot application and configuring it to work with the Dune Discord Bot.

---

## Prerequisites

- A Discord account
- Access to the [Discord Developer Portal](https://discord.com/developers/applications)
- A Discord server where you can invite bots (you need "Manage Server" permissions)

---

## Step 1: Create a Discord Application

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **"New Application"** (top right)
3. Give it a name (e.g., "Dune Bot") and click **"Create"**

---

## Step 2: Get Your Bot Token

1. In your application, go to the **"Bot"** tab (left sidebar)
2. Click **"Add Bot"** if you haven't created a bot yet
3. Under **"Token"**, click **"Reset Token"** or **"Copy"**
   - ⚠️ **IMPORTANT**: Keep this token secret! Never commit it to version control.
   - If you accidentally share it, click "Reset Token" immediately
4. Copy the token and save it temporarily (you'll need it for Step 8)

---

## Step 3: Configure Bot Settings

Still in the **"Bot"** tab:

1. **Username**: Customize the bot's display name (optional)
2. **Icon**: Upload a bot icon (optional)
3. **Public Bot**: Leave this **disabled** for private use
4. **Message Content Intent**: Not needed (we use slash commands)
5. **Privileged Gateway Intents**: None required for this bot

---

## Step 4: Set Up Bot Permissions

1. Go to the **"OAuth2"** → **"URL Generator"** tab
2. Under **"Scopes"**, select:
   - ✅ `bot`
   - ✅ `applications.commands`
3. Under **"Bot Permissions"**, select:
   - ✅ `Send Messages`
   - ✅ `Use Slash Commands`
   - ✅ `Embed Links`
   - ✅ `Read Message History`
4. A URL will be generated at the bottom — **copy this URL** (you'll use it in Step 5)

---

## Step 5: Invite Bot to Your Server

1. Paste the copied URL from Step 4 into your browser
2. Select the Discord server where you want to add the bot
3. Click **"Authorize"**
4. Complete any CAPTCHA if prompted
5. The bot should now appear in your server's member list (offline, until you start it)

---

## Step 6: Get Your Channel ID (For Scheduled Mode)

If you plan to use scheduled query execution, you'll need the channel ID where results should be posted.

### Enable Developer Mode

1. Open Discord → **User Settings** (gear icon)
2. Go to **"Advanced"**
3. Enable **"Developer Mode"**

### Get Channel ID

1. Right-click on the Discord channel where you want results posted
2. Click **"Copy Channel ID"**
3. Save this ID for Step 8

## Step 7: Get Your Server ID (Optional, but Recommended)

Setting a Server ID enables instant command syncing during development (otherwise it can take up to an hour).

### Enable Developer Mode

1. Open Discord → **User Settings** (gear icon)
2. Go to **"Advanced"**
3. Enable **"Developer Mode"**

### Get Server ID

1. Right-click on your Discord server's name or icon
2. Click **"Copy Server ID"**
3. Save this ID for Step 8

---

## Step 8: Configure the Application

1. In your project directory, create a `.env` file for your secrets:
   ```bash
   cp .env.example .env
   # OR use the secrets template:
   # cp .env.secrets.example .env
   ```
   
   ⚠️ **IMPORTANT**: The `.env` file contains real secrets and is automatically ignored by git. Never commit it!

2. Edit the `.env` file and add your credentials:

   ```dotenv
   # Required: Paste your bot token from Step 2
   DISCORD_BOT_TOKEN=paste-your-bot-token-here

   # Optional: Paste your server ID from Step 7 (recommended for development)
   DISCORD_GUILD_ID=paste-your-server-id-here

   # Required: Your Dune API key
   DUNE_API_KEY=your-dune-api-key-here

   # Optional: Delay in seconds between sending embeds (default: 10)
   EMBED_DELAY_SECONDS=10

   # Optional: Scheduled execution settings (for scheduled mode)
   # SCHEDULED_QUERY_ID=1234567
   # SCHEDULED_EXECUTION_TIME=14:30  # HH:MM format (24-hour)
   # DISCORD_CHANNEL_ID=999999999999999999  # Channel ID for scheduled results
   ```

   **Example:**
   ```dotenv
   DISCORD_BOT_TOKEN=MTIzNDU2Nzg5MDEyMzQ1Njc4OQ.GhIjKl.MnOpQrStUvWxYzAbCdEfGhIjKlMnOpQrStUvWxY
   DISCORD_GUILD_ID=987654321098765432
   DUNE_API_KEY=your-dune-api-key-here
   ```
   
   **Note:** Never commit your actual `.env` file! It should contain real secrets and is automatically ignored by git.

---

## Step 9: Start the Bot

1. Make sure your virtual environment is activated:
   ```bash
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Run the bot:
   ```bash
   python -m scripts.run_bot
   ```

3. You should see logs like:
   ```
   INFO - bot.logging - Setting up bot...
   INFO - bot.client - Bot is ready! Logged in as YourBotName#1234 (ID: 123456789)
   INFO - bot.client - Connected to 1 guild(s)
   ```

4. The bot should appear **online** in your Discord server

---

## Step 10: Test the Bot

1. In Discord, type `/ping` in any channel where the bot has access
2. You should see the ping command appear (autocomplete)
3. Send the command — the bot should respond with "🏓 Pong! Latency: XXms"

If it works, check the bot status:
```
/status
```

This will show you the bot's current status and scheduled query information (if configured).

**Note:** When scheduled execution is configured, the bot runs queries automatically on a schedule. Use `/ping` and `/status` commands for health monitoring.

---

## Troubleshooting

### Bot Token Issues

- **"Invalid Token"**
  - Double-check that you copied the entire token with no extra spaces
  - Make sure there are no line breaks in the `.env` file
  - Try resetting the token in the Developer Portal and updating `.env`

### Commands Not Appearing

- **Commands take time to sync globally** (up to 1 hour)
- **Solution**: Set `DISCORD_GUILD_ID` in `.env` for instant sync to your server
- If you added the guild ID, restart the bot — commands should appear immediately

### "Missing Access" or "Missing Permissions"

- Make sure the bot is actually in your server (check member list)
- Verify you gave the bot the correct permissions when inviting (Step 4)
- Re-invite the bot with the correct permissions if needed

### Bot Shows as Offline

- Make sure `python -m scripts.run_bot` is running
- Check the console output for error messages
- Verify your `.env` file has the correct `DISCORD_BOT_TOKEN`

### "Application Command Failed"

- The bot might be rate-limited
- Wait a few seconds and try again
- Check the bot's console logs for detailed error messages

---

## Security Best Practices

1. **Never commit `.env` to version control**
   - The `.env` file is already in `.gitignore`
   - Double-check before pushing to GitHub

2. **Keep your bot token secret**
   - Don't share it in screenshots, messages, or public channels
   - If exposed, reset it immediately in the Developer Portal

3. **Use environment variables in production**
   - Don't hardcode tokens in your code
   - Use secure secret management for deployment

---

## Next Steps

Once your bot is running, you can:

- Check bot health with `/ping`
- View bot status and scheduled query info with `/status`
- Configure scheduled query execution in your `.env` file

For more information, see the [README.md](README.md) file.

---

## Quick Reference

| Item | Where to Find It |
|------|------------------|
| **Bot Token** | Developer Portal → Your App → Bot tab → Token |
| **Server ID** | Right-click server (with Developer Mode) → Copy Server ID |
| **Invite URL** | Developer Portal → OAuth2 → URL Generator → Copy URL |
| **Application ID** | Developer Portal → General Information → Application ID |

---

## Additional Resources

- [Discord Developer Portal](https://discord.com/developers/applications)
- [Discord.py Documentation](https://discordpy.readthedocs.io/)
- [Discord Slash Commands Guide](https://discord.com/developers/docs/interactions/application-commands)

