#!/bin/bash
# Start the backend server

echo "Starting Mutual Fund Chatbot Backend..."
echo "Checking for processes on port 5000 and 5001..."

# Kill any existing processes on ports 5000 and 5001
lsof -ti:5000 | xargs kill -9 2>/dev/null || true
lsof -ti:5001 | xargs kill -9 2>/dev/null || true

# Start the backend on port 5001
echo "Starting backend on port 5001..."
cd /Users/chiragalawat/chatbot
python3 -m flask run --port=5001

# Or use the direct Python method:
# python3 app.py
