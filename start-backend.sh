#!/bin/bash

# Start Backend Script for Core Website Vitals

echo "Starting Core Website Vitals Backend..."

# Navigate to backend directory
cd backend

# Activate virtual environment
source venv/bin/activate

# Start the backend server
echo "Starting FastAPI server on http://localhost:8000"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000