# DealMaster Telegram Bot (Railway Deployment)

This is a Telegram bot to upload and schedule affiliate products directly to your Telegram channel. Built using `pyTelegramBotAPI`.

## Features
- Admin-only control
- Upload product with image, description, and affiliate link
- Schedule post with built-in timer
- 24/7 uptime on Railway
- No dynamic cloning/token handling (secure)

## Files
- `DealMaster_Simplified.py`: Main bot code
- `Procfile`: Required for Railway to start the bot
- `requirements.txt`: Python packages needed

## How to Deploy on Railway

### Step 1: Create GitHub Repo
- Upload all 3 files (`DealMaster_Simplified.py`, `Procfile`, `requirements.txt`) to GitHub

### Step 2: Connect Railway
1. Go to https://railway.app
2. Create New Project > Deploy from GitHub
3. Select your repo
4. Railway will auto-detect `Procfile` and start bot

### Step 3: Set Environment Variables
Go to Railway > Variables and set:
- `MAIN_TOKEN`: Your bot token from BotFather
- `ADMIN_ID`: Your Telegram numeric user ID
- `CHANNEL_USERNAME`: Your channel username (e.g., `@YourChannel`)

### Done!
Bot will now run 24/7 in the cloud.
