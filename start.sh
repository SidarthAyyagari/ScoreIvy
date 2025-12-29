#!/bin/bash

# ScoreIvy Startup Script
# Starts database (Docker), backend, and frontend

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting ScoreIvy Application...${NC}\n"

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down services...${NC}"
    docker-compose down 2>/dev/null || true
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    exit
}

trap cleanup SIGINT SIGTERM

# 1. Start Database (Docker)
echo -e "${GREEN}📦 Starting database (Docker)...${NC}"
docker-compose up -d
echo -e "${GREEN}✅ Database started${NC}\n"

# Wait for database to be ready
echo -e "${YELLOW}⏳ Waiting for database to be ready...${NC}"
sleep 5

# 2. Start Backend
echo -e "${GREEN}🔧 Starting backend server...${NC}"
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "venv/.installed" ]; then
    echo -e "${YELLOW}📥 Upgrading pip and setuptools...${NC}"
    pip3 install --upgrade pip setuptools wheel
    
    echo -e "${YELLOW}📥 Installing backend dependencies...${NC}"
    pip3 install -r requirements.txt
    touch venv/.installed
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "DATABASE_URL=postgresql://postgres:postgres@localhost:5432/scoreivy" > .env
fi

# Start backend in background
python3 -m uvicorn main:app --reload > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..
echo -e "${GREEN}✅ Backend started (PID: $BACKEND_PID)${NC}\n"

# 3. Start Frontend
echo -e "${GREEN}🎨 Starting frontend server...${NC}"
cd frontend

# Install dependencies
echo -e "${YELLOW}📥 Installing frontend dependencies...${NC}"
npm install

# Start frontend in background
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo -e "${GREEN}✅ Frontend started (PID: $FRONTEND_PID)${NC}\n"

# Wait a moment for servers to start
sleep 3

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ All services started successfully!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "\n📍 Services:"
echo -e "   🗄️  Database:  http://localhost:5432"
echo -e "   🔧 Backend:    http://localhost:8000"
echo -e "   📚 API Docs:   http://localhost:8000/docs"
echo -e "   🎨 Frontend:   http://localhost:3000"
echo -e "\n📋 Logs:"
echo -e "   Backend:  tail -f backend.log"
echo -e "   Frontend: tail -f frontend.log"
echo -e "\n${YELLOW}Press Ctrl+C to stop all services${NC}\n"

# Keep script running and wait for processes
echo -e "${BLUE}Services are running. Check logs with:${NC}"
echo -e "   tail -f backend.log"
echo -e "   tail -f frontend.log\n"

# Wait for background processes
wait $BACKEND_PID $FRONTEND_PID 2>/dev/null || true

