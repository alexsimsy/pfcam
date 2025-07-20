#!/bin/bash

echo "Fixing SECRET_KEY issue..."

# Generate a new secure secret key
NEW_SECRET_KEY=$(openssl rand -hex 32)
echo "Generated new SECRET_KEY: $NEW_SECRET_KEY"

# Update docker-compose.yml with the new secret key
sed -i "s/SECRET_KEY=.*/SECRET_KEY=$NEW_SECRET_KEY/" docker-compose.yml

echo "Updated docker-compose.yml with new SECRET_KEY"

# Restart the application
echo "Restarting application..."
docker compose down
docker compose up -d

echo "Application restarted. Checking status..."
docker compose ps

echo "Checking backend logs..."
docker compose logs backend --tail=20 