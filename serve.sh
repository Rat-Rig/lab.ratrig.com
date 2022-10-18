#!/bin/sh
docker build -t ratrig_lab .
docker run -p 80:8000 -w /app -v $(pwd):/app ratrig_lab
