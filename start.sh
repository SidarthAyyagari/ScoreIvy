#!/bin/bash

# ScoreIvy Startup Script
# Starts database (Docker), backend, student UI, and admin UI
# Press Ctrl+C to stop all services

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting ScoreIvy Application...${NC}\n"

# Initialize PIDs (will be set when processes start)
BACKEND_PID=""
USER_UI_PID=""
ADMIN_UI_PID=""

# Function to cleanup on exit (Ctrl+C)
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down services...${NC}"
    
    # Kill backend process if it exists
    if [ ! -z "$BACKEND_PID" ] && kill -0 $BACKEND_PID 2>/dev/null; then
        echo -e "${YELLOW}   Stopping backend (PID: $BACKEND_PID)...${NC}"
        kill $BACKEND_PID 2>/dev/null || true
        wait $BACKEND_PID 2>/dev/null || true
    else
        pkill -f "uvicorn main:app" 2>/dev/null || true
    fi
    
    # Kill student UI process if it exists
    if [ ! -z "$USER_UI_PID" ] && kill -0 $USER_UI_PID 2>/dev/null; then
        echo -e "${YELLOW}   Stopping student UI (PID: $USER_UI_PID)...${NC}"
        kill $USER_UI_PID 2>/dev/null || true
        wait $USER_UI_PID 2>/dev/null || true
    fi

    # Kill admin UI process if it exists
    if [ ! -z "$ADMIN_UI_PID" ] && kill -0 $ADMIN_UI_PID 2>/dev/null; then
        echo -e "${YELLOW}   Stopping admin UI (PID: $ADMIN_UI_PID)...${NC}"
        kill $ADMIN_UI_PID 2>/dev/null || true
        wait $ADMIN_UI_PID 2>/dev/null || true
    else
        pkill -f "next dev" 2>/dev/null || true
    fi
    
    # Note: Docker containers are NOT stopped - database keeps running
    # To stop database, run: docker-compose down
    
    echo -e "${GREEN}✅ Backend and UIs stopped${NC}"
    echo -e "${BLUE}💡 Database is still running. To stop it, run: docker-compose down${NC}"
    exit 0
}

# Trap Ctrl+C (SIGINT) and SIGTERM to run cleanup
trap cleanup SIGINT SIGTERM EXIT

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

# 3. Start Student UI
echo -e "${GREEN}🎨 Starting student UI (ui_user)...${NC}"
cd ui_user

echo -e "${YELLOW}📥 Installing ui_user dependencies...${NC}"
npm install

npm run dev > ../ui-user.log 2>&1 &
USER_UI_PID=$!
cd ..
echo -e "${GREEN}✅ Student UI started (PID: $USER_UI_PID)${NC}\n"

# 4. Start Admin UI
echo -e "${GREEN}🛠️  Starting admin UI (ui_admin)...${NC}"
cd ui_admin

echo -e "${YELLOW}📥 Installing ui_admin dependencies...${NC}"
npm install

npm run dev > ../ui-admin.log 2>&1 &
ADMIN_UI_PID=$!
cd ..
echo -e "${GREEN}✅ Admin UI started (PID: $ADMIN_UI_PID)${NC}\n"

# Wait a moment for servers to start
sleep 3

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ All services started successfully!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "\n📍 Services:"
echo -e "   🗄️  Database:  http://localhost:5432"
echo -e "   🔧 Backend:    http://localhost:8000"
echo -e "   📚 API Docs:   http://localhost:8000/docs"
echo -e "   🎨 Student UI:  http://localhost:3000"
echo -e "   🛠️  Admin UI:    http://localhost:3001"
echo -e "\n📋 Logs:"
echo -e "   Backend:   tail -f backend.log"
echo -e "   Student:   tail -f ui-user.log"
echo -e "   Admin:     tail -f ui-admin.log"
echo -e "\n${YELLOW}Press Ctrl+C to stop all services${NC}\n"

# Keep script running and wait for processes
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Services are running. View logs with:${NC}"
echo -e "   Backend:   tail -f backend.log"
echo -e "   Student:   tail -f ui-user.log"
echo -e "   Admin:     tail -f ui-admin.log"
echo -e "\n${YELLOW}Or open logs in separate terminals:${NC}"
echo -e "   Terminal 1: tail -f backend.log"
echo -e "   Terminal 2: tail -f ui-user.log"
echo -e "   Terminal 3: tail -f ui-admin.log"
echo -e "\n${RED}Press Ctrl+C to stop all services${NC}\n"

# Wait for background processes (will be interrupted by trap on Ctrl+C)
wait $BACKEND_PID $USER_UI_PID $ADMIN_UI_PID 2>/dev/null || true
