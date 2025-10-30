#!/bin/bash

# Simple Hit Worker Startup Script
# This starts the simplified hit processor worker

echo "🚀 Starting Simple Hit Worker..."
echo "=================================="

# Activate virtual environment
source .venv/bin/activate

# Start the hit worker
python -m shortener_app.hit_processor.hit_worker

echo "🛑 Simple Hit Worker stopped"
