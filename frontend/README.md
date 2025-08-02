# LogSage AI Frontend

Flask-based frontend for the LogSage AI log analysis system with Tailwind CSS styling.

## Features

- **Responsive Dashboard**: Clean, modern interface built with Tailwind CSS
- **File Upload Interface**: Drag-and-drop file upload with progress tracking
- **Log Analysis Views**: Browse and filter uploaded log files
- **Anomaly Detection Display**: View detected anomalies and patterns
- **AI Chat Interface**: Interactive chat with AI for log analysis
- **Real-time Status**: System health monitoring and status indicators

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   ```bash
   cp .env.template .env
   # Edit .env with your settings
   ```

3. **Start the Frontend**:
   ```bash
   python run.py
   ```

The frontend will be available at `http://localhost:3000`

## Configuration

Edit `.env` file to configure:

- `SECRET_KEY`: Flask secret key for sessions
- `BACKEND_URL`: URL of the FastAPI backend (default: http://localhost:8000)
- `FRONTEND_HOST`: Host to bind to (default: 0.0.0.0)
- `FRONTEND_PORT`: Port to listen on (default: 3000)

## Project Structure

```
frontend/
├── app.py              # Main Flask application
├── run.py              # Development server runner
├── requirements.txt    # Python dependencies
├── .env.template       # Environment configuration template
├── templates/          # Jinja2 templates
│   ├── base.html       # Base template with Tailwind CSS
│   ├── dashboard.html  # Main dashboard
│   ├── upload.html     # File upload page
│   ├── logs.html       # Log analysis page
│   ├── anomalies.html  # Anomaly detection page
│   ├── chat.html       # AI chat interface
│   ├── 404.html        # Error pages
│   └── 500.html
└── static/             # Static assets
    ├── css/
    │   └── custom.css  # Custom styles
    └── js/
        └── main.js     # Main JavaScript functionality
```

## Backend Integration

The frontend communicates with the FastAPI backend through REST API calls. Make sure the backend is running on the configured `BACKEND_URL` before starting the frontend.

## Development

- The frontend runs in debug mode by default in development
- Templates are automatically reloaded when changed
- Static files are served from the `/static` directory
- CORS is configured in the backend to allow requests from localhost:3000

## Technology Stack

- **Flask**: Python web framework
- **Jinja2**: Template engine
- **Tailwind CSS**: Utility-first CSS framework (via CDN)
- **Font Awesome**: Icon library
- **Vanilla JavaScript**: Frontend interactivity