# Videoflix Backend 🎬

Ein professionelles Django-Backend für Video-Streaming mit adaptiver Bitrate (ABR), automatischer Thumbnail-Generierung und asynchroner Video-Verarbeitung.

---

Link zum passenden Frontend: https://github.com/fReEsPiRiT-Spiritsoft/videoflix_frontend


## 📋 Table of Contents / Inhaltsverzeichnis

### Deutsch
- [ Quick Start](#-quick-start-deutsch)
- [ Was ist Videoflix?](#-was-ist-videoflix)
- [ Features](#-features)
- [ Verwendung](#-verwendung)
- [ Konfiguration](#️-konfiguration)
- [ Troubleshooting](#-troubleshooting)

### English
- [ Quick Start](#-quick-start-english)
- [ What is Videoflix?](#-what-is-videoflix)
- [ Features](#-features-1)
- [ Usage](#-usage)
- [ Configuration](#️-configuration)
- [ Troubleshooting](#-troubleshooting-1)

---

# Deutsch 🇩🇪

## 🚀 Quick Start (Deutsch)

### Voraussetzungen

- **Docker** & **Docker Compose** installiert ([Installation](https://docs.docker.com/compose/install/))
- **Git** installiert ([Installation](https://git-scm.com/downloads))

### Installation in 3 Schritten

1. **Repository klonen**
   ```bash
   git clone <repository-url>
   cd videoflix
   ```

2. **Umgebungsvariablen konfigurieren**
   ```bash
   cp .env.template .env
   ```
   
   Passe die `.env` Datei mit deinen Werten an (siehe [Konfiguration](#️-konfiguration)).

3. **Docker Container starten**
   ```bash
   docker compose up --build
   ```


 **Fertig!** Die Anwendung läuft auf [http://localhost:8000](http://localhost:8000)

---

##  Was ist Videoflix?

Videoflix ist ein **vollständiges Video-Streaming-Backend** basierend auf Django, das moderne Web-Technologien für professionelles Video-Hosting nutzt.

### Technologie-Stack

- **Backend**: Django 6.0.4 + Django REST Framework
- **Datenbank**: PostgreSQL (containerisiert)
- **Cache & Queue**: Redis + Django-RQ
- **Video-Processing**: FFmpeg (HLS mit Adaptive Bitrate Streaming)
- **Authentication**: JWT mit HttpOnly Cookies (djangorestframework-simplejwt)
- **CORS**: django-cors-headers für Cross-Origin Requests
- **Server**: Gunicorn WSGI Server
- **Container**: Docker + Docker Compose

---

##  Features

###  Video-Funktionen
- **Adaptive Bitrate Streaming (ABR)**: Automatische Konvertierung in 480p, 720p, 1080p
- **HLS-Format**: HTTP Live Streaming mit .m3u8 Playlists
- **Automatische Thumbnails**: Generierung aus dem mittleren Frame
- **Asynchrone Verarbeitung**: Video-Processing im Hintergrund via Redis Queue

###  Authentifizierung
- **JWT-basierte Auth**: Secure tokens in HttpOnly Cookies
- **Email-Aktivierung**: Account-Bestätigung per E-Mail
- **Passwort-Reset**: Sichere Passwort-Wiederherstellung
- **CORS-Support**: Cross-Origin Requests für Frontend-Integration

###  Admin & Management
- **Auto-Superuser**: Automatische Admin-Erstellung beim Start
- **Database Cleanup**: Management-Command für Datenbankbereinigung
- **Static Files**: WhiteNoise für optimiertes Static-File-Serving
- **Docker Ready**: Vollständig containerisiert mit Docker Compose

---

##  Verwendung

### Datenbank-Migrationen

**Im laufenden Container ausführen:**
```bash
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
```

### Neue Pakete installieren

1. Paket zu `requirements.txt` hinzufügen
2. Container neu bauen:
   ```bash
   docker compose up --build
   ```

### Admin-Panel

Zugriff auf das Django Admin Panel: [http://localhost:8000/admin](http://localhost:8000/admin)

**Login-Daten** (aus `.env`):
- Username: `admin` (oder `DJANGO_SUPERUSER_USERNAME`)
- Password: `adminpassword` (oder `DJANGO_SUPERUSER_PASSWORD`)

### Videos hochladen

1. Im Admin-Panel einloggen
2. Zu "Videos" navigieren
3. Video hochladen → automatische Verarbeitung startet
4. Status in der Redis Queue überprüfen: [http://localhost:8000/django-rq/](http://localhost:8000/django-rq/)

---

## ⚙️ Konfiguration

### Environment Variablen (.env)

| Variable | Beschreibung | Standard | Pflicht |
|----------|--------------|----------|---------|
| **DJANGO_SUPERUSER_USERNAME** | Admin-Benutzername | `admin` | ✅ |
| **DJANGO_SUPERUSER_PASSWORD** | Admin-Passwort | `adminpassword` | ✅ |
| **DJANGO_SUPERUSER_EMAIL** | Admin-Email | `admin@example.com` | ✅ |
| **SECRET_KEY** | Django Secret Key | - | ✅ |
| **DEBUG** | Debug-Modus | `True` | ❌ |
| **ALLOWED_HOSTS** | Erlaubte Hosts (comma-separated) | `localhost,127.0.0.1` | ✅ |
| **CSRF_TRUSTED_ORIGINS** | CSRF-Trusted Origins | `http://localhost:5500,...` | ✅ |
| **CORS_ALLOWED_ORIGINS** | CORS-Allowed Origins | `http://localhost:5500,...` | ✅ |
| **DB_NAME** | Datenbankname | `your_database_name` | ✅ |
| **DB_USER** | Datenbank-Benutzer | `your_database_user` | ✅ |
| **DB_PASSWORD** | Datenbank-Passwort | `your_database_password` | ✅ |
| **DB_HOST** | Datenbank-Host | `db` | ❌ |
| **DB_PORT** | Datenbank-Port | `5432` | ❌ |
| **REDIS_HOST** | Redis Host | `redis` | ❌ |
| **REDIS_PORT** | Redis Port | `6379` | ❌ |
| **EMAIL_HOST** | SMTP Server | `smtp.example.com` | ✅ |
| **EMAIL_PORT** | SMTP Port | `587` | ❌ |
| **EMAIL_USE_TLS** | TLS verwenden | `True` | ❌ |
| **EMAIL_USE_SSL** | SSL verwenden | `False` | ❌ |
| **EMAIL_HOST_USER** | E-Mail Benutzername | - | ✅ |
| **EMAIL_HOST_PASSWORD** | E-Mail Passwort | - | ✅ |
| **DEFAULT_FROM_EMAIL** | Absender-Email | `EMAIL_HOST_USER` | ❌ |

> ** WICHTIG für Production:**
> - `DEBUG=False` setzen
> - Starkes `SECRET_KEY` generieren
> - `ALLOWED_HOSTS` mit echter Domain konfigurieren
> - HTTPS-URLs in `CORS_ALLOWED_ORIGINS` und `CSRF_TRUSTED_ORIGINS`

---

##  Troubleshooting

### Docker startet nicht

**Fehler**: `unable to get image 'postgres:latest'`

**Lösung**: Docker Desktop starten

---

### Entrypoint-Fehler

**Fehler**: `exec ./backend.entrypoint.sh: no such file or directory`

**Lösung**: Line-Endings auf `LF` setzen (nicht `CRLF`)
```bash
# In VS Code: Unten rechts auf "CRLF" klicken → "LF" auswählen
```

---

### Migration schlägt fehl

**Fehler**: Datenbank-Migration nach Model-Änderung fehlgeschlagen

**Lösung**: Migration im Container ausführen
```bash
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
```

---

### Port 8000 bereits belegt

**Fehler**: `port is already allocated`

**Lösung**: Anderen Prozess stoppen oder Port ändern
```bash
# Port-Konflikt finden
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Oder Port in docker-compose.yml ändern
ports:
  - "8001:8000"  # Host:Container
```

---

# English 🇬🇧

## 🚀 Quick Start (English)

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
