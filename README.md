# Telegram Inline Whisper Bot

A Telegram inline bot that allows users to send secret messages that can only be read by the intended recipient.

## Features

- 🤫 Send secret messages using inline mode
- 🔒 Messages can only be opened by the intended recipient
- 📊 MongoDB storage for message tracking
- 👨‍💼 Admin notifications for new whispers
- 🌐 Multi-language support (English/Hindi)
- ☁️ Ready for deployment on Render.com

## Setup

1. **Create a Telegram Bot**
   - Message @BotFather on Telegram
   - Use `/newbot` command
   - Enable inline mode with `/setinline`

2. **Set up MongoDB Atlas**
   - Create a free account at https://mongodb.com
   - Create a cluster and get connection string

3. **Environment Variables**
   ```env
   BOT_TOKEN=your_bot_token_here
   MONGODB_URI=your_mongodb_connection_string
   ADMIN_IDS=123456789,987654321  # Your Telegram user IDs
   WEBHOOK_BASE_URL=https://your-app-name.onrender.com
   DEFAULT_LANG=en  # or hi
