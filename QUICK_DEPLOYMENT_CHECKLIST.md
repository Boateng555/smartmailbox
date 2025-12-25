# Quick Deployment Checklist

## Pre-Deployment

- [ ] All code changes committed
- [ ] `.gitignore` file created
- [ ] Server IP updated in ESP32 firmware (`194.164.59.137`)
- [ ] Environment variables documented
- [ ] Database backup plan ready

## GitHub Setup

- [ ] GitHub repository created
- [ ] Code pushed to GitHub
- [ ] Repository is accessible

## Server Setup

- [ ] Server access (SSH) configured
- [ ] Python 3.9+ installed
- [ ] PostgreSQL/MySQL installed
- [ ] Nginx installed
- [ ] Supervisor installed
- [ ] Repository cloned to server
- [ ] Virtual environment created
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Environment variables configured (`.env` file)
- [ ] Database created and configured
- [ ] Migrations run (`python manage.py migrate`)
- [ ] Superuser created (`python manage.py createsuperuser`)
- [ ] Static files collected (`python manage.py collectstatic`)
- [ ] Supervisor configured and running
- [ ] Nginx configured and running
- [ ] Firewall rules configured
- [ ] SSL certificate installed (optional)

## ESP32-CAM Setup

- [ ] ESP32-CAM hardware connected
- [ ] PlatformIO/Arduino IDE ready
- [ ] WiFi credentials configured in firmware
- [ ] Server IP set to `194.164.59.137`
- [ ] Firmware compiled successfully
- [ ] Firmware uploaded to ESP32-CAM
- [ ] Serial monitor shows no errors

## Testing

- [ ] Server accessible via browser
- [ ] Django admin accessible
- [ ] API endpoints responding
- [ ] ESP32 connects to WiFi
- [ ] ESP32 uploads photos successfully
- [ ] Manual trigger button works
- [ ] Click limits enforced (Free: 3, Premium: 10)
- [ ] ChatGPT analysis working
- [ ] Notifications sent correctly
- [ ] Dashboard displays captures
- [ ] WebSocket connections working

## Post-Deployment

- [ ] Logs monitored for errors
- [ ] Performance checked
- [ ] Backup system configured
- [ ] Monitoring alerts set up
- [ ] Documentation updated
- [ ] Team notified of deployment

## Rollback Plan

- [ ] Previous version tagged in Git
- [ ] Database backup available
- [ ] Rollback procedure documented

## Success Criteria

✅ ESP32 wakes every 2 hours automatically
✅ Manual trigger works via app button
✅ Photos upload successfully
✅ ChatGPT analyzes images correctly
✅ Users receive notifications
✅ Click limits enforced properly
✅ Web app displays all data correctly

---

**Deployment Date:** _______________
**Deployed By:** _______________
**Server IP:** 194.164.59.137
**Status:** ☐ In Progress ☐ Complete ☐ Failed

