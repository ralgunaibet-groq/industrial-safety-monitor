#!/bin/bash

# Google Cloud Run Deployment Script
# Industrial Safety Monitor

set -e

echo "🚀 Deploying Industrial Safety Monitor to Google Cloud Run..."
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="industrial-safety-monitor"
SERVICE_NAME="industrial-safety-monitor"
REGION="us-central1"
MEMORY="2Gi"
CPU="2"
TIMEOUT="300"
MAX_INSTANCES="10"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found!${NC}"
    echo "Install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

echo -e "${BLUE}📋 Configuration:${NC}"
echo "  Project ID: $PROJECT_ID"
echo "  Service: $SERVICE_NAME"
echo "  Region: $REGION"
echo "  Memory: $MEMORY"
echo "  CPU: $CPU"
echo ""

# Ask for confirmation
read -p "Deploy with these settings? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 0
fi

echo ""
echo -e "${BLUE}🔧 Setting up project...${NC}"

# Set project
gcloud config set project $PROJECT_ID 2>/dev/null || {
    echo -e "${RED}❌ Project not found. Creating new project...${NC}"
    gcloud projects create $PROJECT_ID --name="Industrial Safety Monitor"
    gcloud config set project $PROJECT_ID
}

echo -e "${GREEN}✅ Project set${NC}"
echo ""

# Enable APIs
echo -e "${BLUE}🔌 Enabling required APIs...${NC}"
gcloud services enable run.googleapis.com --quiet
gcloud services enable cloudbuild.googleapis.com --quiet
gcloud services enable containerregistry.googleapis.com --quiet
echo -e "${GREEN}✅ APIs enabled${NC}"
echo ""

# Deploy
echo -e "${BLUE}🚢 Deploying to Cloud Run...${NC}"
echo "This may take 3-5 minutes..."
echo ""

gcloud run deploy $SERVICE_NAME \
  --source . \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --port 8080 \
  --memory $MEMORY \
  --cpu $CPU \
  --timeout $TIMEOUT \
  --max-instances $MAX_INSTANCES \
  --quiet

echo ""
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --format 'value(status.url)')

echo -e "${GREEN}🎉 Your app is live!${NC}"
echo ""
echo -e "${BLUE}📱 Access your application:${NC}"
echo "  $SERVICE_URL"
echo ""
echo -e "${BLUE}📊 View logs:${NC}"
echo "  gcloud run services logs tail $SERVICE_NAME --region $REGION"
echo ""
echo -e "${BLUE}🔧 Update deployment:${NC}"
echo "  ./deploy-cloudrun.sh"
echo ""
echo -e "${BLUE}🛑 Delete service:${NC}"
echo "  gcloud run services delete $SERVICE_NAME --region $REGION"
echo ""
echo -e "${GREEN}Happy monitoring! 🏭${NC}"

