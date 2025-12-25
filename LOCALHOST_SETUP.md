# How to Run Django Server on Localhost

## Quick Start

### 1. Navigate to Django Project Directory

```bash
cd django-webapp
```

### 2. Create Virtual Environment (if not already created)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run Database Migrations

```bash
python manage.py migrate
```

### 5. Create Superuser (Optional - for admin access)

```bash
python manage.py createsuperuser
```

### 6. Run Development Server

```bash
python manage.py runserver
```

### 7. Open in Browser

Once the server is running, open your browser and go to:

**Main Application:**
```
http://localhost:8000
```

**Admin Panel:**
```
http://localhost:8000/admin
```

**API Endpoints:**
```
http://localhost:8000/api/device/capture/
http://localhost:8000/api/device/trigger/
http://localhost:8000/api/device/status/
```

## Complete Setup Commands (Copy & Paste)

### Windows (PowerShell)
```powershell
cd django-webapp
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Mac/Linux
```bash
cd django-webapp
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## What You'll See

When the server starts successfully, you'll see:

```
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

## Troubleshooting

### Port Already in Use

If port 8000 is already in use, use a different port:

```bash
python manage.py runserver 8001
```

Then access at: `http://localhost:8001`

### Module Not Found Errors

Make sure you:
1. Created and activated the virtual environment
2. Installed all requirements: `pip install -r requirements.txt`

### Database Errors

Run migrations:
```bash
python manage.py migrate
```

### Permission Errors

On Mac/Linux, you might need:
```bash
chmod +x manage.py
```

## Using Docker (Alternative)

If you prefer Docker:

```bash
cd django-webapp
docker-compose up
```

Then access at: `http://localhost:8000`

## Default URLs

- **Home**: http://localhost:8000/
- **Admin**: http://localhost:8000/admin/
- **API Capture**: http://localhost:8000/api/device/capture/
- **API Trigger**: http://localhost:8000/api/device/trigger/
- **API Status**: http://localhost:8000/api/device/status/

## Next Steps

1. **Access the web interface** at http://localhost:8000
2. **Login** (if you created a superuser)
3. **Test API endpoints** using Postman or curl
4. **Configure ESP32** to point to `localhost:8000` (or your local IP)

## Note for ESP32 Testing

If you want to test with ESP32-CAM:
- Use your computer's local IP address instead of `localhost`
- Find your IP: 
  - Windows: `ipconfig` (look for IPv4 Address)
  - Mac/Linux: `ifconfig` or `ip addr`
- Example: `http://192.168.1.100:8000`

## Stop the Server

Press `CTRL+C` in the terminal to stop the development server.


