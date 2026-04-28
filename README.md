
# English 🇬🇧

## 🚀 Quick Start (English)
Link to Frontend: https://github.com/fReEsPiRiT-Spiritsoft/videoflix_frontend
### Prerequisites

- **Docker** & **Docker Compose** installed ([Installation](https://docs.docker.com/compose/install/))
- **Git** installed ([Installation](https://git-scm.com/downloads))

### Installation in 3 Steps

1. **Clone repository**
   ```bash
   git clone <repository-url>
   cd videoflix
   ```

2. **Configure environment variables**
   ```bash
   cp .env.template .env
   ```
   
   Adjust the `.env` file with your values (see [Configuration](#️-configuration)).

3. **Start Docker containers**
   ```bash
   docker compose up --build
   ```

✅ **Done!** The application runs on [http://localhost:8000](http://localhost:8000)

---

##  What is Videoflix?

Videoflix is a **complete video streaming backend** based on Django, utilizing modern web technologies for professional video hosting.

### Technology Stack

- **Backend**: Django 6.0.4 + Django REST Framework
- **Database**: PostgreSQL (containerized)
- **Cache & Queue**: Redis + Django-RQ
- **Video Processing**: FFmpeg (HLS with Adaptive Bitrate Streaming)
- **Authentication**: JWT with HttpOnly Cookies (djangorestframework-simplejwt)
- **CORS**: django-cors-headers for Cross-Origin Requests
- **Server**: Gunicorn WSGI Server
- **Container**: Docker + Docker Compose

---

##  Features

###  Video Features
- **Adaptive Bitrate Streaming (ABR)**: Automatic conversion to 480p, 720p, 1080p
- **HLS Format**: HTTP Live Streaming with .m3u8 playlists
- **Automatic Thumbnails**: Generated from middle frame
- **Asynchronous Processing**: Background video processing via Redis Queue

###  Authentication
- **JWT-based Auth**: Secure tokens in HttpOnly Cookies
- **Email Activation**: Account confirmation via email
- **Password Reset**: Secure password recovery
- **CORS Support**: Cross-Origin Requests for frontend integration

###  Admin & Management
- **Auto-Superuser**: Automatic admin creation on startup
- **Database Cleanup**: Management command for database cleanup
- **Static Files**: WhiteNoise for optimized static file serving
- **Docker Ready**: Fully containerized with Docker Compose

---

##  Usage

### Database Migrations

**Execute in running container:**
```bash
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
```

### Install New Packages

1. Add package to `requirements.txt`
2. Rebuild container:
   ```bash
   docker compose up --build
   ```

### Admin Panel

Access Django Admin Panel: [http://localhost:8000/admin](http://localhost:8000/admin)

**Login credentials** (from `.env`):
- Username: `admin` (or `DJANGO_SUPERUSER_USERNAME`)
- Password: `adminpassword` (or `DJANGO_SUPERUSER_PASSWORD`)

### Upload Videos

1. Login to Admin Panel
2. Navigate to "Videos"
3. Upload video → automatic processing starts
4. Check status in Redis Queue: [http://localhost:8000/django-rq/](http://localhost:8000/django-rq/)

---

## ⚙️ Configuration

### Environment Variables (.env)

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| **DJANGO_SUPERUSER_USERNAME** | Admin username | `admin` | ✅ |
| **DJANGO_SUPERUSER_PASSWORD** | Admin password | `adminpassword` | ✅ |
| **DJANGO_SUPERUSER_EMAIL** | Admin email | `admin@example.com` | ✅ |
| **SECRET_KEY** | Django Secret Key | - | ✅ |
| **DEBUG** | Debug mode | `True` | ❌ |
| **ALLOWED_HOSTS** | Allowed hosts (comma-separated) | `localhost,127.0.0.1` | ✅ |
| **CSRF_TRUSTED_ORIGINS** | CSRF trusted origins | `http://localhost:5500,...` | ✅ |
| **CORS_ALLOWED_ORIGINS** | CORS allowed origins | `http://localhost:5500,...` | ✅ |
| **DB_NAME** | Database name | `your_database_name` | ✅ |
| **DB_USER** | Database user | `your_database_user` | ✅ |
| **DB_PASSWORD** | Database password | `your_database_password` | ✅ |
| **DB_HOST** | Database host | `db` | ❌ |
| **DB_PORT** | Database port | `5432` | ❌ |
| **REDIS_HOST** | Redis host | `redis` | ❌ |
| **REDIS_PORT** | Redis port | `6379` | ❌ |
| **EMAIL_HOST** | SMTP server | `smtp.example.com` | ✅ |
| **EMAIL_PORT** | SMTP port | `587` | ❌ |
| **EMAIL_USE_TLS** | Use TLS | `True` | ❌ |
| **EMAIL_USE_SSL** | Use SSL | `False` | ❌ |
| **EMAIL_HOST_USER** | Email username | - | ✅ |
| **EMAIL_HOST_PASSWORD** | Email password | - | ✅ |
| **DEFAULT_FROM_EMAIL** | Sender email | `EMAIL_HOST_USER` | ❌ |

> ** IMPORTANT for Production:**
> - Set `DEBUG=False`
> - Generate strong `SECRET_KEY`
> - Configure `ALLOWED_HOSTS` with real domain
> - Use HTTPS URLs in `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS`

---

##  Troubleshooting

### Docker won't start

**Error**: `unable to get image 'postgres:latest'`

**Solution**: Start Docker Desktop

---

### Entrypoint Error

**Error**: `exec ./backend.entrypoint.sh: no such file or directory`

**Solution**: Set line endings to `LF` (not `CRLF`)
```bash
# In VS Code: Click "CRLF" at bottom right → Select "LF"
```

---

### Migration fails

**Error**: Database migration failed after model changes

**Solution**: Execute migration in container
```bash
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
```

---

### Port 8000 already in use

**Error**: `port is already allocated`

**Solution**: Stop other process or change port
```bash
# Find port conflict
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Or change port in docker-compose.yml
ports:
  - "8001:8000"  # Host:Container
```

---

##  License / Lizenz

This project is licensed under the MIT License.

Dieses Projekt ist unter der MIT-Lizenz lizenziert.
