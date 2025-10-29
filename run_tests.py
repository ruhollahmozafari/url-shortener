#!/usr/bin/env python3
"""
Simple test runner for the URL shortener project.
Run this to execute all tests.
"""

import subprocess
import sys
import os

def run_tests():
    """Run the test suite"""
    print("🧪 Running URL Shortener Tests")
    print("=" * 40)
    
    # Change to project directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        # Run pytest
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/", 
            "-v", 
            "--tb=short"
        ], check=True)
        
        print("\n✅ All tests passed!")
        return 0
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Tests failed with exit code {e.returncode}")
        return e.returncode
    except FileNotFoundError:
        print("❌ pytest not found. Install with: pip install pytest")
        return 1

if __name__ == "__main__":
    sys.exit(run_tests())
