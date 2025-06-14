# Catering Service Voice Agent 🎤🍽️

An intelligent voice-powered chatbot for Catering Service marketplace that helps customers find the perfect catering services through natural conversation. Built with **Retell AI** for voice interactions and **OpenAI** for intelligent responses.

![EZCaters Voice Agent](https://img.shields.io/badge/Voice-AI-blue) ![Python](https://img.shields.io/badge/Python-3.8+-green) ![Flask](https://img.shields.io/badge/Flask-2.0+-red) ![Retell AI](https://img.shields.io/badge/Retell-AI-purple)

## 🌟 Features

### 🎯 Core Functionality
- **Voice-First Interface**: Natural conversation using Retell AI's advanced voice technology
- **Intelligent Search**: AI-powered catering service recommendations based on:
  - Cuisine preferences (Italian, Mexican, Chinese, Mediterranean, American)
  - Location and delivery areas
  - Specific menu items and dietary requirements
  - Budget and event size
- **Real-time Responses**: Instant recommendations with detailed caterer information
- **Seamless Handoff**: Direct connection to preferred catering partners

### 🛠️ Technical Features
- **Speech Recognition**: Browser-based voice input with real-time transcription
- **Text-to-Speech**: Natural voice responses for complete hands-free experience
- **Responsive Design**: Beautiful, modern UI that works on all devices
- **RESTful API**: Clean endpoints for searching and managing catering services
- **Error Handling**: Robust error management and fallback options

### 🏢 Business Features
- **Marketplace Integration**: Connects customers with verified catering partners
- **Lead Qualification**: Captures customer preferences and contact information
- **Call Analytics**: Track conversation flows and conversion metrics
- **Multi-channel Support**: Voice calls, web interface, and potential SMS integration

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Retell AI API key ([Get it here](https://www.retellai.com/))
- OpenAI API key ([Get it here](https://platform.openai.com/))

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ezcaters-voice-agent
   ```

2. **Create and activate virtual environment**
   ```bash
   python3 -m venv ezcaters_voice_agent
   source ezcaters_voice_agent/bin/activate  # On Windows: ezcaters_voice_agent\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env_template.txt .env
   ```
   
   Edit `.env` file with your API keys:
   ```env
   RETELL_API_KEY=your_retell_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   WEBHOOK_URL=https://your-domain.com/webhook
   ```

5. **Set up Retell AI agent**
   ```bash
   python retell_agent.py setup
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

7. **Open your browser**
   ```
   http://localhost:5000
   ```

## 📋 API Documentation

### Endpoints

#### `POST /webhook`
Webhook endpoint for Retell AI voice interactions
- **Purpose**: Handles voice call events and processes customer speech
- **Authentication**: Retell AI webhook signature
- **Request Body**: Retell AI webhook payload

#### `POST /search`
Search catering services
```json
{
  "type": "cuisine|location|menu",
  "query": "search term"
}
```

#### `GET /services`
List all available catering services

#### `GET /health`
Health check endpoint

### Example API Usage

```python
import requests

# Search for Italian catering
response = requests.post('http://localhost:5000/search', json={
    "type": "cuisine",
    "query": "Italian"
})

# Get all services
services = requests.get('http://localhost:5000/services')
```

## 🎙️ Voice Agent Setup

### Setting up Retell AI

1. **Get your API key** from [Retell AI Dashboard](https://app.retellai.com/)

2. **Configure your webhook URL** (must be publicly accessible):
   ```bash
   # For development, use ngrok
   ngrok http 5000
   ```

3. **Set up the voice agent**:
   ```bash
   python retell_agent.py setup
   ```

4. **Test the agent**:
   ```bash
   python retell_agent.py test +1234567890
   ```

### Voice Agent Configuration

The voice agent is configured with:
- **Conversation Flow**: Structured dialogue for gathering customer requirements
- **Voice Settings**: Professional, friendly voice with natural pacing
- **Intent Recognition**: Understands cuisine, location, and menu preferences
- **Fallback Handling**: Graceful error recovery and alternative suggestions

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Customer      │    │   EZCaters      │    │   Retell AI     │
│   (Phone/Web)   │◄──►│   Voice Agent   │◄──►│   Platform      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   OpenAI GPT    │
                       │   (Intent &     │
                       │   Responses)    │
                       └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Catering      │
                       │   Database      │
                       │   (Mock Data)   │
                       └─────────────────┘
```

## 🎯 Usage Examples

### Voice Interactions

**Customer**: "Hi, I need catering for my office meeting"
**Agent**: "Hello! I'd be happy to help you find perfect catering for your office meeting. What type of cuisine are you interested in?"

**Customer**: "Something Italian, maybe pasta or pizza"
**Agent**: "Great choice! I found Bella's Italian Catering that specializes in Italian cuisine. They're rated 4.8 stars and located in Boston, MA. They offer pasta, pizza, sandwiches, and salads. Would you like their contact information?"

### Web Interface

1. **Voice Demo**: Click "Start Voice Demo" to test speech recognition
2. **Browse Caterers**: Use the search modal to find services by cuisine, location, or menu
3. **View Results**: See detailed information including ratings, specialties, and contact info

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `RETELL_API_KEY` | Your Retell AI API key | Yes |
| `OPENAI_API_KEY` | Your OpenAI API key | Yes |
| `WEBHOOK_URL` | Public URL for Retell webhooks | Yes |
| `DEFAULT_VOICE_ID` | Preferred voice ID (default: 11labs-Adrian) | No |
| `MAX_SEARCH_RADIUS` | Search radius in miles (default: 50) | No |
| `BUSINESS_START_HOUR` | Business hours start (default: 8) | No |
| `BUSINESS_END_HOUR` | Business hours end (default: 22) | No |

### Customization

#### Adding New Caterers
Edit the `CateringService` class in `app.py`:

```python
{
    "id": 6,
    "name": "Your Catering Service",
    "cuisine": "Cuisine Type",
    "location": "City, State",
    "coordinates": (latitude, longitude),
    "rating": 4.5,
    "price_range": "$$",
    "min_order": 25,
    "specialties": ["item1", "item2"],
    "phone": "+1-555-0106",
    "description": "Service description"
}
```

#### Modifying Voice Responses
Update prompts in `retell_agent.py` or the `VoiceAssistant` class in `app.py`.

## 📱 Frontend Features

### Modern UI Components
- **Animated Voice Button**: Visual feedback during recording
- **Real-time Transcription**: See what the agent hears
- **Response Display**: View agent responses with TTS playback
- **Search Modal**: Alternative text-based search interface
- **Responsive Design**: Mobile-friendly interface

### Browser Compatibility
- Chrome/Edge: Full speech recognition support
- Firefox: Limited speech recognition
- Safari: Limited speech recognition
- Mobile: Touch-optimized interface

## 🧪 Testing

### Manual Testing
1. **Web Interface**: Test voice demo and search functionality
2. **API Endpoints**: Use Postman or curl to test APIs
3. **Voice Calls**: Use Retell AI dashboard to make test calls

### Example Test Scenarios
- "I need Italian food in Boston"
- "What Mexican restaurants deliver to Cambridge?"
- "Do you have any vegetarian options?"
- "I'm looking for catering for 50 people"

## 📊 Monitoring & Analytics

### Call Analytics
- Track conversation duration and success rates
- Monitor popular cuisine types and locations
- Analyze customer drop-off points

### Performance Metrics
- Response time monitoring
- Error rate tracking
- Customer satisfaction scores

## 🚀 Deployment

### Production Deployment

1. **Set up a cloud server** (AWS, Google Cloud, etc.)

2. **Configure environment variables** for production

3. **Set up reverse proxy** (nginx recommended):
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

4. **Use production WSGI server**:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

5. **Set up SSL certificate** for HTTPS (required for webhooks)

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Common Issues

**Speech recognition not working**
- Ensure you're using HTTPS or localhost
- Check browser permissions for microphone access
- Try Chrome or Edge for best compatibility

**Retell AI webhook errors**
- Verify webhook URL is publicly accessible
- Check API key configuration
- Ensure webhook endpoint returns proper JSON responses

**OpenAI API errors**
- Verify API key is correct and has credits
- Check rate limits and quotas
- Monitor usage in OpenAI dashboard

### Getting Help

- 📧 Email: support@ezcaters.com
- 💬 Discord: [Join our community](https://discord.gg/ezcaters)
- 📚 Documentation: [Full docs](https://docs.ezcaters.com)
- 🐛 Issues: [GitHub Issues](https://github.com/ezcaters/voice-agent/issues)

## 🔗 Related Links

- [Retell AI Documentation](https://docs.retellai.com/)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [EZCaters Website](https://www.ezcater.com/)
- [Voice AI Best Practices](https://docs.retellai.com/best-practices)

---

**Built with ❤️ by the EZCaters team**

*Revolutionizing catering discovery through voice AI technology* 
