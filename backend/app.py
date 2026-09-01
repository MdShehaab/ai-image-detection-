"""
Flask Application Factory for Content Authenticity Detection System.
"""

import os
from flask import Flask, jsonify
from flask_cors import CORS

from config import config_by_name, Config
from api.routes import api_bp

def create_app(config_name: str = "default") -> Flask:
    """
    Application factory initializing Flask app, CORS, configurations,
    error handlers, and API blueprints.
    """
    app = Flask(__name__)
    
    # Load configuration
    selected_config = config_by_name.get(config_name, Config)
    app.config.from_object(selected_config)
    
    # Ensure upload directory exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    
    # Enable CORS for all frontend origins in development
    CORS(
        app,
        resources={r"/api/*": {"origins": "*"}},
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
        methods=["GET", "POST", "OPTIONS"]
    )
    
    # Register blueprints
    app.register_blueprint(api_bp)
    
    # Root status endpoint
    @app.route("/", methods=["GET"])
    def root():
        return jsonify({
            "message": "AI Content Authenticity Detection System Backend API",
            "docs": "/api/modules",
            "health": "/api/health"
        }), 200

    # Custom Error Handlers
    @app.errorhandler(413)
    def request_entity_too_large(error):
        max_mb = app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024)
        return jsonify({
            "error": "File size exceeds the maximum limit.",
            "max_size_allowed_mb": max_mb,
            "status_code": 413
        }), 413

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "error": "The requested resource or endpoint was not found.",
            "status_code": 404
        }), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            "error": "Internal server error occurred within the detection pipeline.",
            "status_code": 500
        }), 500

    return app

if __name__ == "__main__":
    app = create_app(os.environ.get("FLASK_ENV", "development"))
    port = int(os.environ.get("PORT", 5000))
    print(f"[*] Veritas Authenticity Backend running on http://127.0.0.1:{port}")

    app.run(host="0.0.0.0", port=port, debug=True)
