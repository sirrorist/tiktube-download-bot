#!/bin/bash

# Deployment script for remote server

echo "🚀 Starting deployment..."

# Pull latest changes
git pull origin main

# Build and restart containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Run database migrations
docker-compose exec bot alembic upgrade head

# Clean up old files
docker-compose exec bot find temp/ -type f -mtime +1 -delete

echo "✅ Deployment completed!"
