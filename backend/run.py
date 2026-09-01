"""
Main execution script for running Veritas AI Authenticity backend.
"""

import os
from app import create_app

env = os.environ.get("FLASK_ENV", "development")
app = create_app(env)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"==================================================")
    print(f" [*] AI Content Authenticity Detection System")
    print(f" [*] Backend API listening on http://{host}:{port}")
    print(f" [*] Health Check: http://localhost:{port}/api/health")
    print(f"==================================================")

    app.run(host=host, port=port, debug=True)
