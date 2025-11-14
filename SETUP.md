# WorkFlow - Local Development Setup Guide

This guide will help you set up the WorkFlow project on your local machine from scratch.

## Prerequisites

Before starting, make sure you have the following installed:

- **Docker Desktop** - [Download here](https://www.docker.com/products/docker-desktop/)
- **Git** - [Download here](https://git-scm.com/downloads)
- **A code editor** (VS Code, PyCharm, etc.)

## Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/workflow.git
cd workflow
```

## Step 2: Create Environment File

Create a `.env` file in the project root directory. You can manually create it or use the template below.

**On Linux/Mac:**
```bash
touch .env
```

**On Windows (PowerShell):**
```powershell
New-Item -Path .env -ItemType File
```

Then copy the template below into your `.env` file.

## Step 3: Configure Environment Variables

Open the `.env` file and configure the following variables. Here's a complete template:

```env
# Django Configuration
SECRET_KEY=your-secret-key-here-generate-with-django-secret-key-generator
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration (Local Development)
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=localpassword
DB_HOST=db-local
DB_PORT=5432

# Email Configuration (Gmail with App Password)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password

# Firebase Configuration (For Push Notifications)
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_PRIVATE_KEY_ID=your-private-key-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nYour private key here\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=your-service-account@your-project.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=your-client-id
FIREBASE_CLIENT_X509_CERT_URL=https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com

# CSRF Trusted Origins (Optional)
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
```

Now configure each section:

### Required Variables

#### 1. Django Secret Key
Generate a secret key for Django. You can use this command:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Or use an online generator: https://djecrety.ir/

Add to `.env`:
```
SECRET_KEY=your-generated-secret-key-here
```

#### 2. Database Configuration (Optional - defaults work for local)
```
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=localpassword
DB_HOST=db-local
DB_PORT=5432
```

#### 3. Debug Mode
```
DEBUG=True
```

#### 4. Allowed Hosts
```
ALLOWED_HOSTS=localhost,127.0.0.1
```

#### 5. Email Configuration (Required for password reset and invitations)

You need a Gmail account with an App Password:

1. Go to your Google Account settings
2. Enable 2-Step Verification
3. Generate an App Password: https://myaccount.google.com/apppasswords
4. Use the generated password (not your regular Gmail password)

Add to `.env`:
```
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password-here
```

#### 6. Firebase Configuration (Required for push notifications)

To get Firebase credentials:

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project or select an existing one
3. Go to Project Settings > Service Accounts
4. Click "Generate New Private Key"
5. Download the JSON file
6. Extract the following values from the JSON:

Add to `.env`:
```
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY_ID=your-private-key-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nYour private key here\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=your-service-account@your-project.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=your-client-id
FIREBASE_CLIENT_X509_CERT_URL=https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com
```

**Important Notes:**
- The `FIREBASE_PRIVATE_KEY` must be on a single line with `\n` characters
- Keep the quotes around the private key value
- Replace all `\n` in the private key with actual newlines or use `\\n` in the .env file

#### 7. Storage Configuration (Optional for local development)

For local development, you don't need to configure Hetzner storage. The app will use local file storage automatically when `DEBUG=True`.

If you want to test production storage, you'll need:
```
HETZNER_ACCESS_KEY=your-access-key
HETZNER_SECRET_KEY=your-secret-key
HETZNER_BUCKET_NAME=your-bucket-name
HETZNER_ENDPOINT_URL=https://your-endpoint-url
```

## Step 4: Build and Start Containers

### First Time Setup

Build the Docker images:
```bash
docker-compose build
```

### Start the Application

Start all services:
```bash
docker-compose up
```

Or run in detached mode (background):
```bash
docker-compose up -d
```

### Check Container Status

Verify all containers are running:
```bash
docker-compose ps
```

You should see three services running:
- `db-local` (PostgreSQL database)
- `web-local` (Django application)
- `nginx-local` (Nginx web server)

## Step 5: Create Superuser

After the containers are running, create a superuser account to access the admin panel:

```bash
docker-compose exec web-local python manage.py createsuperuser
```

Follow the prompts to enter:
- Email address
- Username (optional, can use email)
- Password

## Step 6: Verify Installation

### Check API Health

Open your browser and visit:
- **API Root**: http://localhost:8000/api/
- **Admin Panel**: http://localhost:8000/admin/
- **API Documentation**: http://localhost:8000/api/tasks/

### Test Login Endpoint

You can test the login endpoint using curl or Postman:

```bash
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"email": "your-superuser-email@example.com", "password": "your-password"}'
```

## Step 7: Common Commands

### View Logs
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs web-local
docker-compose logs db-local

# Follow logs in real-time
docker-compose logs -f web-local
```

### Stop Containers
```bash
docker-compose down
```

### Restart Containers
```bash
docker-compose restart
```

### Rebuild After Code Changes
```bash
docker-compose up --build
```

### Access Django Shell
```bash
docker-compose exec web-local python manage.py shell
```

### Run Migrations Manually
```bash
docker-compose exec web-local python manage.py migrate
```

### Collect Static Files
```bash
docker-compose exec web-local python manage.py collectstatic --noinput
```

### Create Database Backup
```bash
docker-compose exec db-local pg_dump -U postgres postgres > backup.sql
```

### Restore Database Backup
```bash
docker-compose exec -T db-local psql -U postgres postgres < backup.sql
```

## Troubleshooting

### Port Already in Use

If port 8000 is already in use, you can change it in `docker-compose.yml`:

```yaml
nginx-local:
  ports:
    - 8001:80  # Change 8000 to 8001 or any available port
```

### Database Connection Error

If you see database connection errors:
1. Make sure `db-local` container is running: `docker-compose ps`
2. Check database credentials in `.env` match `docker-compose.yml`
3. Wait a few seconds for the database to fully start

### Permission Errors (Linux/Mac)

If you encounter permission errors with volumes:
```bash
sudo chown -R $USER:$USER .
```

### Container Won't Start

1. Check logs: `docker-compose logs web-local`
2. Verify `.env` file exists and has all required variables
3. Try rebuilding: `docker-compose build --no-cache`

### Email Not Sending

1. Verify Gmail App Password is correct (not your regular password)
2. Check `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` in `.env`
3. Make sure 2-Step Verification is enabled on your Google Account

### Firebase Not Working

1. Verify all Firebase credentials in `.env` are correct
2. Check that the private key is properly formatted with `\n` characters
3. Ensure the service account has proper permissions in Firebase Console

## Next Steps

1. **Import Postman Collection**: Import `WF.postman_collection.json` to test API endpoints
2. **Create Test Users**: Use the admin panel or API to create test users
3. **Create Invitation Codes**: Use the API to create invitation codes for new users
4. **Test Notifications**: Set up a Flutter app or use the API to test push notifications

## Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Docker Documentation](https://docs.docker.com/)
- [Firebase Cloud Messaging](https://firebase.google.com/docs/cloud-messaging)

## Support

If you encounter any issues:
1. Check the logs: `docker-compose logs`
2. Review this guide again
3. Check the project's GitHub Issues
4. Contact the project maintainer

