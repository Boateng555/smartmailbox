#!/bin/bash
# Firewall Configuration Script

set -e

echo "Configuring firewall..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Detect firewall type
if command -v ufw &> /dev/null; then
    echo "Using UFW firewall..."
    
    # Reset UFW to defaults
    ufw --force reset
    
    # Set default policies
    ufw default deny incoming
    ufw default allow outgoing
    
    # Allow SSH (important - don't lock yourself out!)
    ufw allow 22/tcp comment 'SSH'
    
    # Allow HTTP and HTTPS
    ufw allow 80/tcp comment 'HTTP'
    ufw allow 443/tcp comment 'HTTPS'
    
    # Allow port 8000 for development (optional)
    read -p "Allow port 8000 for development? (y/n): " allow_dev
    if [ "$allow_dev" = "y" ]; then
        ufw allow 8000/tcp comment 'Development'
    fi
    
    # Enable firewall
    ufw --force enable
    
    # Show status
    ufw status verbose
    
elif command -v firewall-cmd &> /dev/null; then
    echo "Using firewalld..."
    
    # Start and enable firewalld
    systemctl start firewalld
    systemctl enable firewalld
    
    # Allow services
    firewall-cmd --permanent --add-service=http
    firewall-cmd --permanent --add-service=https
    firewall-cmd --permanent --add-service=ssh
    
    # Allow port 8000 for development (optional)
    read -p "Allow port 8000 for development? (y/n): " allow_dev
    if [ "$allow_dev" = "y" ]; then
        firewall-cmd --permanent --add-port=8000/tcp
    fi
    
    # Reload firewall
    firewall-cmd --reload
    
    # Show status
    firewall-cmd --list-all
    
else
    echo "No supported firewall found (ufw or firewalld)"
    echo "Please configure your firewall manually:"
    echo "  - Allow port 80 (HTTP)"
    echo "  - Allow port 443 (HTTPS)"
    echo "  - Allow port 22 (SSH)"
    echo "  - Optionally allow port 8000 (Development)"
    exit 1
fi

echo ""
echo "Firewall configured successfully!"
echo ""
echo "Allowed ports:"
echo "  - 22 (SSH)"
echo "  - 80 (HTTP)"
echo "  - 443 (HTTPS)"
if [ "$allow_dev" = "y" ]; then
    echo "  - 8000 (Development)"
fi







