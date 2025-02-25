#!/usr/bin/env python3
"""
Script to run the UpToCure application.
This starts the FastAPI server and opens the application in a browser.
"""

import os
import sys
import webbrowser
import time
import subprocess
import platform

def check_dependencies():
    """Check if required Python packages are installed."""
    try:
        import fastapi
        import uvicorn
        print("✅ Required dependencies are installed.")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("📦 Installing required packages using PDM...")
        try:
            subprocess.check_call([sys.executable, "-m", "pdm", "install"])
            print("✅ Dependencies installed successfully!")
        except Exception as install_error:
            print(f"❌ Failed to install dependencies: {install_error}")
            print("Please manually install the required packages:")
            print("pdm install")
            sys.exit(1)

def ensure_reports_dir():
    """Ensure the reports directory exists."""
    # Get the reports directory from the project root
    reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reports')
    if not os.path.exists(reports_dir):
        try:
            os.makedirs(reports_dir)
            print(f"📁 Created reports directory at {reports_dir}")
        except Exception as e:
            print(f"❌ Failed to create reports directory: {e}")
            sys.exit(1)
    else:
        print(f"✅ Reports directory exists at {reports_dir}")
    return reports_dir

def check_sample_reports(reports_dir):
    """Check if there are any reports, if not add sample report."""
    try:
        md_files = [f for f in os.listdir(reports_dir) if f.endswith('.md')]
        if not md_files:
            print("❌ No markdown reports found. Creating a sample report...")
            
            sample_report = """# Sample Report: Introduction to UpToCure

Welcome to UpToCure! This is a sample report to demonstrate the markdown parsing capabilities.

**Key Features:**
* Parses markdown to HTML
* Extracts metadata like title and date
* Displays content in a responsive carousel

## Getting Started

To add your own reports, simply create markdown files in the `reports` directory.

*Last updated: April 15, 2025*
"""
            sample_path = os.path.join(reports_dir, 'sample-report.md')
            with open(sample_path, 'w') as f:
                f.write(sample_report)
            print(f"✅ Sample report created at {sample_path}")
        else:
            print(f"✅ Found {len(md_files)} existing report(s): {', '.join(md_files)}")
    except Exception as e:
        print(f"❌ Error checking/creating sample reports: {e}")
        sys.exit(1)

def check_frontend_dir():
    """Check if the frontend directory exists."""
    # Get the frontend directory from the project root
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
    if not os.path.exists(frontend_dir):
        print(f"❌ Frontend directory not found at {frontend_dir}")
        sys.exit(1)
    
    index_file = os.path.join(frontend_dir, 'index.html')
    if not os.path.exists(index_file):
        print(f"❌ index.html not found at {index_file}")
        sys.exit(1)
    
    print(f"✅ Frontend files found at {frontend_dir}")
    return frontend_dir

def start_server():
    """Start the FastAPI server."""
    print("🚀 Starting UpToCure server...")
    
    # Open browser after a short delay to give the server time to start
    def open_browser():
        time.sleep(2)
        url = 'http://localhost:8000'
        print(f"🌐 Opening browser at {url}")
        webbrowser.open(url)
    
    from threading import Thread
    browser_thread = Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Set up environment variables
    project_root = os.path.dirname(os.path.dirname(__file__))
    os.environ["PYTHONPATH"] = project_root
    
    # Start the server using uvicorn pointing to the src directory
    try:
        print("⚡ Server starting... (Ctrl+C to stop)")
        # Update the path to use src.app:app
        subprocess.run([sys.executable, "-m", "uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"])
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("=" * 50)
    print("🔬 UpToCure Application Launcher 🔬")
    print("=" * 50)
    
    # Check and install dependencies
    check_dependencies()
    
    # Ensure reports directory exists
    reports_dir = ensure_reports_dir()
    
    # Check for sample reports
    check_sample_reports(reports_dir)
    
    # Check frontend directory
    check_frontend_dir()
    
    # Start the server
    start_server() 