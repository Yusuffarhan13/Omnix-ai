# Omnix AI

An intelligent AI assistant with live voice interaction, browser automation, and comprehensive settings management.

## Features

- **Live Voice Mode**: Real-time voice conversation with animated voice sphere
- **Browser Automation**: Automated web browsing and task execution
- **Dark/Light Theme**: Complete theme switching with persistent settings
- **Settings Management**: Comprehensive settings panel with appearance, personalization, and more
- **Multi-Modal AI**: Text and voice interaction capabilities

## Quick Start

### Railway Deployment

1. **Fork this repository** to your GitHub account

2. **Connect to Railway**:
   - Visit [Railway](https://railway.app)
   - Click "Start a New Project"
   - Select "Deploy from GitHub repo"
   - Choose your forked repository

3. **Set Environment Variables** in Railway dashboard:
   ```
   GOOGLE_API_KEY=your_google_api_key_here
   ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
   PORT=8003
   FLASK_ENV=production
   ```

4. **Deploy**: Railway will automatically build and deploy your application

### Local Development

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd omnix-ai
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.template .env
   # Edit .env with your API keys
   ```

4. **Run the application**:
   ```bash
   python main.py
   ```

5. **Access the app**: Open http://localhost:8003

## Environment Variables

Copy `.env.template` to `.env` and configure:

- `GOOGLE_API_KEY`: Google Gemini API key (required)
- `ELEVENLABS_API_KEY`: ElevenLabs API for voice features
- `PORT`: Application port (default: 8003)
- `FLASK_ENV`: Environment (production/development)

## Settings

Access comprehensive settings via the sidebar settings button:

- **Appearance**: Theme selection, font preferences
- **Personalize**: AI customization, voice selection, creativity settings
- **Connectors**: External service integrations
- **Privacy**: Data and privacy controls

## Voice Features

- Live voice interaction with real-time responses
- Multiple voice options via ElevenLabs
- Animated voice sphere with reactive animations

## Browser Automation

Automated web browsing capabilities for task execution and research.

## Tech Stack

- **Backend**: Flask + SocketIO
- **Frontend**: HTML, CSS, JavaScript
- **AI**: Google Gemini, OpenAI Whisper
- **Voice**: ElevenLabs TTS
- **Browser**: Browser-use automation

## Support

For issues and support, please check the project documentation or create an issue in the repository.