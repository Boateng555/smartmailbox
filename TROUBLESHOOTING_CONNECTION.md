# Troubleshooting Connection Refused Error

## Problem
`ERR_CONNECTION_REFUSED` when accessing `http://194.164.59.137:8000`

## Solutions

### 1. Check if Server is Running

On your server, run:
```bash
ps aux | grep manage.py
```

If nothing shows, the server is not running. Start it:
```bash
cd /var/www/smartmailbox/django-webapp
source venv/bin/activate
python3 manage.py runserver 0.0.0.0:8000
```

### 2. Check Firewall

Ubuntu firewall might be blocking port 8000:

```bash
# Check firewall status
sudo ufw status

# Allow port 8000
sudo ufw allow 8000/tcp

# Or allow all HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

### 3. Check if Port is Listening

```bash
# Check if port 8000 is listening
sudo netstat -tlnp | grep 8000
# Or
sudo ss -tlnp | grep 8000
```

### 4. Check Server Logs

Look at the terminal where you ran `runserver` - are there any errors?

### 5. Test Locally on Server

```bash
# On the server itself, test:
curl http://localhost:8000
# Or
curl http://127.0.0.1:8000
```

If this works but external access doesn't, it's a firewall issue.

### 6. Check Cloud Provider Firewall

If using a cloud provider (Hetzner, AWS, DigitalOcean, etc.):
- Check the provider's firewall/security group settings
- Ensure port 8000 (or 80/443) is open in the cloud console

### 7. Run Server in Background (Optional)

If you want to keep server running after closing terminal:
```bash
cd /var/www/smartmailbox/django-webapp
source venv/bin/activate
nohup python3 manage.py runserver 0.0.0.0:8000 > server.log 2>&1 &
```

Check if running:
```bash
ps aux | grep manage.py
```

View logs:
```bash
tail -f /var/www/smartmailbox/django-webapp/server.log
```

## Quick Fix Commands

Run these on your server:

```bash
# 1. Allow firewall
sudo ufw allow 8000/tcp
sudo ufw reload

# 2. Start server (if not running)
cd /var/www/smartmailbox/django-webapp
source venv/bin/activate
python3 manage.py runserver 0.0.0.0:8000
```

## For Production

For production, you should:
1. Use port 80 (HTTP) or 443 (HTTPS)
2. Setup Nginx as reverse proxy
3. Use Gunicorn instead of development server
4. Setup Supervisor to keep it running

See `DEPLOYMENT_GUIDE.md` for production setup.

