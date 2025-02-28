"""
UpToCure Backend Application
===========================

This is a simplified Flask app that doesn't rely on FastAPI.
"""

import os
import sys
import logging
from flask import Flask, jsonify, render_template, send_from_directory, request

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__, static_folder='../frontend', static_url_path='')

# Set up base directory
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
frontend_dir = os.path.join(base_dir, 'frontend')
reports_dir = os.path.join(base_dir, 'reports')
images_dir = os.path.join(frontend_dir, 'images')

@app.route('/')
def index():
    """Serve the main page"""
    logger.info("Serving index page")
    return send_from_directory(frontend_dir, 'index.html')

@app.route('/images/<path:filename>')
def serve_image(filename):
    """Serve images from the images directory"""
    logger.info(f"Serving image: {filename}")
    return send_from_directory(images_dir, filename)

@app.route('/api')
def api_root():
    """API root endpoint"""
    return jsonify({
        "message": "Welcome to UpToCure API",
        "version": "1.0.0"
    })

@app.route('/api/reports')
def get_reports():
    """Get reports list"""
    lang = request.args.get('lang', 'en')
    try:
        from src.parser import process_reports
        reports = process_reports(reports_dir, lang)
        return jsonify({
            "error": False,
            "message": "Reports retrieved successfully",
            "reports": reports
        })
    except Exception as e:
        logger.error(f"Error processing reports: {str(e)}")
        return jsonify({
            "error": True,
            "message": f"Error processing reports: {str(e)}",
            "reports": []
        })

@app.route('/methodology.html')
def methodology():
    """Serve the methodology page"""
    return send_from_directory(frontend_dir, 'methodology.html')

# Add other routes as needed

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return jsonify({"error": True, "message": "Page not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": True, "message": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080))) 