# Quran-Discord-Bot

## Deployment on Coolify

1. Create a new application in Coolify
2. Select "Docker Compose" as the deployment method
3. Use the following environment variables:
   - `DISCORD_TOKEN`: Your Discord bot token
   - `DISCORD_PREFIX`: Command prefix (default: "!")
4. Disable "Expose Publicly" option since Discord bots don't need public URLs
5. Deploy!

The bot will automatically:
- Download and extract Quran MP3 files
- Install dependencies
- Start the bot
