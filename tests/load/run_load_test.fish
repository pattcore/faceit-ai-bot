#!/usr/bin/env fish

# Load testing script using Locust

set -l HOST "http://localhost:8000"
set -l USERS 100
set -l SPAWN_RATE 10
set -l RUN_TIME "5m"

echo "Starting load test..."
echo "Target: $HOST"
echo "Users: $USERS"
echo "Spawn rate: $SPAWN_RATE/sec"
echo "Duration: $RUN_TIME"

locust -f locustfile.py \
    --host=$HOST \
    --users=$USERS \
    --spawn-rate=$SPAWN_RATE \
    --run-time=$RUN_TIME \
    --headless \
    --csv=results
