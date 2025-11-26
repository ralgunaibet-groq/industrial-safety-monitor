#!/bin/bash

# Deploy Industrial Safety Monitor with ngrok
# Full features including webcam access

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🏭 Industrial Safety Monitor - ngrok Deployment${NC}"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found!${NC}"
    echo "Install Python from: https://www.python.org/downloads/"
    exit 1
fi

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo -e "${YELLOW}⚠️  ngrok not found. Installing...${NC}"
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install ngrok
        else
            echo -e "${RED}❌ Homebrew not found. Install ngrok manually:${NC}"
            echo "  https://ngrok.com/download"
            exit 1
        fi
    else
        echo -e "${RED}❌ Please install ngrok manually:${NC}"
        echo "  https://ngrok.com/download"
        exit 1
    fi
fi

echo -e "${GREEN}✅ Prerequisites met${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${BLUE}📦 Creating virtual environment...${NC}"
    python3 -m venv .venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}🔧 Activating virtual environment...${NC}"
source .venv/bin/activate

# Install dependencies
echo -e "${BLUE}📥 Installing dependencies...${NC}"
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Check ngrok auth token
echo -e "${YELLOW}🔑 Checking ngrok authentication...${NC}"
if ! ngrok config check &> /dev/null; then
    echo ""
    echo -e "${YELLOW}⚠️  ngrok auth token not configured${NC}"
    echo ""
    echo "To get your auth token:"
    echo "  1. Go to https://dashboard.ngrok.com/get-started/your-authtoken"
    echo "  2. Sign up (free)"
    echo "  3. Copy your auth token"
    echo ""
    read -p "Enter your ngrok auth token (or press Enter to skip): " AUTH_TOKEN
    
    if [ ! -z "$AUTH_TOKEN" ]; then
        ngrok config add-authtoken $AUTH_TOKEN
        echo -e "${GREEN}✅ Auth token configured${NC}"
    else
        echo -e "${YELLOW}⚠️  Continuing without auth token (limited to 2 hours)${NC}"
    fi
fi

echo ""
echo -e "${GREEN}🚀 Starting Industrial Safety Monitor...${NC}"
echo ""

# Start the app in background
python app.py &
APP_PID=$!

# Wait for app to start
echo "Waiting for app to start..."
sleep 3

# Check if app is running
if ! ps -p $APP_PID > /dev/null; then
    echo -e "${RED}❌ Failed to start app${NC}"
    exit 1
fi

echo -e "${GREEN}✅ App started (PID: $APP_PID)${NC}"
echo ""

# Start ngrok
echo -e "${BLUE}🌐 Starting ngrok tunnel...${NC}"
echo ""

ngrok http 8080 &
NGROK_PID=$!

# Wait for ngrok to start
sleep 2

echo ""
echo -e "${GREEN}🎉 Deployment complete!${NC}"
echo ""
echo -e "${BLUE}📱 Access your application:${NC}"
echo "  Local:    http://localhost:8080"
echo "  Public:   Check ngrok interface above for public URL"
echo ""
echo -e "${BLUE}🔧 Useful commands:${NC}"
echo "  View ngrok dashboard:  http://localhost:4040"
echo "  Stop services:         Press Ctrl+C"
echo ""
echo -e "${YELLOW}💡 Tip: Get a permanent URL with ngrok Pro ($8/month)${NC}"
echo ""

# Wait for user interrupt
trap "echo ''; echo 'Stopping services...'; kill $APP_PID $NGROK_PID 2>/dev/null; echo 'Done!'; exit 0" INT

# Keep script running
wait

