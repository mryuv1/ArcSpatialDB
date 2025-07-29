# ArcSpatialDB Deployment Guide

This guide explains how to deploy the ArcSpatialDB Flask application on a VM and configure the ArcGIS Pro plugin to communicate with it via API.

## Prerequisites

- Python 3.7+ installed on the VM
- Network access to the VM from ArcGIS Pro machines
- Firewall configured to allow HTTP traffic on port 5000 (or your chosen port)

## 1. VM Setup

### Install Python Dependencies

**Good news!** All required libraries are already available in your environment:
- ✅ `flask` - Web framework
- ✅ `sqlalchemy` - Database ORM  
- ✅ `requests` - HTTP client
- ✅ `glob2` - File pattern matching

**No additional installation needed!** The application will work with your existing environment.

If you want to use Gunicorn for production deployment (optional):
```bash
pip install gunicorn
```

### Configure the Application

1. **Update `config.py`** with your VM's settings:

```python
# Replace with your VM's actual IP or domain
API_BASE_URL = "http://your-vm-ip:5000"  # e.g., "http://192.168.1.100:5000"
API_TIMEOUT = 30

# Flask settings for production
FLASK_HOST = "0.0.0.0"  # Allow external connections
FLASK_PORT = 5000
FLASK_DEBUG = False  # Important: Set to False in production
```

2. **Create the database** (if it doesn't exist):
   - The database will be created automatically when the app first runs
   - The app now includes automatic database initialization and sample data creation
   - Or run `python generate_sample_db.py` to create a sample database
   - Or run `python test_db_init.py` to test the database initialization

## 2. Deploy the Flask App

### Option A: Direct Python Execution

```bash
# Navigate to the project directory
cd /path/to/ArcSpatialDB

# Run the Flask app
python app.py
```

### Option B: Using Waitress (Recommended for Windows/Linux Production)

```bash
# Install Waitress (if not already available)
pip install waitress

# Run with Waitress
python server.py
```

### Option C: Using Gunicorn (Recommended for Linux Production)

```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Option C: Using Systemd Service

Create a systemd service file `/etc/systemd/system/arcspatialdb.service`:

```ini
[Unit]
Description=ArcSpatialDB Flask Application
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/ArcSpatialDB
Environment=PATH=/path/to/your/python/environment/bin
ExecStart=/path/to/your/python/environment/bin/python server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl enable arcspatialdb
sudo systemctl start arcspatialdb
sudo systemctl status arcspatialdb
```

## 3. Configure Firewall

### Ubuntu/Debian (ufw)
```bash
sudo ufw allow 5000
sudo ufw enable
```

### CentOS/RHEL (firewalld)
```bash
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload
```

### Windows
- Open Windows Defender Firewall
- Add inbound rule for port 5000

## 4. Test the API

Run the test script to verify the API is working:

```bash
# Update the API_BASE_URL in test_api.py first
python test_api.py
```

Expected output:
```
🚀 Starting ArcSpatialDB API Tests
API Base URL: http://your-vm-ip:5000
==================================================
🧪 Testing API: Add Project
Status Code: 201
Response: {'message': 'Project added successfully', 'uuid': 'abc12345'}
✅ Project added successfully!
...
```

## 5. Configure ArcGIS Pro Plugin

### Update db_manager.pyt

1. **Verify requests library** in ArcGIS Pro's Python environment:
   ```bash
   # Check if requests is available (it should be in your list)
   C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe -c "import requests; print('requests is available')"
   ```
   
   If requests is not available, install it:
   ```bash
   C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe -m pip install requests
   ```

2. **Update the API URL** in `db_manager.pyt`:
   - The plugin will automatically use the `config.py` file if available
   - Or update the fallback URL in the `commit_to_the_db` function

3. **Test the plugin**:
   - Open ArcGIS Pro
   - Load the `db_manager.pyt` toolbox
   - Run the "Export Layout With ID" tool
   - Check the output messages for API communication status

## 6. Network Configuration

### For Local Network Deployment

If your VM is on the same network as ArcGIS Pro machines:

1. **Find your VM's IP address**:
   ```bash
   # Linux
   ip addr show
   
   # Windows
   ipconfig
   ```

2. **Update config.py** with the VM's IP:
   ```python
   API_BASE_URL = "http://192.168.1.100:5000"  # Replace with actual IP
   ```

### For Internet Deployment

If deploying to a cloud VM or public server:

1. **Configure domain name** (optional but recommended)
2. **Set up HTTPS** using a reverse proxy (nginx/Apache) with SSL certificates
3. **Update firewall rules** for your cloud provider
4. **Update config.py** with your domain:
   ```python
   API_BASE_URL = "https://yourdomain.com"
   ```

## 7. Monitoring and Logs

### Check Application Status

```bash
# If using systemd
sudo systemctl status arcspatialdb

# Check logs
sudo journalctl -u arcspatialdb -f

# If running directly
tail -f /path/to/ArcSpatialDB/app.log
```

### Monitor API Requests

The Flask app will log all API requests. Check the console output or logs for:
- Successful project additions
- API errors
- Network connectivity issues

## 8. Troubleshooting

### Common Issues

1. **Connection Refused**:
   - Check if Flask app is running
   - Verify firewall settings
   - Confirm port 5000 is open

2. **API Timeout**:
   - Increase `API_TIMEOUT` in config.py
   - Check network connectivity
   - Verify VM resources (CPU/memory)

3. **Database Errors**:
   - Ensure database file is writable
   - Check disk space
   - Verify SQLite permissions

4. **ArcGIS Pro Plugin Issues**:
   - Install requests library in ArcGIS Pro environment
   - Check Python path in ArcGIS Pro
   - Verify API URL is accessible from ArcGIS Pro machine

5. **Database Initialization Issues**:
   - The app now automatically creates the database and tables if they don't exist
   - If you encounter database errors, run `python test_db_init.py` to verify initialization
   - The app will create sample data if the database is completely empty
   - Check console output for database initialization messages

### Debug Mode

For troubleshooting, temporarily enable debug mode:

```python
# In config.py
FLASK_DEBUG = True
```

**Remember to disable debug mode in production!**

## 9. Security Considerations

1. **Use HTTPS** in production
2. **Implement authentication** if needed
3. **Restrict network access** to trusted IPs
4. **Regular security updates**
5. **Backup database** regularly

## 10. Backup and Maintenance

### Database Backup

```bash
# Create backup
cp elements.db elements.db.backup.$(date +%Y%m%d)

# Or use SQLite backup
sqlite3 elements.db ".backup elements.db.backup"
```

### Log Rotation

Configure log rotation to prevent disk space issues:

```bash
# Add to /etc/logrotate.d/arcspatialdb
/path/to/ArcSpatialDB/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

---

For additional support, check the application logs and ensure all network connectivity is properly configured. 