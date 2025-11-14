Hello! This is a mobile job tracking system I developed, enhanced with Cursor AI. You can find the project details below.

---

# WorkFlow: Job Tracking & Notification System

A mobile application designed to digitize and streamline task management and communication for field operations, particularly between site managers and workers.

## Project Overview

### Subject
Job Tracking and Notification System (WorkFlow)

### Purpose
To digitize the processes of assigning, tracking, and completing tasks. This system aims to accelerate business processes and facilitate job management by sending real-time notifications to workers in the field. It enables users to track their assigned tasks, view documents, and report task completion directly from their mobile devices.

### Target Audience
* **Site Managers:** Administrators responsible for assigning and overseeing tasks.
* **Field Workers:** Employees responsible for completing the assigned tasks.
* **Small and Medium-sized Enterprises (SMEs)**
* **Companies with Field Operations:** Construction, maintenance, technical services, etc.

### Database
* PostgreSQL (Relational Database)

### Data Model
* **User Information:** Role, email, first name, last name
* **Task/Job Information:** Title, description, status, start date, end date
* **Task Documents:** Start and completion documents (photos, files)
* **Device Tokens:** For managing push notifications
* **Invitation Codes:** For controlled user registration
* **Notification History:** Logs and statistics

### Platform
* **Backend:** Django REST Framework
* **Frontend:** Flutter (Android & iOS)
* **Notification System:** Firebase Cloud Messaging (FCM)
* **Deployment:** Docker Containerization

### Programming Languages
* **Backend:** Python (Django)
* **Frontend:** Dart (Flutter)
* **Database:** SQL

### Software Development Model
* **Agile:**
    * Regular sprint planning and review meetings.
    * Continuous Integration & Continuous Deployment (CI/CD).
    * Iterative development based on user feedback.

### Current Stage
* **Development & Iteration:**
    * Core user management and task assignment system is complete.
    * Notification system integration is complete and undergoing optimization.
    * The frontend application is functional with basic features.
    * Improvements are actively being made based on user feedback.
    * Focusing on multi-device token management and notification optimization.

---

## Features

* Site manager and worker roles
* Task creation and assignment
* Photo and document uploading
* Task status tracking (pending, in-progress, completed)
* Push notification system (via FCM)

## Technologies

* **Backend:** Django + Django REST Framework
* **Frontend:** Flutter
* **Authentication:** JWT (JSON Web Token)
* **Database:** SQLite (for local development)
* **Containerization:** Docker

## Installation

For detailed installation steps, please see the [SETUP.MD](SETUP.MD) file.

### Requirements

* [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### Installation with Docker

1.  Clone the project:
    ```bash
    git clone [https://github.com/yourusername/workflow.git](https://github.com/yourusername/workflow.git)
    cd workflow
    ```

2.  Build and run the Docker containers:
    ```bash
    # For initial setup
    docker-compose build

    # To start the project
    docker-compose up

    # To run in the background
    docker-compose up -d

    # To stop
    docker-compose down
    ```

3.  You can access the application by navigating to the following addresses in your browser:
    * **API:** `http://localhost:8000/api/`
    * **Admin Panel:** `http://localhost:8000/admin/`

### Creating a Superuser

To create a superuser for the admin panel, follow these steps:

```bash
# Open a new terminal while the container is running
docker-compose exec web python manage.py createsuperuser

## API Endpoints

TASKS
- `GET /api/tasks/` - List tasks
- `GET /api/tasks/{id}/` - Task detail
- `POST /api/tasks/` - Create a new task
- `POST /api/tasks/{id}/complete/` - Complete a task
- `GET /api/tasks/{id}/documents/` - Get documents for a task

USERS
- `POST /api/token/` - Login
  ```json
  {
    "email": "user@example.com",
    "password": "password123"
  }
  ```
- `POST /api/logout/` - Logout
  ```json
  {
    "refresh": "your_refresh_token"
  }
  ```
- `GET /api/users/me/` - Get current user information
- `POST /api/users/` - Create new user (Invitation code required)
  ```json
  {
    "email": "worker@example.com",
    "password": "secure_password",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "5551234567",
    "invitation_code": "XYZ123"
  }
  ```

DOCUMENTS
- `GET /api/documents/` - List documents
- `POST /api/documents/` - Upload a new document
- `GET /api/documents/{id}/` - Document detail
- `POST /api/documents/{id}/` - Update a document
- `DELETE /api/documents/{id}/` - Delete a document

INVITATIONS (Site Manager Only)
- `POST /api/invitations/create/` - Create a new invitation code
- `GET /api/invitations/list/` - List active invitation codes
- `POST /api/invitations/cancel/{id}/` - Cancel an invitation code

## Development Workflow

- Use the backend branch for `backend` development.
- Use the frontend branch for `frontend` development.
- Create a new feature branch for every new feature or fix.
- Run tests before opening a merge request.

## Postman Collection

To test the API with Postman:

1. Open Postman.
2. Click File > Import.
3. `WF.postman_collection.json` file.
4. `WF.postman_environment.json` environment file.
5. Select "WF" as your active environment.

Note: The token environment variable will be automatically updated when you call the login endpoint.