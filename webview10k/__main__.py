"""Entry point for the 10-K Parser web application.

This module serves as the application entry point when running directly.
It creates and configures the Flask application instance and starts the development server.

Usage:
    python -m webview10k

Configuration:
    HOST: Server host address (default: 127.0.0.1)
    PORT: Server port (default: 5555)
    DEBUG: Debug mode flag (default: True)

Notes:
    - Uses the create_app factory from webview10k package
    - Runs in debug mode for development purposes
    - Host configuration is read from app.config['HOST']
"""
from webview10k import create_app

app = create_app()

if __name__ == "__main__":

    app.run(host=app.config['HOST'],
            port=5555,
            debug=True)