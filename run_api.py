#!/usr/bin/env python3
"""
Wrapper script to run uvicorn with proper Python path setup.
This ensures local packages are importable when uvicorn loads the app.
"""
import sys
import os

# Ensure we're in the right directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Add local packages to path FIRST, before any imports
# This is critical for editable package resolution
sys.path.insert(0, script_dir)
sys.path.insert(0, os.path.join(script_dir, 'python_magnetsetup'))
sys.path.insert(0, os.path.join(script_dir, 'python_magnetgeo'))

# Test that we can import the problem module
try:
    import python_magnetsetup.config
    print(f"✓ Successfully imported python_magnetsetup from: {python_magnetsetup.config.__file__}")
except ImportError as e:
    print(f"✗ Failed to import python_magnetsetup: {e}")
    sys.exit(1)

# Now import the app directly (not via string) so imports happen with correct sys.path
try:
    from python_magnetdb.web import app
    print("✓ Successfully imported FastAPI app")
except ImportError as e:
    print(f"✗ Failed to import app: {e}")
    sys.exit(1)

# Run uvicorn with the app object (not string reference)
if __name__ == "__main__":
    import uvicorn
    print("Starting uvicorn server...")
    uvicorn.run(
        app,  # Pass the actual app object, not a string
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
