#!/bin/bash
# ============================================================================
# Django Deployment Script for Hetzner
# ============================================================================
# This script deploys the latest code to production
# Run as: bash deploy.sh
# ============================================================================

set -e  # Exit on error

# Configuration
APP_DIR="/var/www/smartcamera"
DJANGO_DIR="$APP_DIR/django-webapp"
VENV_DIR="$DJANGO_DIR/venv"
REPO_URL="https://github.com/yourusername/esp32-cam-product.git"  # Update with your repo
BRANCH="main"  # Change to your default branch

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=========================================="
echo "Smart Camera Deployment"
echo "==========================================${NC}"

# Check if running as correct user
if [ "$EUID" -eq 0 ]; then 
    echo -e "${RED}Error: Do not run this script as root. Run as the application user.${NC}"
    exit 1
fi

# ============================================================================
# Step 1: Navigate to application directory
# ============================================================================
echo -e "${YELLOW}Step 1: Navigating to application directory...${NC}"
cd $DJANGO_DIR || {
    echo -e "${RED}Error: Application directory not found: $DJANGO_DIR${NC}"
    echo "Please run setup.sh first or clone the repository."
    exit 1
}

# ============================================================================
# Step 2: Pull latest code
# ============================================================================
echo -e "${YELLOW}Step 2: Pulling latest code from repository...${NC}"
if [ -d ".git" ]; then
    git fetch origin
    git reset --hard origin/$BRANCH
    git clean -fd
    echo -e "${GREEN}✓ Code updated${NC}"
else
    echo -e "${YELLOW}Warning: Not a git repository. Skipping git pull.${NC}"
fi

# ============================================================================
# Step 3: Activate virtual environment
# ============================================================================
echo -e "${YELLOW}Step 3: Activating virtual environment...${NC}"
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3.11 -m venv $VENV_DIR
fi

source $VENV_DIR/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# ============================================================================
# Step 4: Install/update dependencies
# ============================================================================
echo -e "${YELLOW}Step 4: Installing/updating Python dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# ============================================================================
# Step 5: Check environment file
# ============================================================================
echo -e "${YELLOW}Step 5: Checking environment configuration...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo "Please create .env file from .env.example"
    exit 1
fi
echo -e "${GREEN}✓ Environment file found${NC}"

# ============================================================================
# Step 6: Run database migrations
# ============================================================================
echo -e "${YELLOW}Step 6: Running database migrations...${NC}"
python manage.py migrate --noinput
echo -e "${GREEN}✓ Migrations completed${NC}"

# ============================================================================
# Step 7: Collect static files
# ============================================================================
echo -e "${YELLOW}Step 7: Collecting static files...${NC}"
python manage.py collectstatic --noinput --clear
echo -e "${GREEN}✓ Static files collected${NC}"

# ============================================================================
# Step 8: Create necessary directories
# ============================================================================
echo -e "${YELLOW}Step 8: Creating necessary directories...${NC}"
mkdir -p media
mkdir -p logs
mkdir -p staticfiles
echo -e "${GREEN}✓ Directories created${NC}"

# ============================================================================
# Step 9: Restart services
# ============================================================================
echo -e "${YELLOW}Step 9: Restarting services...${NC}"

# Restart Django service
if systemctl is-active --quiet django.service; then
    echo "Restarting Django service..."
    sudo systemctl restart django.service
    echo -e "${GREEN}✓ Django service restarted${NC}"
else
    echo -e "${YELLOW}Django service not running. Starting...${NC}"
    sudo systemctl start django.service
    sudo systemctl enable django.service
    echo -e "${GREEN}✓ Django service started${NC}"
fi

# Restart Daphne service (for WebSockets)
if systemctl is-active --quiet daphne.service; then
    echo "Restarting Daphne service..."
    sudo systemctl restart daphne.service
    echo -e "${GREEN}✓ Daphne service restarted${NC}"
else
    echo -e "${YELLOW}Daphne service not running. Starting...${NC}"
    sudo systemctl start daphne.service
    sudo systemctl enable daphne.service
    echo -e "${GREEN}✓ Daphne service started${NC}"
fi

# Reload Nginx
echo "Reloading Nginx..."
sudo systemctl reload nginx
echo -e "${GREEN}✓ Nginx reloaded${NC}"

# ============================================================================
# Step 10: Check service status
# ============================================================================
echo -e "${YELLOW}Step 10: Checking service status...${NC}"
sleep 2

if systemctl is-active --quiet django.service; then
    echo -e "${GREEN}✓ Django service is running${NC}"
else
    echo -e "${RED}✗ Django service is not running!${NC}"
    echo "Check logs: sudo journalctl -u django.service -n 50"
fi

if systemctl is-active --quiet daphne.service; then
    echo -e "${GREEN}✓ Daphne service is running${NC}"
else
    echo -e "${RED}✗ Daphne service is not running!${NC}"
    echo "Check logs: sudo journalctl -u daphne.service -n 50"
fi

if systemctl is-active --quiet nginx.service; then
    echo -e "${GREEN}✓ Nginx service is running${NC}"
else
    echo -e "${RED}✗ Nginx service is not running!${NC}"
    echo "Check logs: sudo journalctl -u nginx.service -n 50"
fi

# ============================================================================
# Summary
# ============================================================================
echo ""
echo -e "${GREEN}=========================================="
echo "Deployment Complete!"
echo "==========================================${NC}"
echo ""
echo "Services status:"
systemctl is-active django.service && echo "  ✓ Django (Gunicorn)" || echo "  ✗ Django (Gunicorn)"
systemctl is-active daphne.service && echo "  ✓ Daphne (WebSocket)" || echo "  ✗ Daphne (WebSocket)"
systemctl is-active nginx.service && echo "  ✓ Nginx" || echo "  ✗ Nginx"
echo ""
echo "Useful commands:"
echo "  View Django logs: sudo journalctl -u django.service -f"
echo "  View Daphne logs: sudo journalctl -u daphne.service -f"
echo "  View Nginx logs: sudo tail -f /var/log/nginx/smartcamera-error.log"
echo "  Restart all: sudo systemctl restart django.service daphne.service && sudo systemctl reload nginx"
echo ""







