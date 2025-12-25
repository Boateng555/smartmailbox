# Firewall Configuration Guide

## Overview
This guide covers configuring firewalls to allow necessary ports for the IoT Platform.

## Required Ports

- **Port 80 (HTTP)** - Required for Let's Encrypt certificate validation and redirects to HTTPS
- **Port 443 (HTTPS)** - Required for secure web access
- **Port 22 (SSH)** - Required for server administration
- **Port 8000 (Development)** - Optional, for direct Django access during development

## UFW (Ubuntu/Debian)

### Automatic Setup
```bash
sudo bash scripts/setup-firewall.sh
```

### Manual Setup
```bash
# Install UFW if not installed
sudo apt-get update
sudo apt-get install ufw

# Set default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (IMPORTANT - do this first!)
sudo ufw allow 22/tcp comment 'SSH'

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp comment 'HTTP'
sudo ufw allow 443/tcp comment 'HTTPS'

# Optional: Allow development port
sudo ufw allow 8000/tcp comment 'Development'

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status verbose
```

## Firewalld (CentOS/RHEL)

### Automatic Setup
```bash
sudo bash scripts/setup-firewall.sh
```

### Manual Setup
```bash
# Start and enable firewalld
sudo systemctl start firewalld
sudo systemctl enable firewalld

# Allow services
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-service=ssh

# Optional: Allow development port
sudo firewall-cmd --permanent --add-port=8000/tcp

# Reload firewall
sudo firewall-cmd --reload

# Check status
sudo firewall-cmd --list-all
```

## iptables (Generic Linux)

```bash
# Allow SSH
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Allow HTTP
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT

# Allow HTTPS
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Optional: Allow development port
sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT

# Set default policy
sudo iptables -P INPUT DROP
sudo iptables -P FORWARD DROP
sudo iptables -P OUTPUT ACCEPT

# Save rules (Ubuntu/Debian)
sudo iptables-save > /etc/iptables/rules.v4

# Save rules (CentOS/RHEL)
sudo service iptables save
```

## Cloud Provider Firewalls

### AWS Security Groups
1. Go to EC2 → Security Groups
2. Create/Edit security group
3. Add inbound rules:
   - Type: HTTP, Port: 80, Source: 0.0.0.0/0
   - Type: HTTPS, Port: 443, Source: 0.0.0.0/0
   - Type: SSH, Port: 22, Source: Your IP
   - Type: Custom TCP, Port: 8000, Source: Your IP (optional)

### Google Cloud Platform
1. Go to VPC Network → Firewall Rules
2. Create rules for:
   - HTTP (port 80)
   - HTTPS (port 443)
   - SSH (port 22)
   - Custom (port 8000, optional)

### Azure Network Security Groups
1. Go to Network Security Groups
2. Add inbound security rules:
   - HTTP (80)
   - HTTPS (443)
   - SSH (22)
   - Custom (8000, optional)

## Testing Firewall Configuration

```bash
# Test HTTP
curl -I http://your-server-ip

# Test HTTPS
curl -I https://your-server-ip

# Test from external location
# Use online tools like https://www.yougetsignal.com/tools/open-ports/
```

## Security Best Practices

1. **Always allow SSH first** - Don't lock yourself out!
2. **Restrict SSH access** - Only allow from trusted IPs if possible
3. **Use fail2ban** - Protect against brute force attacks
4. **Regular updates** - Keep firewall rules and software updated
5. **Monitor logs** - Check firewall logs regularly for suspicious activity

## Troubleshooting

### Can't access website
- Check firewall status: `sudo ufw status` or `sudo firewall-cmd --list-all`
- Verify ports are open: `sudo netstat -tulpn | grep -E '80|443'`
- Check nginx is running: `docker-compose ps nginx`

### Can't SSH into server
- Verify SSH port is allowed
- Check SSH service: `sudo systemctl status ssh`
- Verify from another location

### Let's Encrypt certificate fails
- Ensure port 80 is open and accessible
- Check domain DNS points to server
- Verify nginx is running and accessible







