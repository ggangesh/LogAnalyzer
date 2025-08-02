#!/usr/bin/env python3
"""
LogSage AI Frontend - Development Server
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from app import app

if __name__ == '__main__':
    # Check if .env file exists, if not create from template
    env_file = current_dir / '.env'
    env_template = current_dir / '.env.template'
    
    if not env_file.exists() and env_template.exists():
        print("Creating .env file from template...")
        with open(env_template, 'r') as template:
            with open(env_file, 'w') as env:
                env.write(template.read())
        print("Please edit .env file with your configuration settings.")
    
    # Get configuration from environment
    host = os.environ.get('FRONTEND_HOST', '0.0.0.0')
    port = int(os.environ.get('FRONTEND_PORT', 3000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    print(f"Starting LogSage AI Frontend on http://{host}:{port}")
    print(f"Debug mode: {debug}")
    print("Press Ctrl+C to stop the server")
    
    try:
        app.run(host=host, port=port, debug=debug)
    except KeyboardInterrupt:
        print("\nShutting down LogSage AI Frontend...")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)