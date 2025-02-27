#!/usr/bin/env python
"""
UpToCure Application Runner
===========================

This script provides a simple entry point to run the UpToCure application.
"""

import os
import sys
import logging
from src.app import app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Get port from environment or use default 8080
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Starting UpToCure on port {port}")
    
    # Run the application with debug mode enabled for development
    app.run(host='0.0.0.0', port=port, debug=True) 