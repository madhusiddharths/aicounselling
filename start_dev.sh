#!/bin/bash

# ANSI colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}   🚀 AI-Counselling Local Development Starter    ${NC}"
echo -e "${BLUE}==================================================${NC}"

# 1. Setup Python Environment
if [ ! -d ".venv" ]; then
    echo -e "\n${YELLOW}📦 Creating Python virtual environment...${NC}"
    python3 -m venv .venv
    source .venv/bin/activate

    echo -e "${YELLOW}⬇️  Installing Python dependencies... (this may take a while)${NC}"
    pip install -r requirements.txt
else
    echo -e "\n${GREEN}✓ Virtual environment found${NC}"
    source .venv/bin/activate
fi

# 2. Check for node_modules
if [ ! -d "node_modules" ]; then
    echo -e "\n${YELLOW}📦 Installing Node.js dependencies...${NC}"
    npm install
fi

# Function to kill all processes on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down servers...${NC}"
    kill $(jobs -p) 2>/dev/null
    exit
}
trap cleanup SIGINT SIGTERM

# 3. Start Backend
echo -e "\n${GREEN}🐍 Starting Backend Server (Port 8000)...${NC}"
python backend/main.py &
BACKEND_PID=$!

# Wait a moment for backend to initialize
sleep 3

# 4. Start Frontend
echo -e "\n${GREEN}⚛️  Starting Frontend Server (Port 3000)...${NC}"
npm run dev &

# Wait for both
wait

