# 🏭 Industrial Safety Monitor

AI-powered real-time video analytics for industrial safety monitoring using Groq's Maverick vision model.

## ✨ Features

- **Real-time Video Analysis**: Continuous monitoring of webcam feed (0.5s intervals)
- **AI-Powered Hazard Detection**: Uses Groq's Maverick vision model to identify safety hazards
- **Beautiful Web Interface**: Modern, responsive dashboard with live video feed
- **Audio Alerts**: Text-to-speech warnings for critical hazards using PlayAI TTS
- **Smart Incident Detection**: Avoids duplicate announcements for the same hazard
- **Rate Limiting**: Prevents announcement spam with intelligent throttling
- **Secure Authentication**: Login system with API key validation
- **Real-time Statistics**: Track analyses, hazards detected, and monitoring uptime
- **Severity Classification**: Categorizes hazards from low to critical
- **Actionable Recommendations**: Provides specific safety recommendations

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Webcam
- Groq API key ([Get one here](https://console.groq.com))

### Installation

1. **Clone or navigate to the project directory**

```bash
cd "Video Analytics"
```

2. **Create a virtual environment** (recommended)

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

### Running the Application

1. **Start the web server**

```bash
python app.py
```

2. **Open your browser**

Navigate to: `http://localhost:8080`

3. **Login with your Groq API key**

Enter your Groq API key on the login page ([Get one here](https://console.groq.com))

4. **Start monitoring**

Click the "Start Monitoring" button to begin real-time safety analysis.

## 🎯 How It Works

1. **Video Capture**: The application captures frames from your webcam every 0.5 seconds
2. **AI Analysis**: Each frame is sent to Groq's Maverick vision model for safety analysis
3. **Hazard Detection**: The AI identifies potential safety hazards including:
   - Missing PPE (helmets, vests, goggles, gloves)
   - Proximity to dangerous machinery (forklifts, vehicles, equipment)
   - Fall hazards and working at height
   - Fire/smoke/spill risks
   - Blocked emergency exits
   - Trip and fall hazards
4. **Smart Incident Tracking**: Duplicate incidents are detected and filtered to avoid announcement spam
5. **Real-time Updates**: Results are instantly displayed in the web dashboard
6. **Audio Alerts**: New hazards trigger voice warnings via text-to-speech (rate-limited to prevent spam)
7. **Status Management**: System tracks hazard lifecycle (new → same → cleared) with appropriate announcements

## 🏗️ Project Structure

```
Video Analytics/
├── app.py                 # Flask backend server with AI analysis
├── requirements.txt       # Python dependencies
├── templates/
│   ├── index.html        # Main dashboard interface
│   └── login.html        # Login page
├── static/
│   ├── css/
│   │   └── style.css     # Styling
│   └── js/
│       └── app.js        # Frontend logic & Socket.IO
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## 🎨 Features Overview

### Dashboard Components

- **Live Video Feed**: Real-time webcam stream with status overlay
- **Safety Status Card**: Current hazard status and severity level
- **Detected Hazards**: List of identified safety concerns
- **Recommendations**: AI-generated safety recommendations
- **Session Statistics**: Total analyses, hazards found, critical alerts, and uptime

### Severity Levels

- 🟢 **None/Low**: Safe conditions
- 🟡 **Medium**: Potential safety concerns
- 🟠 **High**: Significant hazards requiring attention
- 🔴 **Critical**: Immediate danger, triggers audio alerts

## 🔧 Configuration

You can modify these settings in `app.py`:

```python
ANALYZE_EVERY_SECONDS = 0.5           # Analysis frequency (seconds)
MIN_ANNOUNCEMENT_INTERVAL = 3.0       # Minimum time between announcements
announcement_queue = Queue(maxsize=5) # Max queued announcements
HAZARD_PROMPT = "..."                 # Customize the AI instructions
```

## 🛠️ Technologies Used

- **Backend**: Flask, Flask-SocketIO
- **AI/ML**: Groq (Maverick vision model, PlayAI TTS)
- **Computer Vision**: OpenCV
- **Frontend**: HTML5, CSS3, JavaScript, Socket.IO
- **Audio**: sounddevice, soundfile

## 📝 Notes

- The application requires webcam access
- Analysis happens every 0.5 seconds for fast hazard detection
- Audio alerts are rate-limited (minimum 3 seconds between announcements)
- Duplicate incidents are intelligently filtered to avoid spam
- The system tracks hazard lifecycle: new → same → cleared
- Audio alerts only play for new hazards, not repeated detections
- The demo is designed for industrial settings but works in any environment

## 🔒 Security

- API keys are stored in session cookies (not in code)
- Never commit your API keys to version control
- Login required for all monitoring features
- Session-based authentication with secure cookies
- Consider using HTTPS in production deployments

## 📄 License

This project is provided as-is for demonstration purposes.

## 🤝 Contributing

Feel free to fork, modify, and improve this project!

## 💡 Tips for Best Results

- Ensure good lighting for better image analysis
- Position the camera to capture the work area clearly
- Test with industrial safety scenarios for accurate results
- Monitor the console for detailed analysis logs

---

**Powered by Groq's Maverick AI** | Built with ❤️ for industrial safety

