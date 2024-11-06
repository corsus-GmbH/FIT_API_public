#!/bin/sh

export LOG_FILE="/usr/src/FIT/server.log"
# Start the Uvicorn server and redirect output to the log file
#uvicorn API.main:app --host 0.0.0.0 --port 80 > "$LOG_FILE" 2>&1
uvicorn API.main:app --host 0.0.0.0 --port 80
