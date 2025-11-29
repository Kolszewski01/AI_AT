#!/bin/bash
# Run desktop application

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run application
python main.py
