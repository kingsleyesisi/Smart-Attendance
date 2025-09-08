# Smart-Attendance System for DELTASU 👋

A modern, efficient, and user-friendly attendance system designed specifically for Delta State University, Abraka. This system aims to streamline the attendance tracking process, making it easier for both students and administrators.

## Table of Contents
1. [Features](#features)
2. [Technologies Used](#technologies-used)
3. [Installation](#installation)
4. [Usage](#usage)
5. [API Documentation](#api-documentation)
6. [Deployment](#deployment)
7. [Contributing](#contributing)
8. [License](#license)
9. [Acknowledgments](#acknowledgments)

## Features ✨

- **Efficient Attendance Tracking:** Simplifies attendance recording for students.
- **User-Friendly Interface:** Easy to navigate and use, ensuring a smooth experience for all users.
- **Modern Technology Stack:** Built using the latest web development technologies for optimal performance.
- **Scalable Design:** Designed to handle a large number of users and data, ensuring reliability as the university grows.
- **RESTful API:** Provides a flexible and powerful API for managing users and authentication.

## Technologies Used 🛠️

- **Python:** The primary programming language.
- **Django:** A high-level Python web framework for building robust web applications.
- **Django REST Framework:** A powerful toolkit for building Web APIs.
- **SQLite:** Database for development and testing.
- **djangorestframework-simplejwt:** JSON Web Token authentication for Django REST Framework.

[![Python](https://img.shields.io/badge/Python-3.x-blue)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2-green)](https://www.djangoproject.com/)
[![Django REST Framework](https://img.shields.io/badge/DRF-3.12-blueviolet)](https://www.django-rest-framework.org/)
[![SQLite](https://img.shields.io/badge/SQLite-3.x-yellow)](https://www.sqlite.org/)

## Installation ⚙️

Follow these steps to set up the Smart-Attendance project:

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/kingsleyesisi/Smart-Attendance.git
   cd Smart-Attendance
   ```

2. **Create and Activate a Virtual Environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Linux/macOS
   venv\Scripts\activate  # On Windows
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Apply Migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Create a Superuser:**
   ```bash
   python manage.py createsuperuser
   ```

6. **Start the Development Server:**
   ```bash
   python manage.py runserver
   ```

## Usage 💻

1. **Access the Application:**
   Open your web browser and go to `http://127.0.0.1:8000/` to access the application's main view.

2. **Admin Interface:**
   Access the admin interface at `http://127.0.0.1:8000/admin/`. Use the superuser credentials created during installation.

3. **API Endpoints:**
   The application provides RESTful API endpoints for user authentication and profile management. See the [API Documentation](#api-documentation) for details.

## API Documentation 🗂️

### 1. User Signup

- **Endpoint:** `/api/signup/`
- **Method:** `POST`
- **Description:** Registers a new user.
- **Request Body:**
  ```json
  {
    "first_name": "John",
    "last_name": "Doe",
    "middle_name": "M",
    "email": "john.doe@example.com",
    "mat_no": "DSU/20/12345",
    "department": "Computer Science",
    "faculty": "Science",
    "level": "400",
    "phone_number": "08012345678",
    "password": "SecurePassword",
    "confirm_password": "SecurePassword"
  }
  ```
- **Response (Success):**
  ```json
  {
    "id": 1,
    "first_name": "John",
    "last_name": "Doe",
    "middle_name": "M",
    "email": "john.doe@example.com",
    "mat_no": "DSU/20/12345",
    "department": "Computer Science",
    "faculty": "Science",
    "level": "400",
    "phone_number": "08012345678",
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
  ```

### 2. User Login

- **Endpoint:** `/api/login/`
- **Method:** `POST`
- **Description:** Logs in an existing user and returns JWT tokens.
- **Request Body:**
  ```json
  {
    "email": "john.doe@example.com",
    "password": "SecurePassword"
  }
  ```
- **Response (Success):**
  ```json
  {
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
  ```

### 3. Refresh Token

- **Endpoint:** `/api/refresh/`
- **Method:** `POST`
- **Description:** Refreshes an access token using a refresh token.
- **Request Body:**
  ```json
  {
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
  ```
- **Response (Success):**
  ```json
  {
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
  ```

### 4. User Logout

- **Endpoint:** `/api/logout/`
- **Method:** `POST`
- **Description:** Logs out a user by blacklisting the refresh token.
- **Request Body:**
  ```json
  {
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
  ```
- **Response (Success):**
  ```json
  {
    "detail": "Successfully logged out."
  }
  ```

### 5. User Profile

- **Endpoint:** `/api/profile/`
- **Method:** `GET`
- **Description:** Retrieves the profile of the authenticated user. Requires a valid access token.
- **Headers:**
  ```
  Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
  ```
- **Response (Success):**
  ```json
  {
    "id": 1,
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com"
  }
  ```

## Deployment 🚀

To deploy the Smart-Attendance application to a production environment, follow these steps:

1. **Set `DEBUG = False` in `settings.py`.**
2. **Configure a production-ready database (e.g., PostgreSQL).**
3. **Collect static files:**
   ```bash
   python manage.py collectstatic
   ```

4. **Use a production server like Gunicorn or uWSGI:**
   ```bash
   gunicorn backend.wsgi --bind 0.0.0.0:8000
   ```

5. **Set up a reverse proxy server (e.g., Nginx or Apache).**

## Contributing 🤝

Contributions are welcome! Here's how you can contribute:

1. **Fork the repository.**
2. **Create a new branch for your feature or bug fix.**
3. **Make your changes and commit them with descriptive messages.**
4. **Submit a pull request.**

## License 📝

This project is licensed under the [MIT License](LICENSE).

## Acknowledgments 🙏

- Thanks to DELTA STATE UNIVERSITY, ABRAKA, for the opportunity to build this system.
- Special thanks to the Django and Django REST Framework communities for providing excellent tools and documentation.

[![Built with DocMint](https://img.shields.io/badge/Generated%20by-DocMint-red)](https://github.com/kingsleyesisi/DocMint)