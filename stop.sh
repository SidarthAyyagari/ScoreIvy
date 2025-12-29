#!/bin/bash

# ScoreIvy Stop Script
# Stops all running services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛑 Stopping ScoreIvy services...${NC}\n"

# Stop Docker containers
# echo -e "${GREEN}📦 Stopping database...${NC}"
# docker-compose down 2>/dev/null || echo "Database already stopped"

# Kill backend process
echo -e "${GREEN}🔧 Stopping backend...${NC}"
pkill -f "uvicorn main:app" 2>/dev/null || echo "Backend already stopped"

# Kill frontend process
echo -e "${GREEN}🎨 Stopping frontend...${NC}"
pkill -f "next dev" 2>/dev/null || echo "Frontend already stopped"

echo -e "\n${GREEN}✅ All services stopped${NC}"

