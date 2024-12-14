#!/bin/bash

for i in {1..4}
do
    PORT=$((5000 + i))
    NODE_ID="operator_${i}_id"
    echo "Starting $NODE_ID on port $PORT..."
    python operator.py $NODE_ID $PORT &
done
