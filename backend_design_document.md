# Backend Design Document

## 1. System Overview

### Purpose of the System
The backend for the Smart Attendance & Analytics Web Application is designed to provide a robust, scalable, and secure foundation for managing course attendance, user roles, and data analytics. It will handle all business logic, data persistence, and API communications necessary to support the application's frontend and mobile components.

### Key Backend Features
The backend will support the following major functionalities:
*   Course and Attendance Window Management
*   Role-Based Authentication & Authorization (JWT)
*   QR Code Generation and Validation for Attendance
*   Real-time Attendance Tracking and Recording
*   Automated Notifications (Reminders, Absences, Approvals)
*   Data Processing for Analytics and Reporting
*   Bulk Data Export (XLSX, PDF)
*   Secure API Endpoints

### Core Backend Components
The primary architectural components that will deliver these features are:
*   **Django Web Server (uWSGI/Gunicorn + Nginx)**: Handles incoming HTTP requests and serves as the entry point to the application.
*   **Django REST Framework (DRF)**: Facilitates the rapid development of robust and secure RESTful APIs for interaction with frontend and mobile clients.
*   **PostgreSQL Database**: Serves as the primary data store for all application data, including user information, course details, attendance records, and system configurations.
*   **Celery Distributed Task Queue**: Manages asynchronous operations such as sending notifications, generating reports, and other background tasks to ensure responsiveness of the main application.
*   **Redis/RabbitMQ**: Acts as a message broker for Celery, enabling reliable communication between the web application and background workers. It may also be used for caching frequently accessed data to improve performance.
*   **Authentication Service**: Manages user identity, issues and validates JSON Web Tokens (JWTs), and enforces role-based access control (RBAC) across the system.
*   **Course Management Service**: Handles the creation, updating, and deletion of courses, manages course enrollments, and controls access based on departments and user roles.
*   **Attendance Service**: Manages the generation and validation of QR codes for attendance, defines and controls attendance windows, and records attendance data accurately.
*   **Notification Engine**: Powered by Celery, this component is responsible for sending out various automated alerts, including reminders for upcoming classes, notifications for absences, and updates on attendance approvals.
*   **Reporting & Analytics Engine**: Processes raw attendance data to generate insightful analytics and reports, supporting features like bulk data export in XLSX and PDF formats.

### Technology Stack Summary
The backend system will be built using the following mandated technologies:
*   **Framework**: Django and Django REST Framework (DRF)
*   **Database**: PostgreSQL
*   **Task Queue**: Celery
*   **Message Broker**: Redis (or RabbitMQ)
*   **Containerization**: Docker

## 2. API Design

### 2.1. General Principles
*   **RESTful Architecture**: The API will adhere to REST principles, utilizing standard HTTP methods (GET, POST, PUT, DELETE, PATCH) for resource manipulation.
*   **Statelessness**: Each API request will be independent and contain all necessary information for the server to process it. No client session state will be maintained on the server.
*   **JSON for Data Interchange**: All API requests and responses will use JSON (application/json) as the data format.
*   **Clear Versioning**: The API will be versioned (e.g., `/api/v1/...`) to allow for future updates without breaking existing client integrations.
*   **Consistent Naming Conventions**: API endpoints and resource fields will follow a consistent naming convention (e.g., snake_case for resource fields).
*   **Comprehensive Error Handling**: The API will provide clear and informative error messages with appropriate HTTP status codes to aid in debugging and client-side error handling. Standard error responses will follow a consistent format, e.g., `{ "error": "Descriptive error message", "details": { ... } }`.
*   **Security**: All API endpoints will be secured using HTTPS. Sensitive data will be encrypted in transit and at rest where appropriate. Input validation will be strictly enforced to prevent common web vulnerabilities (e.g., SQL injection, XSS).
*   **Pagination for Collections**: Endpoints returning lists of resources will implement pagination to manage response size and improve performance (e.g., using limit/offset or cursor-based pagination).
*   **Rate Limiting**: To protect against abuse and ensure fair usage, rate limiting will be implemented on API endpoints.

### 2.2. Authentication and Authorization
*   **JWT-based Authentication**: Authentication will be managed using JSON Web Tokens (JWT).
    *   Users will obtain a JWT by submitting their credentials (e.g., email and password) to a dedicated login endpoint (`/api/v1/auth/login/`).
    *   The JWT will be short-lived and must be included in the `Authorization` header of subsequent requests using the `Bearer` scheme (e.g., `Authorization: Bearer <token>`).
    *   A refresh token mechanism will be implemented (`/api/v1/auth/refresh/`) to allow clients to obtain new access tokens without requiring users to re-authenticate, enhancing user experience while maintaining security.
*   **Role-Based Access Control (RBAC)**:
    *   The system will define distinct user roles: `Super Admin`, `Admin`, `Faculty`, and `Student`.
    *   Each role will have specific permissions determining which API endpoints they can access and what operations they can perform.
    *   Permissions will be enforced at the API endpoint level using DRF's permission classes. For example, only `Admin` or `Super Admin` can create new courses, while `Faculty` can manage attendance for their assigned courses.
    *   Sensitive operations may require additional checks beyond basic role assignment (e.g., a faculty member can only modify attendance for courses they teach).
*   **User Registration and Management**:
    *   A registration endpoint (`/api/v1/auth/register/`) will allow new users to create accounts. The default role for new registrations will be `Student`.
    *   `Super Admin` and `Admin` users will have access to endpoints for managing user accounts, including assigning roles and activating/deactivating users.

## 3. High-Level Architecture

### 3.1. Architectural Style
The backend will be implemented as a **Modular Monolithic Django application**. This approach allows for a well-structured, maintainable codebase within a single deployment unit. Core functionalities will be organized into distinct services/modules, promoting separation of concerns and enabling focused development, while still leveraging the cohesiveness of the Django framework. This style is suitable for the current project scope and allows for potential future refactoring into microservices if scalability demands it.

### 3.2. Core Services/Modules
The system is composed of several core services/modules, expanding on the components identified in the System Overview:

*   **API Layer (Django REST Framework - DRF)**:
    *   **Responsibilities**: Serves as the primary entry point for all client requests (web frontend, mobile app). It handles request parsing, input validation (serialization/deserialization), user authentication (verifying JWTs), and authorization (checking role-based permissions). It then routes validated requests to the appropriate internal service for business logic execution and formats responses.

*   **Authentication Service**:
    *   **Responsibilities**: Manages all aspects of user identity and access control. This includes user registration (with a specific approval workflow for coordinator roles), secure login (issuing JWT access and refresh tokens), password reset mechanisms, email verification processes, and user role management (assigning and modifying roles like Super Admin, Admin, Faculty, Student).

*   **Course Management Service**:
    *   **Responsibilities**: Handles all Create, Read, Update, Delete (CRUD) operations for courses and departments. It manages the definition and enforcement of time windows during which attendance can be marked for specific courses. Crucially, it implements department-based access control, ensuring users can only interact with courses relevant to their department.

*   **Attendance Core Service**:
    *   **Responsibilities**: Central to the attendance tracking functionality. This service is responsible for generating unique, time-sensitive QR codes for attendance sessions. It validates scanned QR codes against active attendance windows, records student attendance, prevents duplicate check-ins for the same session, and handles policies for late entries. It also manages the state of attendance sessions (e.g., activating/deactivating them, potentially via scheduled tasks managed by Celery Beat).

*   **Notification Service (Celery-based)**:
    *   **Responsibilities**: Manages and dispatches all asynchronous notifications from the system. Primarily focused on email notifications, it handles:
        *   Reminders for upcoming classes or attendance windows.
        *   Follow-up notifications to students marked absent.
        *   Alerts for registration approvals/rejections (e.g., for coordinators).
        *   Other system alerts as needed.
    *   It relies on Celery for background task execution to avoid blocking user-facing operations.

*   **Data Processing & Reporting Service**:
    *   **Responsibilities**: Performs calculations and aggregations on raw attendance data to generate insightful analytics. This includes calculating attendance rates, identifying trends, and preparing data for reports. It also handles requests for bulk data export, generating files in formats like XLSX and PDF. Scheduled report generation (e.g., weekly summaries for admins) will also be managed by this service, likely using Celery.

*   **Database (PostgreSQL)**:
    *   **Responsibilities**: Acts as the central, persistent storage for all application data. This includes user profiles, course information, department structures, attendance records, system configurations, and potentially audit logs.

*   **Message Queue (Redis/RabbitMQ)**:
    *   **Responsibilities**: Serves as the message broker for Celery. It facilitates communication between the main Django application and Celery workers, ensuring reliable delivery and processing of asynchronous tasks like sending notifications or generating reports.

*   **Cache (Redis - Recommended)**:
    *   **Responsibilities**: Provides an in-memory data store for caching frequently accessed data. This can include things like user permissions, active course details, or results of common queries. Caching helps to reduce database load and improve the responsiveness of the API.

### 3.3. Data Flow Diagrams (Conceptual)

Below are textual descriptions of data flows for key use cases:

*   **User Authentication**:
    1.  `Client` (Frontend/Mobile) sends login credentials (email/password) to `API Layer`.
    2.  `API Layer` passes credentials to `Authentication Service`.
    3.  `Authentication Service` validates credentials against the `Database`.
    4.  If valid, `Authentication Service` generates a JWT (and refresh token) and returns it to the `API Layer`.
    5.  `API Layer` sends the JWT back to the `Client`.

*   **Coordinator Registers**:
    1.  `Prospective Coordinator Client` submits registration details to `API Layer`.
    2.  `API Layer` forwards details to `Authentication Service`.
    3.  `Authentication Service` creates a user record in the `Database` with a 'pending approval' status and 'Coordinator' role request.
    4.  `Authentication Service` triggers `Notification Service` (via Celery task and `Message Queue`).
    5.  `Notification Service` sends an email to `Admin/Super Admin` regarding the pending approval.
    6.  `Admin Client` approves the registration via an endpoint on the `API Layer`.
    7.  `API Layer` calls `Authentication Service` to update the user's role and status in the `Database`.
    8.  `Authentication Service` (optionally) triggers `Notification Service` again.
    9.  `Notification Service` sends an email to the `Coordinator` confirming their registration.

*   **Student Check-in (QR Scan)**:
    1.  `Student Client` scans a QR code and sends the embedded data (e.g., session ID, course ID) to the `API Layer`.
    2.  `API Layer` (after authenticating the student via JWT) forwards the request to `Attendance Core Service`.
    3.  `Attendance Core Service` validates the QR code data, checks if the attendance window for the course/session is active (querying `Database`), and verifies against duplicate entries for the student in the current session.
    4.  If valid, `Attendance Core Service` records the attendance in the `Database`.
    5.  `Attendance Core Service` returns success to `API Layer`.
    6.  `API Layer` returns success to `Student Client`.
    7.  (Potentially) `Attendance Core Service` triggers `Notification Service` for an optional check-in confirmation email/notification to the student.

*   **Admin Exports Report**:
    1.  `Admin Client` requests a data export (e.g., attendance report for a specific course) via the `API Layer`, specifying parameters like date range, course, format.
    2.  `API Layer` (after authentication/authorization) forwards the request to `Data Processing & Reporting Service`.
    3.  `Data Processing & Reporting Service` might queue this as a Celery task (via `Message Queue`) if the report is large.
    4.  The service (or its Celery worker) fetches the required data from the `Database`.
    5.  It processes the data and generates the report file (e.g., XLSX, PDF).
    6.  The service returns a link to the generated file or the file itself (depending on size and implementation) to the `API Layer`.
    7.  `API Layer` provides the file/link to the `Admin Client`.

*   **Automated Attendance Window Opening**:
    1.  `Celery Beat` (scheduler) triggers a predefined task at the scheduled time for opening an attendance window.
    2.  The task is picked up by a `Celery Worker` executing logic within the `Attendance Core Service`.
    3.  `Attendance Core Service` updates the state of the relevant attendance window (e.g., sets `is_active = true`) in the `Database`.
    4.  (Optionally) `Attendance Core Service` might trigger `Notification Service` to remind enrolled faculty/students that the window is open.

*   **Automated Reminder Notification (e.g., Class Reminder)**:
    1.  `Celery Beat` triggers a predefined notification task (e.g., 1 hour before class starts).
    2.  The task is picked up by a `Celery Worker` executing logic within the `Notification Service`.
    3.  `Notification Service` fetches relevant data from the `Database` (e.g., list of students and faculty for upcoming courses).
    4.  `Notification Service` formats and sends out emails (or other configured notifications) to the recipients.

### 3.4. Interaction between Components
Interactions between these services will primarily follow two patterns:

*   **Synchronous Calls**: For operations requiring immediate feedback or those that are integral to the current request-response cycle, services will interact via direct Python method calls. For example, the `API Layer` directly calls the `Authentication Service` during a login attempt. The `Attendance Core Service` might directly query the `Course Management Service` to validate course details. These are typically fast, in-process operations.
*   **Asynchronous Tasks (via Celery & Message Queue)**: For operations that can be offloaded to run in the background, thereby improving the responsiveness of the API, Celery will be used. This is suitable for:
    *   Sending emails/notifications (`Notification Service`).
    *   Generating large reports or data exports (`Data Processing & Reporting Service`).
    *   CPU-intensive background processing.
    *   Scheduled tasks like opening/closing attendance windows or sending daily summaries (`Attendance Core Service`, `Notification Service` triggered by Celery Beat).
    The main application (e.g., `API Layer` or another service) will publish a task to the `Message Queue` (Redis/RabbitMQ). Celery workers, running as separate processes, will consume these tasks and execute the corresponding logic from the relevant service.

This separation ensures that user-facing API endpoints remain fast, while longer-running or non-critical operations are handled efficiently in the background.

## 4. Database Schema (PostgreSQL)

### 4.1. Introduction
The backend system will utilize PostgreSQL as its relational database management system (RDBMS). PostgreSQL is chosen for its well-established reputation for reliability, data integrity features (ACID compliance, foreign keys, transactions), and its capability to handle complex queries and large datasets efficiently. Its extensibility and robust feature set make it suitable for the diverse data storage and retrieval needs of the Smart Attendance & Analytics Web Application, including user management, course scheduling, attendance tracking, and analytics.

### 4.2. Entity-Relationship Diagram (ERD) - Conceptual Description

The following outlines the main entities and their relationships within the system:

*   **Users & Roles**:
    *   A `User` entity stores information about individuals interacting with the system (students, faculty, admins).
    *   A `Role` entity defines the permissions and access levels (e.g., 'Super Admin', 'Admin', 'Faculty', 'Student').
    *   Each `User` is assigned exactly one `Role`. One `Role` can be assigned to many `Users`. (One-to-Many: Role to Users)

*   **Departments & Courses**:
    *   A `Department` entity represents academic or organizational units.
    *   A `Course` entity represents a specific subject or class.
    *   A `Department` can have multiple `Courses`. Each `Course` belongs to exactly one `Department`. (One-to-Many: Department to Courses)

*   **Courses & Users (Faculty/Coordinators)**:
    *   Faculty members or Coordinators (who are `Users` with a 'Faculty' or equivalent role) manage courses.
    *   A `Course` can be managed by multiple `Users` (Coordinators/Faculty).
    *   A `User` (Coordinator/Faculty) can manage multiple `Courses`.
    *   This is a Many-to-Many relationship, implemented via a `CourseCoordinatorLink` table.

*   **Courses & Users (Students)**:
    *   Students (`Users` with a 'Student' role) enroll in courses.
    *   A `Course` can have many `Students` enrolled.
    *   A `Student` can be enrolled in many `Courses`.
    *   This is a Many-to-Many relationship, implemented via an `Enrollments` table.

*   **Courses & AttendanceWindows**:
    *   An `AttendanceWindow` entity defines a specific time frame during which attendance can be marked for a course session.
    *   A `Course` can have multiple `AttendanceWindows` (e.g., one for each lecture/lab).
    *   Each `AttendanceWindow` belongs to exactly one `Course`. (One-to-Many: Course to AttendanceWindows)

*   **AttendanceWindows & QRCodes**:
    *   A `QRCode` entity stores the unique data for a QR code used for attendance marking.
    *   Each `AttendanceWindow` has one unique `QRCode` generated for that specific session.
    *   Each `QRCode` is associated with exactly one `AttendanceWindow`. (One-to-One: AttendanceWindow to QRCode)

*   **AttendanceWindows & AttendanceRecords**:
    *   An `AttendanceRecord` entity logs a student's attendance for a specific window.
    *   An `AttendanceWindow` can have multiple `AttendanceRecords` (one for each student who checked in).
    *   Each `AttendanceRecord` belongs to exactly one `AttendanceWindow`. (One-to-Many: AttendanceWindow to AttendanceRecords)

*   **Users (Students) & AttendanceRecords**:
    *   A `Student` (`User`) can have multiple `AttendanceRecords` across different courses and windows.
    *   Each `AttendanceRecord` is associated with exactly one `Student` (`User`). (One-to-Many: User to AttendanceRecords)

*   **Notifications**:
    *   A `Notification` entity stores information about system-generated alerts (e.g., reminders, approvals).
    *   `Notifications` are typically linked to a specific `User` (the recipient).
    *   A `User` can receive multiple `Notifications`. (One-to-Many: User to Notifications)

### 4.3. Table Definitions

Below are the detailed definitions for each table:

1.  **`Roles`**
    *   **Table Name**: `Roles`
    *   **Columns**:
        *   `id` (SERIAL): Unique identifier for the role.
        *   `name` (VARCHAR(50)): Name of the role (e.g., 'super_admin', 'admin', 'faculty', 'student').
        *   `description` (TEXT): Optional description of the role's responsibilities.
    *   **Primary Key**: `id`
    *   **Constraints**: `name` must be UNIQUE and NOT NULL.
    *   **Indexes**: `name` (for lookups).

2.  **`Users`** (Custom User Model)
    *   **Table Name**: `Users`
    *   **Columns**:
        *   `id` (SERIAL): Unique identifier for the user.
        *   `email` (VARCHAR(255)): User's email address, used for login.
        *   `password_hash` (VARCHAR(255)): Hashed password for the user.
        *   `first_name` (VARCHAR(100)): User's first name.
        *   `last_name` (VARCHAR(100)): User's last name.
        *   `role_id` (INTEGER): Foreign key referencing `Roles.id`.
        *   `is_active` (BOOLEAN): Whether the user account is active. Defaults to `TRUE`.
        *   `is_verified` (BOOLEAN): Whether the user's email has been verified. Defaults to `FALSE`.
        *   `registration_status` (VARCHAR(20)): Status for role applications (e.g., faculty/coordinator registration: 'pending', 'approved', 'rejected'). Defaults to `pending` or can be `NULL` if not applicable.
        *   `created_at` (TIMESTAMP WITH TIME ZONE): Timestamp of user creation. Defaults to `CURRENT_TIMESTAMP`.
        *   `updated_at` (TIMESTAMP WITH TIME ZONE): Timestamp of last user update. Defaults to `CURRENT_TIMESTAMP`.
    *   **Primary Key**: `id`
    *   **Foreign Keys**: `role_id` REFERENCES `Roles(id)` (ON DELETE RESTRICT - prevent role deletion if users are assigned).
    *   **Constraints**: `email` must be UNIQUE and NOT NULL. `password_hash` NOT NULL. `role_id` NOT NULL.
    *   **Indexes**: `email` (for login), `role_id`.

3.  **`Departments`**
    *   **Table Name**: `Departments`
    *   **Columns**:
        *   `id` (SERIAL): Unique identifier for the department.
        *   `name` (VARCHAR(255)): Name of the department.
        *   `description` (TEXT): Optional description of the department.
    *   **Primary Key**: `id`
    *   **Constraints**: `name` must be UNIQUE and NOT NULL.
    *   **Indexes**: `name`.

4.  **`Courses`**
    *   **Table Name**: `Courses`
    *   **Columns**:
        *   `id` (SERIAL): Unique identifier for the course.
        *   `code` (VARCHAR(20)): Unique code for the course (e.g., 'CS101').
        *   `name` (VARCHAR(255)): Full name of the course.
        *   `description` (TEXT): Optional detailed description of the course.
        *   `department_id` (INTEGER): Foreign key referencing `Departments.id`.
        *   `start_date` (DATE): Official start date of the course.
        *   `end_date` (DATE): Official end date of the course.
        *   `created_at` (TIMESTAMP WITH TIME ZONE): Timestamp of course creation. Defaults to `CURRENT_TIMESTAMP`.
        *   `updated_at` (TIMESTAMP WITH TIME ZONE): Timestamp of last course update. Defaults to `CURRENT_TIMESTAMP`.
    *   **Primary Key**: `id`
    *   **Foreign Keys**: `department_id` REFERENCES `Departments(id)` ON DELETE CASCADE (if a department is deleted, its courses are also deleted).
    *   **Constraints**: `code` must be UNIQUE and NOT NULL. `name` NOT NULL. `department_id` NOT NULL.
    *   **Indexes**: `code`, `department_id`.

5.  **`CourseCoordinatorLink`**
    *   **Table Name**: `CourseCoordinatorLink`
    *   **Purpose**: Links Users (Coordinators/Faculty) to Courses they manage (Many-to-Many).
    *   **Columns**:
        *   `id` (SERIAL): Unique identifier for the link.
        *   `user_id` (INTEGER): Foreign key referencing `Users.id`.
        *   `course_id` (INTEGER): Foreign key referencing `Courses.id`.
    *   **Primary Key**: `id`
    *   **Foreign Keys**:
        *   `user_id` REFERENCES `Users(id)` ON DELETE CASCADE.
        *   `course_id` REFERENCES `Courses(id)` ON DELETE CASCADE.
    *   **Constraints**: UNIQUE (`user_id`, `course_id`) to prevent duplicate assignments.
    *   **Indexes**: `user_id`, `course_id`.

6.  **`Enrollments`**
    *   **Table Name**: `Enrollments`
    *   **Purpose**: Links Users (Students) to Courses they are enrolled in (Many-to-Many).
    *   **Columns**:
        *   `id` (SERIAL): Unique identifier for the enrollment.
        *   `user_id` (INTEGER): Foreign key referencing `Users.id` (the student).
        *   `course_id` (INTEGER): Foreign key referencing `Courses.id`.
        *   `enrollment_date` (TIMESTAMP WITH TIME ZONE): Timestamp of when the enrollment occurred. Defaults to `CURRENT_TIMESTAMP`.
    *   **Primary Key**: `id`
    *   **Foreign Keys**:
        *   `user_id` REFERENCES `Users(id)` ON DELETE CASCADE.
        *   `course_id` REFERENCES `Courses(id)` ON DELETE CASCADE.
    *   **Constraints**: UNIQUE (`user_id`, `course_id`) to prevent duplicate enrollments.
    *   **Indexes**: `user_id`, `course_id`.

7.  **`AttendanceWindows`**
    *   **Table Name**: `AttendanceWindows`
    *   **Columns**:
        *   `id` (SERIAL): Unique identifier for the attendance window.
        *   `course_id` (INTEGER): Foreign key referencing `Courses.id`.
        *   `start_time` (TIMESTAMP WITH TIME ZONE): Scheduled start time for check-in.
        *   `end_time` (TIMESTAMP WITH TIME ZONE): Scheduled end time for check-in.
        *   `status` (VARCHAR(20)): Current status of the window (e.g., 'scheduled', 'open', 'closed', 'extended').
        *   `created_at` (TIMESTAMP WITH TIME ZONE): Timestamp of window creation. Defaults to `CURRENT_TIMESTAMP`.
    *   **Primary Key**: `id`
    *   **Foreign Keys**: `course_id` REFERENCES `Courses(id)` ON DELETE CASCADE.
    *   **Constraints**: `course_id` NOT NULL, `start_time` NOT NULL, `end_time` NOT NULL, `status` NOT NULL.
    *   **Indexes**: `course_id`, `status`, `start_time`, `end_time`.

8.  **`QRCodes`**
    *   **Table Name**: `QRCodes`
    *   **Columns**:
        *   `id` (SERIAL): Unique identifier for the QR code record.
        *   `attendance_window_id` (INTEGER): Foreign key referencing `AttendanceWindows.id`.
        *   `qr_data` (TEXT): The actual data embedded in the QR code, must be unique.
        *   `expires_at` (TIMESTAMP WITH TIME ZONE): Expiration time of the QR code, should align with `AttendanceWindows.end_time`.
        *   `created_at` (TIMESTAMP WITH TIME ZONE): Timestamp of QR code creation. Defaults to `CURRENT_TIMESTAMP`.
    *   **Primary Key**: `id`
    *   **Foreign Keys**: `attendance_window_id` REFERENCES `AttendanceWindows(id)` ON DELETE CASCADE.
    *   **Constraints**: `attendance_window_id` UNIQUE and NOT NULL. `qr_data` UNIQUE and NOT NULL. `expires_at` NOT NULL.
    *   **Indexes**: `qr_data` (for quick validation), `attendance_window_id`.

9.  **`AttendanceRecords`**
    *   **Table Name**: `AttendanceRecords`
    *   **Columns**:
        *   `id` (SERIAL): Unique identifier for the attendance record.
        *   `attendance_window_id` (INTEGER): Foreign key referencing `AttendanceWindows.id`.
        *   `student_id` (INTEGER): Foreign key referencing `Users.id` (the student).
        *   `timestamp` (TIMESTAMP WITH TIME ZONE): Actual time of check-in. Defaults to `CURRENT_TIMESTAMP`.
        *   `status` (VARCHAR(20)): Status of attendance (e.g., 'present', 'late').
    *   **Primary Key**: `id`
    *   **Foreign Keys**:
        *   `attendance_window_id` REFERENCES `AttendanceWindows(id)` ON DELETE CASCADE.
        *   `student_id` REFERENCES `Users(id)` ON DELETE CASCADE.
    *   **Constraints**: UNIQUE (`attendance_window_id`, `student_id`) to prevent duplicate check-ins for the same student in the same window. `status` NOT NULL.
    *   **Indexes**: `attendance_window_id`, `student_id`.

10. **`Notifications`**
    *   **Table Name**: `Notifications`
    *   **Columns**:
        *   `id` (SERIAL): Unique identifier for the notification.
        *   `user_id` (INTEGER): Foreign key referencing `Users.id` (the recipient).
        *   `type` (VARCHAR(50)): Type of notification (e.g., 'class_reminder', 'absentee_followup', 'registration_approved').
        *   `message` (TEXT): Content of the notification.
        *   `status` (VARCHAR(20)): Status of the notification (e.g., 'pending', 'sent', 'failed'). Defaults to `pending`.
        *   `scheduled_time` (TIMESTAMP WITH TIME ZONE): If the notification is scheduled for a future time. Can be `NULL`.
        *   `sent_time` (TIMESTAMP WITH TIME ZONE): Actual time the notification was sent. Can be `NULL`.
        *   `created_at` (TIMESTAMP WITH TIME ZONE): Timestamp of notification creation. Defaults to `CURRENT_TIMESTAMP`.
    *   **Primary Key**: `id`
    *   **Foreign Keys**: `user_id` REFERENCES `Users(id)` ON DELETE CASCADE.
    *   **Constraints**: `user_id` NOT NULL, `type` NOT NULL, `message` NOT NULL, `status` NOT NULL.
    *   **Indexes**: `user_id`, `type`, `status`, `scheduled_time`.

### 4.4. DDL Statements (PostgreSQL)

```sql
CREATE TABLE Roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE Users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role_id INTEGER NOT NULL REFERENCES Roles(id) ON DELETE RESTRICT,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    registration_status VARCHAR(20) DEFAULT 'pending', -- For coordinator: pending, approved, rejected
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Departments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE Courses (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    department_id INTEGER NOT NULL REFERENCES Departments(id) ON DELETE CASCADE,
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE CourseCoordinatorLink (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES Users(id) ON DELETE CASCADE,
    course_id INTEGER NOT NULL REFERENCES Courses(id) ON DELETE CASCADE,
    UNIQUE (user_id, course_id)
);

CREATE TABLE Enrollments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES Users(id) ON DELETE CASCADE, -- Student
    course_id INTEGER NOT NULL REFERENCES Courses(id) ON DELETE CASCADE,
    enrollment_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, course_id)
);

CREATE TABLE AttendanceWindows (
    id SERIAL PRIMARY KEY,
    course_id INTEGER NOT NULL REFERENCES Courses(id) ON DELETE CASCADE,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'scheduled', -- scheduled, open, closed, extended
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE QRCodes (
    id SERIAL PRIMARY KEY,
    attendance_window_id INTEGER UNIQUE NOT NULL REFERENCES AttendanceWindows(id) ON DELETE CASCADE,
    qr_data TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE AttendanceRecords (
    id SERIAL PRIMARY KEY,
    attendance_window_id INTEGER NOT NULL REFERENCES AttendanceWindows(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES Users(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL, -- e.g., 'present', 'late'
    UNIQUE (attendance_window_id, student_id)
);

CREATE TABLE Notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES Users(id) ON DELETE CASCADE, -- Recipient
    type VARCHAR(50) NOT NULL, -- e.g., 'class_reminder', 'absentee_followup', 'registration_approved'
    message TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending', -- pending, sent, failed
    scheduled_time TIMESTAMP WITH TIME ZONE NULL,
    sent_time TIMESTAMP WITH TIME ZONE NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Trigger to update 'updated_at' timestamp for Users table
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at
BEFORE UPDATE ON Users
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Trigger to update 'updated_at' timestamp for Courses table
CREATE TRIGGER update_courses_updated_at
BEFORE UPDATE ON Courses
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

```

### 4.5. Data Integrity Notes
Data integrity is paramount and will be maintained through several PostgreSQL features:
*   **ACID Properties**: All database operations will adhere to Atomicity, Consistency, Isolation, and Durability (ACID) properties, ensuring reliable transaction processing.
*   **Foreign Key Constraints**: As defined in the table structures, foreign keys will enforce referential integrity between related tables. For example, an `AttendanceRecord` cannot exist without a valid `student_id` from the `Users` table and a valid `attendance_window_id` from the `AttendanceWindows` table. The `ON DELETE` clauses (e.g., `CASCADE`, `RESTRICT`) specify how dependent records are handled when a referenced record is deleted.
*   **NOT NULL Constraints**: Ensure that essential data fields are always populated.
*   **UNIQUE Constraints**: Prevent duplicate entries for fields that must be unique (e.g., `Users.email`, `Courses.code`, `QRCodes.qr_data`).
*   **Check Constraints (Potential)**: While not explicitly defined in the DDL above for brevity, `CHECK` constraints can be added to enforce specific conditions on data values (e.g., `Courses.end_date >= Courses.start_date`).
*   **Application-Level Validation**: Django models will provide an additional layer of validation before data is even sent to the database.

### 4.6. Indexing Strategy
To ensure optimal query performance, indexes will be created on:
*   **Primary Keys**: PostgreSQL automatically creates indexes on primary keys.
*   **Foreign Keys**: Indexes will be explicitly created on all foreign key columns (e.g., `Users.role_id`, `Courses.department_id`, `AttendanceRecords.student_id`, `AttendanceRecords.attendance_window_id`, etc.) as these are frequently used in JOIN operations.
*   **Frequently Queried Columns**: Columns often used in `WHERE` clauses, `ORDER BY` clauses, or for lookups will be indexed. Examples include:
    *   `Users.email` (critical for login)
    *   `Courses.code` (for looking up courses by their unique code)
    *   `AttendanceWindows.status` (for querying active or scheduled windows)
    *   `AttendanceWindows.start_time` and `AttendanceWindows.end_time` (for time-based queries)
    *   `QRCodes.qr_data` (for validating QR codes quickly)
    *   `Notifications.status` and `Notifications.scheduled_time` (for processing pending or scheduled notifications)
*   **Composite Indexes**: For queries involving multiple columns in `WHERE` clauses, composite indexes will be considered (e.g., `UNIQUE (attendance_window_id, student_id)` in `AttendanceRecords` also serves as a performance index).

The specific indexes will be further refined based on observed query patterns and performance testing during development.

## 5. API Specification (DRF)

### 5.1. Introduction
The API for the Smart Attendance & Analytics Web Application will be built using the Django REST Framework (DRF), providing a powerful and flexible toolkit for developing RESTful APIs.

Key characteristics of the API include:
*   **Versioning**: All API endpoints will be versioned to ensure backward compatibility and allow for smooth transitions during updates. The current version will be `/api/v1/`.
*   **Authentication**: Secure authentication will be managed using JSON Web Tokens (JWT). Clients must include a JWT access token in the `Authorization` header of their requests using the `Bearer` scheme (e.g., `Authorization: Bearer <your_jwt_token>`).
*   **Standard HTTP Status Codes**: The API will utilize standard HTTP status codes to indicate the outcome of requests:
    *   `200 OK`: Request succeeded.
    *   `201 Created`: Resource successfully created.
    *   `204 No Content`: Request succeeded, but there is no content to return (e.g., for DELETE operations).
    *   `400 Bad Request`: The server could not understand the request due to invalid syntax or missing parameters.
    *   `401 Unauthorized`: Authentication is required and has failed or has not yet been provided.
    *   `403 Forbidden`: The authenticated user does not have permission to perform the requested action.
    *   `404 Not Found`: The requested resource could not be found.
    *   `500 Internal Server Error`: An unexpected condition was encountered on the server.
*   **Global Considerations**:
    *   **Rate Limiting**: To protect system resources and ensure fair usage, rate limiting will be implemented on API endpoints. Specific limits will be configured based on expected load and usage patterns.
    *   **Request Validation**: DRF serializers will be used extensively for input validation, ensuring that data conforms to expected formats and constraints before processing.

### 5.2. Authentication Endpoints (Auth Service)
Base URL: `/api/v1/auth/`

*   **`POST /api/v1/auth/register/`**
    *   **Description**: Allows new users to register. For users selecting the 'coordinator' role, their `registration_status` will be set to 'pending' for admin approval. The 'admin' or 'super_admin' role cannot be self-assigned via this endpoint.
    *   **Request Body**:
        ```json
        {
            "email": "user@example.com",
            "password": "securepassword123",
            "first_name": "John",
            "last_name": "Doe",
            "role": "student" // or "coordinator"
        }
        ```
    *   **Response Body**: `201 Created`
        ```json
        {
            "id": 1,
            "email": "user@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "role": "student", // or "coordinator"
            "registration_status": "approved" // or "pending" if role is coordinator
        }
        ```
    *   **Auth**: None.

*   **`POST /api/v1/auth/login/`**
    *   **Description**: Authenticates a user and returns JWT access and refresh tokens.
    *   **Request Body**:
        ```json
        {
            "email": "user@example.com",
            "password": "securepassword123"
        }
        ```
    *   **Response Body**: `200 OK`
        ```json
        {
            "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        }
        ```
    *   **Auth**: None.

*   **`POST /api/v1/auth/token/refresh/`**
    *   **Description**: Obtains a new JWT access token using a valid refresh token.
    *   **Request Body**:
        ```json
        {
            "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        }
        ```
    *   **Response Body**: `200 OK`
        ```json
        {
            "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        }
        ```
    *   **Auth**: None (requires a valid refresh token in the request body).

*   **`POST /api/v1/auth/password/reset/`**
    *   **Description**: Initiates the password reset process by sending an email with a reset token to the user.
    *   **Request Body**:
        ```json
        {
            "email": "user@example.com"
        }
        ```
    *   **Response Body**: `200 OK`
        ```json
        {
            "message": "Password reset email sent."
        }
        ```
    *   **Auth**: None.

*   **`POST /api/v1/auth/password/reset/confirm/`**
    *   **Description**: Allows a user to set a new password using a valid reset token.
    *   **Request Body**:
        ```json
        {
            "token": "valid_reset_token_string",
            "new_password": "newsecurepassword456"
        }
        ```
    *   **Response Body**: `200 OK`
        ```json
        {
            "message": "Password has been reset."
        }
        ```
    *   **Auth**: None.

*   **`POST /api/v1/auth/verify-email/`**
    *   **Description**: Initiates the email verification process by sending a verification token to the user's email. Useful if the initial verification email was missed or expired.
    *   **Request Body**:
        ```json
        {
            "email": "user@example.com" // Optional if user is authenticated, defaults to logged-in user's email
        }
        ```
    *   **Response Body**: `200 OK`
        ```json
        {
            "message": "Verification email sent."
        }
        ```
    *   **Auth**: JWT (User must be logged in to re-request verification for their own account).

*   **`POST /api/v1/auth/verify-email/confirm/`**
    *   **Description**: Confirms a user's email address using a valid verification token.
    *   **Request Body**:
        ```json
        {
            "token": "valid_verification_token_string"
        }
        ```
    *   **Response Body**: `200 OK`
        ```json
        {
            "message": "Email verified successfully."
        }
        ```
    *   **Auth**: None.

*   **`GET /api/v1/auth/users/me/`**
    *   **Description**: Retrieves the details of the currently authenticated user.
    *   **Request Body**: None.
    *   **Response Body**: `200 OK`
        ```json
        {
            "id": 1,
            "email": "user@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "role": "student", // or "coordinator", "admin"
            "is_active": true,
            "is_verified": true,
            "registration_status": "approved" // or "pending"
        }
        ```
    *   **Auth**: JWT (Any authenticated user).

*   **Admin-Specific User Management Endpoints**
    *   Base URL: `/api/v1/admin/users/`
    *   **`GET /api/v1/admin/users/`**:
        *   **Description**: Lists all users. Supports pagination.
        *   **Auth**: JWT (Admin/Super Admin role required).
        *   **Response**: `200 OK` - Array of user objects.
    *   **`GET /api/v1/admin/users/{id}/`**:
        *   **Description**: Retrieves a specific user by their ID.
        *   **Auth**: JWT (Admin/Super Admin role required).
        *   **Response**: `200 OK` - User object.
    *   **`PUT /api/v1/admin/users/{id}/`**:
        *   **Description**: Updates a user's details, including their role, active status, etc.
        *   **Auth**: JWT (Admin/Super Admin role required).
        *   **Request Body**: `{ "role": "faculty", "is_active": false }` (Example)
        *   **Response**: `200 OK` - Updated user object.
    *   **`POST /api/v1/admin/users/{id}/approve-coordinator/`**:
        *   **Description**: Approves a pending coordinator registration. Sets `registration_status` to 'approved' and `is_active` to `true`.
        *   **Auth**: JWT (Admin/Super Admin role required).
        *   **Response**: `200 OK` - `{"message": "Coordinator approved successfully."}`
    *   **`POST /api/v1/admin/users/{id}/reject-coordinator/`**:
        *   **Description**: Rejects a pending coordinator registration. Sets `registration_status` to 'rejected'.
        *   **Auth**: JWT (Admin/Super Admin role required).
        *   **Response**: `200 OK` - `{"message": "Coordinator rejected successfully."}`

### 5.3. Course Management Endpoints (Course Service)
Base URL: `/api/v1/`

*   **Departments**
    *   Base URL: `/api/v1/departments/`
    *   **`GET /departments/`**:
        *   **Description**: Lists all departments.
        *   **Auth**: JWT (Admin, Coordinator roles).
        *   **Response**: `200 OK` - Array of department objects.
            ```json
            [
                {"id": 1, "name": "Computer Science", "description": "..."},
                {"id": 2, "name": "Electrical Engineering", "description": "..."}
            ]
            ```
    *   **`POST /departments/`**:
        *   **Description**: Creates a new department.
        *   **Auth**: JWT (Admin role required).
        *   **Request Body**: `{ "name": "Mechanical Engineering", "description": "..." }`
        *   **Response**: `201 Created` - Created department object.
    *   **`GET /departments/{id}/`**:
        *   **Description**: Retrieves a specific department.
        *   **Auth**: JWT (Admin, Coordinator roles).
        *   **Response**: `200 OK` - Department object.
    *   **`PUT /departments/{id}/`**:
        *   **Description**: Updates a department.
        *   **Auth**: JWT (Admin role required).
        *   **Request Body**: `{ "name": "Civil Engineering", "description": "Updated description" }`
        *   **Response**: `200 OK` - Updated department object.
    *   **`DELETE /departments/{id}/`**:
        *   **Description**: Deletes a department.
        *   **Auth**: JWT (Admin role required).
        *   **Response**: `204 No Content`.

*   **Courses**
    *   Base URL: `/api/v1/courses/`
    *   **`GET /courses/`**:
        *   **Description**: Lists courses. Supports filtering by `department_id`, `coordinator_id`, `student_id`.
        *   **Auth**: JWT (Admin, Coordinator, Student - scoped access based on role).
        *   **Response**: `200 OK` - Array of course objects.
            ```json
            [
                {"id": 1, "code": "CS101", "name": "Intro to Programming", "department_id": 1, ...},
                {"id": 2, "code": "EE202", "name": "Circuit Theory", "department_id": 2, ...}
            ]
            ```
    *   **`POST /courses/`**:
        *   **Description**: Creates a new course.
        *   **Auth**: JWT (Admin role required).
        *   **Request Body**: `{ "code": "PY201", "name": "Python Programming", "department_id": 1, "start_date": "2024-09-01", "end_date": "2024-12-15" }`
        *   **Response**: `201 Created` - Created course object.
    *   **`GET /courses/{id}/`**:
        *   **Description**: Retrieves a specific course.
        *   **Auth**: JWT (Admin, Assigned Coordinator, Enrolled Student).
        *   **Response**: `200 OK` - Course object.
    *   **`PUT /courses/{id}/`**:
        *   **Description**: Updates a course.
        *   **Auth**: JWT (Admin, Assigned Coordinator of the course).
        *   **Request Body**: `{ "name": "Advanced Python Programming", "description": "..." }`
        *   **Response**: `200 OK` - Updated course object.
    *   **`DELETE /courses/{id}/`**:
        *   **Description**: Deletes a course.
        *   **Auth**: JWT (Admin role required).
        *   **Response**: `204 No Content`.
    *   **`POST /courses/{id}/assign-coordinator/`**:
        *   **Description**: Assigns a coordinator (user with Faculty/Coordinator role) to a course.
        *   **Auth**: JWT (Admin role required).
        *   **Request Body**: `{ "user_id": 25 }` // ID of the coordinator
        *   **Response**: `200 OK` - `{"message": "Coordinator assigned successfully."}`
    *   **`POST /courses/{id}/enroll/`**:
        *   **Description**: Allows the authenticated student to enroll in a course.
        *   **Auth**: JWT (Student role required).
        *   **Response**: `201 Created` - `{"message": "Successfully enrolled in the course."}`
    *   **`POST /courses/{id}/unenroll/`**:
        *   **Description**: Allows the authenticated student to un-enroll from a course.
        *   **Auth**: JWT (Student role required).
        *   **Response**: `200 OK` - `{"message": "Successfully un-enrolled from the course."}`

### 5.4. Attendance Endpoints (Attendance Service)
Base URL: `/api/v1/`

*   **Attendance Windows**
    *   **`GET /courses/{course_id}/attendance-windows/`**:
        *   **Description**: Lists all attendance windows for a specific course.
        *   **Auth**: JWT (Admin, Assigned Coordinator of the course, Enrolled Student in the course).
        *   **Response**: `200 OK` - Array of attendance window objects.
            ```json
            [
                {"id": 1, "course_id": 1, "start_time": "2024-10-01T09:00:00Z", "end_time": "2024-10-01T09:15:00Z", "status": "open"},
                ...
            ]
            ```
    *   **`POST /courses/{course_id}/attendance-windows/`**:
        *   **Description**: Creates a new attendance window for a course. QR code is generated automatically.
        *   **Auth**: JWT (Admin, Assigned Coordinator of the course).
        *   **Request Body**: `{ "start_time": "2024-10-08T09:00:00Z", "end_time": "2024-10-08T09:15:00Z" }`
        *   **Response**: `201 Created` - Created attendance window object (may include QR code data if user is privileged).
    *   **`GET /attendance-windows/{id}/`**:
        *   **Description**: Retrieves details of a specific attendance window. Includes QR code data if the user is an Admin or the Assigned Coordinator.
        *   **Auth**: JWT (Admin, Assigned Coordinator of the course, Enrolled Student in the course).
        *   **Response**: `200 OK` - Attendance window object.
    *   **`PUT /attendance-windows/{id}/`**:
        *   **Description**: Updates an attendance window (e.g., extend `end_time`, change `status`).
        *   **Auth**: JWT (Admin, Assigned Coordinator of the course).
        *   **Request Body**: `{ "end_time": "2024-10-01T09:30:00Z", "status": "extended" }`
        *   **Response**: `200 OK` - Updated attendance window object.
    *   **`DELETE /attendance-windows/{id}/`**:
        *   **Description**: Deletes an attendance window.
        *   **Auth**: JWT (Admin, Assigned Coordinator of the course).
        *   **Response**: `204 No Content`.
    *   **`POST /attendance-windows/{id}/open/`**:
        *   **Description**: Manually opens the check-in for an attendance window. Sets status to 'open'.
        *   **Auth**: JWT (Admin, Assigned Coordinator of the course).
        *   **Response**: `200 OK` - `{"message": "Attendance window opened."}`
    *   **`POST /attendance-windows/{id}/close/`**:
        *   **Description**: Manually closes the check-in for an attendance window. Sets status to 'closed'.
        *   **Auth**: JWT (Admin, Assigned Coordinator of the course).
        *   **Response**: `200 OK` - `{"message": "Attendance window closed."}`
    *   **`GET /attendance-windows/{id}/qr-code/`**:
        *   **Description**: Retrieves the QR code data for a specific attendance window.
        *   **Auth**: JWT (Admin, Assigned Coordinator of the course).
        *   **Response**: `200 OK` - `{ "qr_data": "unique_qr_string_for_window_1", "expires_at": "2024-10-01T09:15:00Z" }`

*   **Attendance Records**
    *   **`POST /api/v1/attendance/check-in/`**:
        *   **Description**: Allows a student to check-in for a course session by submitting valid QR code data.
        *   **Auth**: JWT (Student role required).
        *   **Request Body**:
            ```json
            {
                "qr_data": "unique_qr_string_for_window_1",
                "location_data": { "latitude": 34.0522, "longitude": -118.2437 } // Optional
            }
            ```
        *   **Response Body**: `201 Created`
            ```json
            {
                "record_id": 123,
                "student_id": 42,
                "course_name": "Intro to Programming",
                "timestamp": "2024-10-01T09:05:12Z",
                "status": "present" // or "late"
            }
            ```
    *   **`GET /api/v1/attendance-windows/{window_id}/records/`**:
        *   **Description**: Lists all attendance records for a specific attendance window.
        *   **Auth**: JWT (Admin, Assigned Coordinator of the course associated with the window).
        *   **Response**: `200 OK` - Array of attendance record objects.
    *   **`GET /api/v1/courses/{course_id}/attendance-summary/`**:
        *   **Description**: Retrieves an attendance summary for a specific course (e.g., overall attendance rate, list of absentees).
        *   **Auth**: JWT (Admin, Assigned Coordinator of the course).
        *   **Response**: `200 OK` - Summary data object.
    *   **`GET /api/v1/students/{student_id}/attendance-history/`**:
        *   **Description**: Retrieves the attendance history for a specific student. Can be filtered by course.
        *   **Auth**: JWT (Admin, Assigned Coordinator, Student themselves).
        *   **Response**: `200 OK` - Array of attendance record objects.

### 5.5. Data Export Endpoints (Reporting Service)
Base URL: `/api/v1/export/`

*   **`GET /export/course/{course_id}/attendance/xlsx/`**
    *   **Description**: Exports all attendance records for a specified course to an XLSX file.
    *   **Auth**: JWT (Admin, Assigned Coordinator of the course).
    *   **Response**: `200 OK` - XLSX file download.
    *   **Headers**: `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`

*   **`GET /export/course/{course_id}/attendance/pdf/`**
    *   **Description**: Exports all attendance records for a specified course to a PDF file.
    *   **Auth**: JWT (Admin, Assigned Coordinator of the course).
    *   **Response**: `200 OK` - PDF file download.
    *   **Headers**: `Content-Type: application/pdf`

*   **`GET /export/department/{department_id}/attendance-summary/xlsx/`**
    *   **Description**: Exports an attendance summary (e.g., aggregated statistics) for all courses within a specified department to an XLSX file.
    *   **Auth**: JWT (Admin role required).
    *   **Response**: `200 OK` - XLSX file download.
    *   **Headers**: `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`

### 5.6. Permissions Summary Table
This table provides a high-level overview of permissions for different user roles across key resources. "Coordinator" here generally refers to a user with the 'Faculty' role who is assigned to manage a course.

| Resource             | Admin        | Coordinator (Faculty) | Student      |
|----------------------|--------------|-----------------------|--------------|
| Users (all)          | CRUD         | Read (self)           | Read (self)  |
| Coordinator Approval | Approve/Reject| N/A                   | N/A          |
| Departments          | CRUD         | Read                  | None         |
| Courses              | CRUD         | RUD (assigned courses)| Read (enrolled courses)|
| Course Assignment    | Assign/Remove| N/A                   | N/A          |
| Enrollment           | Manage       | Manage (own courses)  | Self-Enroll/Unenroll |
| Attendance Windows   | CRUD         | CRUD (assigned courses)| Read (enrolled course windows)|
| QR Codes             | Read         | Read (assigned courses)| None (uses via check-in)|
| Check-in (Record)    | N/A          | N/A                   | Create       |
| Attendance Records   | Read         | Read (assigned courses)| Read (own records) |
| Data Export          | All          | Assigned Courses Only | None         |

**Note**:
*   `CRUD` stands for Create, Read, Update, Delete.
*   `RUD` stands for Read, Update, Delete.
*   Permissions can be more granular and context-dependent (e.g., a coordinator can only update courses they are assigned to).
*   The "Super Admin" role (if implemented as distinct from "Admin") would typically have all Admin permissions.
This detailed API specification will serve as a blueprint for the development of DRF serializers, views (ViewSets), and URL routing configurations.

## 6. Core Algorithms

This section details the critical operational logic for QR code management and the state transitions of attendance windows.

### 6.1. QR Code Generation and Validation

#### 6.1.1. Generation Process

The generation of QR codes is a critical step for enabling student check-ins. The system will use secure random tokens as the QR code data.

1.  **Trigger**:
    *   A new QR code is automatically generated when a new `AttendanceWindow` is successfully created via the `POST /courses/{course_id}/attendance-windows/` endpoint.
    *   An existing QR code for an `AttendanceWindow` can be refreshed (a new token generated) if an authorized user (Admin/Coordinator of the course) explicitly requests this action (e.g., through a dedicated API endpoint like `POST /attendance-windows/{id}/refresh-qr/` - *Note: this endpoint was not previously defined but is implied by this requirement*).

2.  **Uniqueness**:
    *   The `qr_data` (the secure random token) stored in the `QRCodes` table is guaranteed to be unique by a `UNIQUE` constraint on the column. This ensures each QR code presented for check-in maps to at most one active attendance session.

3.  **Data Payload (Conceptual - Not Embedded in QR Code itself)**:
    *   The QR code scanned by the student will *only* contain the secure random token (`qr_data`).
    *   The backend, upon receiving this token, will look up the associated details from the `QRCodes` and `AttendanceWindows` tables. These details include:
        *   `attendance_window_id`: The ID of the `AttendanceWindows` table entry (linked from `QRCodes.attendance_window_id`).
        *   `course_id`: The ID of the associated `Courses` table entry (linked from `AttendanceWindows.course_id`).
        *   `expires_at_ts`: The QR code's expiry time, derived from `QRCodes.expires_at` (which mirrors `AttendanceWindow.end_time`).

4.  **Format (of the `qr_data` token)**:
    *   The `qr_data` will be a cryptographically secure, URL-safe random string. For example, generated using Python's `secrets.token_urlsafe(32)` which produces a 32-byte random string. This string is what's embedded in the physical QR code image.

5.  **Security (Chosen Approach)**:
    *   The system uses the simpler and highly secure approach where the `qr_data` itself is a meaningless, secure random token.
    *   No sensitive information or business logic is embedded in the QR code. This prevents any client-side tampering or inference of session details from the QR code content. All validation and mapping logic resides securely on the backend.

6.  **Storage (`QRCodes` Table)**:
    *   When an `AttendanceWindow` is created (or its QR code is refreshed):
        *   A new entry is created in the `QRCodes` table.
        *   `attendance_window_id` (INTEGER): Foreign key referencing the `AttendanceWindows.id` of the associated window. This column has a UNIQUE constraint to ensure one QR code per window.
        *   `qr_data` (TEXT): The unique, secure random token (e.g., `secrets.token_urlsafe(32)`). This column has a UNIQUE constraint.
        *   `expires_at` (TIMESTAMP WITH TIME ZONE): This timestamp is copied from the `AttendanceWindow.end_time` and indicates when the QR code (and the window) is no longer valid for check-in.

#### 6.1.2. Validation Process (Student Check-in)

This process occurs when a student submits the scanned `qr_data` via the `POST /api/v1/attendance/check-in/` endpoint.

1.  **Input**:
    *   The student client sends a JSON request containing the `qr_data` string obtained from scanning the QR code.
    *   The request is authenticated using the student's JWT, so `request.user` is available.

2.  **Lookup**:
    *   The backend queries the `QRCodes` table: `SELECT id, attendance_window_id, expires_at FROM QRCodes WHERE qr_data = <submitted_qr_data>;`

3.  **Checks**:
    *   **Not Found**: If the query returns no record, the submitted `qr_data` is invalid. Reject the request with an HTTP `400 Bad Request` and a message like "Invalid QR Code."
    *   **Expired**:
        *   Check if `CURRENT_TIMESTAMP >= QRCodes.expires_at`.
        *   If true, the QR code has expired. Reject with HTTP `400 Bad Request` and "QR Code Expired" or "Attendance Window Closed."
    *   **Window Status**:
        *   Using the `attendance_window_id` from the looked-up `QRCodes` record, fetch the corresponding `AttendanceWindow`: `SELECT course_id, start_time, end_time, status FROM AttendanceWindows WHERE id = <attendance_window_id>;`
        *   If the `AttendanceWindow.status` is not 'open' (and not 'extended', if that state is actively used as an open equivalent), reject with HTTP `400 Bad Request` and "Attendance window is not open."
    *   **Course Enrollment**:
        *   Verify if the authenticated student (`request.user.id`) is enrolled in the `AttendanceWindow.course_id`. This involves checking the `Enrollments` table: `SELECT EXISTS (SELECT 1 FROM Enrollments WHERE user_id = <request.user.id> AND course_id = <course_id>);`
        *   If the student is not enrolled, reject with HTTP `403 Forbidden` and "Not enrolled in this course."
    *   **Duplicate Check-in**:
        *   Check if an `AttendanceRecord` already exists for the `request.user.id` and the `attendance_window_id`: `SELECT EXISTS (SELECT 1 FROM AttendanceRecords WHERE student_id = <request.user.id> AND attendance_window_id = <attendance_window_id>);`
        *   If a record exists, reject with HTTP `400 Bad Request` and "Already checked in for this session."

4.  **Success**: If all the above checks pass:
    *   Create a new entry in the `AttendanceRecords` table:
        *   `attendance_window_id`: The ID obtained from the `QRCodes` table.
        *   `student_id`: The ID of the authenticated student (`request.user.id`).
        *   `timestamp`: The current server timestamp (`CURRENT_TIMESTAMP`).
        *   `status`: Determine if 'present' or 'late'.
            *   Define a grace period (e.g., 5 minutes). This should be a configurable system setting.
            *   If `CURRENT_TIMESTAMP > (AttendanceWindow.start_time + grace_period)`: status is 'late'.
            *   Otherwise: status is 'present'.
    *   Return an HTTP `201 Created` response, potentially including details of the created attendance record as specified in the API documentation.

### 6.2. Attendance Window Logic & State Machine

The `AttendanceWindows` table has a `status` field that defines its current state.

#### 6.2.1. States

*   **`scheduled`**: The default initial state when an attendance window is created. The window is planned for a future time (`start_time`) but is not yet active for student check-ins.
*   **`open`**: The window is currently active. The `start_time` has been reached (or manually overridden), and the `end_time` has not yet passed. Students can check-in using the associated QR code.
*   **`closed`**: The window is no longer active. This can occur because the `end_time` has passed or an Admin/Coordinator has manually closed it. Check-ins are not permitted.
*   **`extended`** (Optional): This state can be used if an Admin/Coordinator extends the window beyond its original `end_time`. Functionally, it behaves like 'open' (allowing check-ins) but provides an explicit indication that the window's duration was modified. If not implemented as a distinct state, extending a window would involve updating its `end_time` and keeping the status as 'open' until the new `end_time` is reached. For simplicity, we can assume extending a window means updating `end_time` and it remains 'open' or transitions from 'closed' back to 'open' if extended after closure.

#### 6.2.2. Automated State Transitions (Celery Beat Tasks)

These tasks run periodically in the background, managed by Celery Beat, to automate the opening and closing of attendance windows.

1.  **Open Window Task**:
    *   **Trigger**: Configured to run at a regular interval (e.g., every minute).
    *   **Logic**:
        ```sql
        SELECT id FROM AttendanceWindows
        WHERE status = 'scheduled'
          AND CURRENT_TIMESTAMP >= start_time
          AND CURRENT_TIMESTAMP < end_time;
        ```
    *   **Action**: For each `id` returned by the query, update its status:
        ```sql
        UPDATE AttendanceWindows SET status = 'open' WHERE id = <found_id> AND status = 'scheduled';
        ```
        The `AND status = 'scheduled'` in the `UPDATE` ensures idempotency – it only updates windows that are still in the 'scheduled' state, preventing race conditions or redundant updates if a window was manually opened just before the task ran.
    *   **Notification (Optional)**: Could trigger a notification to faculty/enrolled students that the window is now open.

2.  **Close Window Task**:
    *   **Trigger**: Configured to run at a regular interval (e.g., every minute).
    *   **Logic**:
        ```sql
        SELECT id FROM AttendanceWindows
        WHERE (status = 'open' OR status = 'extended') -- Include 'extended' if used as a distinct open-like state
          AND CURRENT_TIMESTAMP >= end_time;
        ```
    *   **Action**: For each `id` returned by the query, update its status:
        ```sql
        UPDATE AttendanceWindows SET status = 'closed' WHERE id = <found_id> AND (status = 'open' OR status = 'extended');
        ```
        The `AND (status = 'open' OR status = 'extended')` ensures idempotency.
    *   **Notification (Optional)**: Could trigger a notification summary if needed.

#### 6.2.3. Manual State Transitions (API Endpoints)

Admins and assigned Coordinators have the authority to manually control the state of attendance windows via API endpoints:

*   **`POST /api/v1/attendance-windows/{id}/open/`**:
    *   Sets `AttendanceWindow.status` to 'open'.
    *   This allows opening a window before its scheduled `start_time` or reopening a 'closed' window (if business rules permit).
    *   If opened early, the `start_time` is *not* automatically changed by this manual action; the automated 'Open Window Task' would have handled it at `start_time` anyway if its status was `scheduled`. The manual override simply forces the `open` state.
*   **`POST /api/v1/attendance-windows/{id}/close/`**:
    *   Sets `AttendanceWindow.status` to 'closed'.
    *   This can be used to prematurely end an 'open' window.
*   **`PUT /api/v1/attendance-windows/{id}/` (for extending)**:
    *   To extend a window, an Admin/Coordinator would update the `end_time` to a future value.
    *   If the window is currently 'closed' but the new `end_time` is in the future, the status should also be updated to 'open' (or 'extended').
    *   If 'open', it remains 'open' with a new `end_time`.

#### 6.2.4. Activation/Deactivation

*   **Activation**: An attendance window becomes active for check-in when its `status` transitions to 'open' (or 'extended'). This can happen automatically via the Celery task at `start_time` or manually via an API call.
*   **Deactivation**: An attendance window becomes inactive for check-in when its `status` transitions to 'closed'. This can happen automatically via the Celery task when `end_time` is reached or manually via an API call.

#### 6.2.5. Department-based Access Control

*   As detailed in the API Specification and Permissions Summary Table, all actions related to creating, updating (including state changes), and deleting `AttendanceWindows` are subject to authorization.
*   DRF permission classes will ensure that:
    *   Only `Admin` users or `Coordinators` (Faculty) assigned to the specific `Course` (via `CourseCoordinatorLink`) to which an `AttendanceWindow` belongs can manage that window.
    *   This inherently enforces department-based access since courses are linked to departments, and coordinators are typically associated with courses within their department.

## 7. Notification System (Celery)

### 7.1. Introduction

The notification system is a critical component for timely communication with users. To ensure that sending notifications (primarily emails) does not degrade the performance and responsiveness of the web application's API endpoints, these operations will be handled asynchronously using Celery.

*   **Celery's Role**: Celery is a distributed task queue that allows the main application to offload time-consuming or scheduled tasks to background worker processes. This means when a notification needs to be sent, the API request can complete quickly by simply queuing the notification task, and a Celery worker will pick it up and process it independently.
*   **Message Broker**: Celery requires a message broker to manage the communication between the application and the workers. The system will use **Redis** (or RabbitMQ as an alternative, though Redis is preferred for simplicity if already used for caching) to store and transmit task messages.
*   **Celery Beat**: For tasks that need to run on a regular schedule (e.g., sending class reminders or checking for absentees), **Celery Beat** will be used. Celery Beat is a scheduler that periodically queues predefined tasks based on configured intervals or cron-like schedules.

### 7.2. Notification Types

The system will support the following types of notifications, primarily delivered via email:

1.  **Class Reminders**: Sent to enrolled students a configurable amount of time (e.g., 15-30 minutes) before a scheduled class session (i.e., before an `AttendanceWindow` opens).
2.  **Absentee Follow-ups**: Sent to students who were enrolled in a class session but were marked absent (or have no attendance record) after the `AttendanceWindow` has closed.
3.  **Registration Approval/Rejection**: Sent to users who applied for a 'Coordinator' (Faculty) role, informing them of the Admin's decision on their application.
4.  **Password Reset Emails**: Sent to users who request to reset their password, containing a secure token/link to complete the reset process.
5.  **Email Verification Emails**: Sent to new users upon registration (and on request) to verify their email address, containing a secure token/link.

### 7.3. Celery Task Definitions

A generic email sending task will form the core, supplemented by specific tasks for scheduling or more complex logic.

*   **Generic Email Task**:
    *   **Task Name**: `send_email_task`
    *   **Purpose**: To send an email to a specified user and record the notification attempt. This is the fundamental task used by other, more specialized tasks.
    *   **Parameters**:
        *   `user_id` (int): The ID of the recipient user.
        *   `subject` (str): The email subject.
        *   `message_body_html` (str): The HTML content of the email.
        *   `message_body_text` (str): The plain text content of the email (for compatibility).
        *   `notification_type` (str): A string identifying the type of notification (e.g., 'class_reminder', 'password_reset').
        *   `notification_record_id` (int, optional): The ID of the pre-created record in the `Notifications` table. This allows updating the status later.
    *   **Core Logic**:
        1.  Fetch the `User` object using `user_id` to get the recipient's email address. If not found, log an error and exit.
        2.  Construct the email using Django's email backend (e.g., `send_mail` or `EmailMultiAlternatives` for HTML/text). The backend will be configured to use an external SMTP service (e.g., SendGrid, Mailgun, AWS SES) for robust delivery.
        3.  Attempt to send the email.
        4.  If `notification_record_id` is provided, update the corresponding `Notifications` record:
            *   On success: Set `status` to 'sent', `sent_time` to `CURRENT_TIMESTAMP`.
            *   On failure: Set `status` to 'failed'. Log the error. (Celery's retry mechanism might handle transient failures before marking as 'failed').
        5.  If `notification_record_id` is not provided (e.g., for immediate one-off emails like password reset where the record might be created within the task), create a `Notifications` record with the outcome.
    *   **Error Handling**:
        *   Utilize Celery's built-in retry mechanisms for transient network issues (e.g., `autoretry_for`, `retry_kwargs`).
        *   Log persistent errors for debugging.
    *   **Example Task Signature**:
        ```python
        # tasks.py
        @shared_task(autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
        def send_email_task(user_id: int, subject: str, message_body_html: str, message_body_text: str, notification_type: str, notification_record_id: int = None):
            # ... logic as described above ...
            pass
        ```

*   **Coordinator Registration Status Notification Task**:
    *   **Task Name**: `notify_coordinator_registration_status`
    *   **Purpose**: To inform a user about the approval or rejection of their coordinator registration request.
    *   **Parameters**:
        *   `user_id` (int): The ID of the user whose registration status changed.
        *   `new_status` (str): The new status ('approved' or 'rejected').
    *   **Core Logic**:
        1.  Fetch the `User` object.
        2.  Based on `new_status`, determine the email subject and message content (using templates).
        3.  Create a `Notifications` record with type 'registration_status', status 'pending', user_id.
        4.  Queue `send_email_task` with the fetched user details, email content, and the new `Notifications` record ID.
    *   **Example Task Signature**:
        ```python
        @shared_task
        def notify_coordinator_registration_status(user_id: int, new_status: str):
            # ... logic to fetch user, prepare email content ...
            # notification_record = Notifications.objects.create(...)
            # send_email_task.delay(user_id, subject, html_body, text_body, 'registration_status', notification_record.id)
            pass
        ```

*   **Class Reminder Scheduling Task (Invoked by Celery Beat)**:
    *   **Task Name**: `schedule_class_reminders_for_upcoming_windows`
    *   **Purpose**: Periodically checks for attendance windows that are starting soon and schedules individual reminder emails for each enrolled student.
    *   **Parameters**: None (it queries for relevant windows).
    *   **Core Logic**:
        1.  Define a "reminder window" (e.g., windows starting between 15 and 30 minutes from now).
        2.  Query `AttendanceWindows` for `status='scheduled'` and `start_time` within this reminder window.
        3.  For each qualifying window:
            a.  Check if reminders have already been scheduled for this window (e.g., a flag on `AttendanceWindows` or by checking existing `Notifications`). If so, skip.
            b.  Fetch all `user_id`s from `Enrollments` for the window's `course_id`.
            c.  For each `user_id`:
                i.  Prepare reminder email subject and body (using templates, including course name, start time).
                ii. Create a `Notifications` record (user_id, type='class_reminder', status='pending', scheduled_time = window.start_time - reminder_config.PRE_WINDOW_REMINDER_MINUTES).
                iii. Schedule the actual email sending: `send_email_task.apply_async((user_id, subject, html_body, text_body, 'class_reminder', notification.id), eta=notification.scheduled_time)`.
            d.  Mark the `AttendanceWindow` as "reminders_scheduled" to prevent duplicate scheduling.
    *   **Example Task Signature**:
        ```python
        @shared_task
        def schedule_class_reminders_for_upcoming_windows():
            # ... logic ...
            pass
        ```

*   **Absentee Follow-up Scheduling Task (Invoked by Celery Beat)**:
    *   **Task Name**: `schedule_absentee_followups_for_closed_windows`
    *   **Purpose**: Periodically checks for attendance windows that have recently closed and schedules follow-up emails for students marked absent.
    *   **Parameters**: None.
    *   **Core Logic**:
        1.  Define a "recently closed" window (e.g., `status='closed'`, `end_time` was within the last hour, and `absentee_followup_sent` flag is false).
        2.  Query `AttendanceWindows` based on these criteria.
        3.  For each qualifying window:
            a.  Fetch all enrolled students for the window's `course_id`.
            b.  Fetch all `AttendanceRecords` for this window.
            c.  Identify students who are enrolled but do not have an `AttendanceRecord` (or whose record explicitly marks them as absent, if such a status exists).
            d.  For each absent student:
                i.  Prepare absentee follow-up email subject and body (using templates).
                ii. Create a `Notifications` record (user_id, type='absentee_followup', status='pending').
                iii. Queue `send_email_task.delay(user_id, subject, html_body, text_body, 'absentee_followup', notification.id)`.
            e.  Mark the `AttendanceWindow` as `absentee_followup_sent=True`.
    *   **Example Task Signature**:
        ```python
        @shared_task
        def schedule_absentee_followups_for_closed_windows():
            # ... logic ...
            pass
        ```

### 7.4. Celery Beat Schedules

Celery Beat will be configured to run the scheduling tasks at regular intervals:

*   **Class Reminder Scheduler**:
    *   **Task**: `schedule_class_reminders_for_upcoming_windows`
    *   **Frequency**: Every 5 minutes.
    *   **Logic**: As described in its task definition. This frequency ensures that windows are checked often enough to schedule reminders timely (e.g., 15-30 minutes before class).

*   **Absentee Follow-up Scheduler**:
    *   **Task**: `schedule_absentee_followups_for_closed_windows`
    *   **Frequency**: Every 15-30 minutes (or hourly, depending on desired promptness).
    *   **Logic**: As described in its task definition.

*   **Scheduled Report Generation (Example)**:
    *   If, for instance, admins require a daily summary report emailed to them:
    *   **Task**: `generate_and_email_daily_admin_summary_report`
    *   **Frequency**: Daily at a specified time (e.g., 01:00 AM).
    *   **Logic**: This task would aggregate data, generate a report (e.g., PDF/XLSX), and then use `send_email_task` to email it to a list of admin users.

### 7.5. Workflow for Notifications

*   **Registration Approval/Rejection**:
    1.  Admin user interacts with the API (`/api/v1/admin/users/{id}/approve-coordinator/` or `.../reject-coordinator/`).
    2.  The DRF view, after performing the primary action (updating user's `registration_status`), calls the Celery task: `notify_coordinator_registration_status.delay(user_id_of_coordinator, new_status)`.
    3.  A Celery worker process picks up the `notify_coordinator_registration_status` task.
    4.  The task prepares email content and queues the `send_email_task` with all necessary details including a new `Notifications` record ID.
    5.  Another (or the same) Celery worker picks up `send_email_task`, sends the email, and updates the `Notifications` record to 'sent' or 'failed'.

*   **Class Reminders (Detailed Example)**:
    1.  Celery Beat, according to its schedule (e.g., every 5 minutes), queues the `schedule_class_reminders_for_upcoming_windows` task.
    2.  A Celery worker picks up this task.
    3.  The task queries for `AttendanceWindows` starting, for example, in the next 15-30 minutes for which reminders haven't been scheduled.
    4.  For an identified `AttendanceWindow` (e.g., Window X for Course Y):
        a.  It fetches all students enrolled in Course Y.
        b.  For each student, it constructs the reminder message.
        c.  It creates a `Notifications` DB record: `{ user_id: student.id, type: 'class_reminder', status: 'pending', scheduled_time: WindowX.start_time - 15 minutes, message: '...' }`.
        d.  It then schedules the actual sending: `send_email_task.apply_async((student.id, subject, html_body, text_body, 'class_reminder', notification_record.id), eta=notification_record.scheduled_time)`. The `eta` ensures Celery holds the task until the desired delivery time.
    5.  The task marks Window X as "reminders_scheduled".
    6.  At the `eta`, a Celery worker picks up the `send_email_task` for a specific student.
    7.  It sends the email via the configured email backend.
    8.  It updates the corresponding `Notifications` record (e.g., status to 'sent', `sent_time` to now).

*   **Password Reset / Email Verification**:
    1.  User requests password reset or email verification via an API endpoint.
    2.  The API view generates a secure, unique token.
    3.  It constructs the email body (using a template) including the token/link.
    4.  It creates a `Notifications` record (type 'password_reset' or 'email_verification', status 'pending').
    5.  It calls `send_email_task.delay(user.id, subject, html_body, text_body, type, notification_record.id)`.
    6.  Celery worker picks up `send_email_task`, sends the email, and updates the `Notifications` record.

### 7.6. Email Templates

To ensure maintainability and ease of modification of email content, all emails sent by the system will use Django's template engine.
*   Templates will be created for each notification type (e.g., `class_reminder.html`, `absentee_followup.html`, `password_reset_email.html`).
*   These templates will allow for dynamic content (e.g., user names, course names, dates, verification links).
*   Both HTML and plain text versions of templates will be provided for broader email client compatibility.

### 7.7. Error Handling and Retries

Celery provides robust mechanisms for handling errors and retrying tasks:
*   **Automatic Retries**: As shown in the `send_email_task` signature, tasks can be configured with `autoretry_for` to automatically retry on specific exceptions (e.g., network issues when connecting to the SMTP server) up to a `max_retries` count with a `countdown` delay between retries.
*   **Logging**: All task executions, especially failures, will be thoroughly logged. This includes Celery's own logging and custom logging within tasks.
*   **Dead Letter Queue (DLQ)**: For tasks that fail persistently even after retries, Celery can be configured (though not explicitly detailed here) to move them to a DLQ. This allows administrators to inspect such failures and potentially manually retry or address the underlying issue.
*   **Notification Status**: The `Notifications` table's `status` field ('pending', 'sent', 'failed') will provide visibility into the outcome of each notification attempt.
This comprehensive approach ensures that notifications are handled reliably and efficiently without impacting the core application's performance.

## 8. Export Features (XLSX/PDF)

### 8.1. Introduction

For effective administration, analysis, and record-keeping, the system must provide functionality to export key data in common, portable formats. XLSX (Excel) and PDF are standard choices, catering to needs ranging from detailed data manipulation in spreadsheets to printable, formatted reports.

*   **XLSX Exports**: Ideal for users who need to perform further analysis, sorting, filtering, or integrate attendance data with other datasets.
    *   **Chosen Libraries**: `pandas` for data manipulation and structuring, and `openpyxl` as the engine for `pandas` to write to XLSX format. `pandas` provides a convenient `to_excel()` method.
*   **PDF Exports**: Suitable for generating official, read-only documents, summaries, and printable reports.
    *   **Chosen Library**: `ReportLab` is a powerful, industry-standard Python library for creating PDF documents programmatically. It offers fine-grained control over the document layout and content.

### 8.2. General Export Workflow

The process for exporting data, whether to XLSX or PDF, follows a consistent pattern:

1.  **Request**:
    *   An authorized user (typically an Admin or a Coordinator/Faculty for their assigned courses) initiates an export request via a dedicated API endpoint. Examples:
        *   `GET /api/v1/export/course/{course_id}/attendance/xlsx/`
        *   `GET /api/v1/export/course/{course_id}/attendance/pdf/`
        *   `GET /api/v1/export/department/{department_id}/attendance-summary/xlsx/`
    *   The request may include parameters like date ranges if applicable, though the current API specification focuses on course/department wide exports.

2.  **Authorization**:
    *   The system rigorously verifies the user's identity (via JWT) and permissions.
    *   Using DRF permission classes, it checks if the user has the authority to access and export the data for the requested scope (e.g., an Admin can export for any course, while a Coordinator can only export for courses they are assigned to).

3.  **Data Fetching**:
    *   The backend service (e.g., `Data Processing & Reporting Service`) retrieves the necessary data from the PostgreSQL database.
    *   This often involves complex SQL queries, potentially joining multiple tables. For instance, an attendance report for a course would require joining `AttendanceRecords` with `Users` (to get student names), `AttendanceWindows` (to get session details), and `Courses`.
    *   Example: Fetching all attendance records for a course, including student names, email, attendance window details (date, start/end times), check-in timestamp, and attendance status.

4.  **Data Processing & Aggregation (if needed)**:
    *   **Raw Data Reports**: For detailed exports like a full attendance log for a course, the fetched data might be directly structured for the report.
    *   **Summary Reports**: For reports like a "Department Attendance Summary," data needs aggregation. This is where `pandas` DataFrames are particularly useful. Operations could include:
        *   Calculating attendance percentages per student or per course.
        *   Counting total present, absent, or late instances.
        *   Grouping data by course, student, or date.
    *   The data is then transformed into a suitable structure (e.g., a list of dictionaries or a `pandas` DataFrame) for the file generation step.

5.  **File Generation**:
    *   **XLSX**:
        1.  The processed data (often a `pandas` DataFrame) is converted into an Excel file format.
        2.  `pandas.DataFrame.to_excel()` method is used, with `openpyxl` specified as the engine.
        3.  The file is generated in-memory (e.g., using `io.BytesIO`) to avoid temporary file writes to disk.
    *   **PDF**:
        1.  Data is formatted and rendered into a PDF document using `ReportLab`'s components.
        2.  This involves creating a document structure (e.g., `SimpleDocTemplate`), defining styles for paragraphs and tables, and adding elements like titles, paragraphs, and tables (often from `reportlab.platypus.Table`) to a 'story' list.
        3.  The PDF is also generated in-memory using `io.BytesIO`.

6.  **Response**:
    *   The generated file (from the in-memory buffer) is returned in the HTTP response.
    *   Crucial HTTP headers are set:
        *   `Content-Type`:
            *   For XLSX: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
            *   For PDF: `application/pdf`
        *   `Content-Disposition`: `attachment; filename="your_report_name.xlsx"` (or `.pdf`). This header prompts the browser to download the file.
    *   For the current scope, synchronous generation is assumed. The user makes a request and waits for the file to be generated and streamed back.

### 8.3. XLSX Generation Logic (using pandas/openpyxl)

#### 8.3.1. Course Attendance Report (XLSX)

*   **Target Endpoint**: `GET /api/v1/export/course/{course_id}/attendance/xlsx/`
*   **Data**:
    *   Fetch all `AttendanceRecords` associated with the given `course_id`.
    *   Join with `Users` table to get student `first_name`, `last_name`, `email`.
    *   Join with `AttendanceWindows` table to get `start_time` (labeled as 'Window Start Time') and `course_id` (to get course name via another join with `Courses` table).
    *   The `AttendanceRecords.timestamp` is the 'Check-in Time'.
    *   `AttendanceRecords.status` is 'Status (Present, Late)'.
    *   If a student is enrolled but has no `AttendanceRecord` for a window, they should be listed as 'Absent' for that window. This requires fetching all enrolled students and all windows, then carefully merging/aligning data.
*   **Structure (Columns in Excel sheet)**:
    1.  Student Name (e.g., "Doe, John")
    2.  Student Email
    3.  Course Name
    4.  Window Date (e.g., "2024-10-15")
    5.  Window Start Time (e.g., "09:00 AM")
    6.  Check-in Time (e.g., "09:03 AM" or N/A if absent)
    7.  Status (Present, Late, Absent)
*   **Implementation Sketch**:
    1.  Retrieve course information.
    2.  Fetch all `AttendanceWindows` for the course, ordered by `start_time`.
    3.  Fetch all `Enrollments` for the course, getting student details.
    4.  For each window, iterate through enrolled students:
        a.  Try to find a matching `AttendanceRecord`.
        b.  If found, record student details, window details, check-in time, and status.
        c.  If not found, record student details, window details, N/A for check-in, and "Absent" for status.
    5.  Compile this list of records into a `pandas` DataFrame.
        ```python
        # Example column names for DataFrame
        columns = ['Student Name', 'Student Email', 'Course Name', 'Window Date', 
                   'Window Start Time', 'Check-in Time', 'Status']
        report_data_df = pd.DataFrame(list_of_attendance_data_dicts, columns=columns)
        ```
    6.  Use `io.BytesIO` to create an in-memory buffer.
    7.  Use `pandas.ExcelWriter` with `openpyxl` engine:
        ```python
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            report_data_df.to_excel(writer, sheet_name='Attendance Report', index=False)
            # Optional: Access worksheet to apply styles using openpyxl
            # worksheet = writer.sheets['Attendance Report']
            # worksheet.column_dimensions['A'].width = 30 
            # ... other styling ...
        output.seek(0)
        ```
    8.  Return an `HttpResponse` with `output.getvalue()`, correct `Content-Type`, and `Content-Disposition`.

#### 8.3.2. Department Attendance Summary (XLSX Example)

*   **Target Endpoint**: `GET /api/v1/export/department/{department_id}/attendance-summary/xlsx/`
*   **Data**:
    *   Aggregate attendance data for all courses within the specified `department_id`.
    *   For each course: total enrolled students, overall attendance rate, total number of 'Present', 'Late', 'Absent' records.
*   **Structure (Columns in Excel sheet)**:
    1.  Course Code
    2.  Course Name
    3.  Total Enrolled Students
    4.  Total Attendance Windows
    5.  Average Attendance Rate (%)
    6.  Total Present Records
    7.  Total Late Records
    8.  Total Absent Records
*   **Implementation Sketch**:
    1.  Fetch all courses in the department.
    2.  For each course:
        a.  Count enrolled students.
        b.  Count total attendance windows.
        c.  Query `AttendanceRecords` to sum up present, late statuses.
        d.  Calculate absentees (enrolled * windows - (present + late)).
        e.  Calculate attendance rate.
    3.  Compile into a `pandas` DataFrame.
    4.  Generate XLSX as described above.

### 8.4. PDF Generation Logic (using ReportLab)

#### 8.4.1. Course Attendance Report (PDF)

*   **Target Endpoint**: `GET /api/v1/export/course/{course_id}/attendance/pdf/`
*   **Data**: Similar data to the XLSX version, focusing on individual attendance events.
*   **Structure**:
    *   **Title**: e.g., "Attendance Report - [Course Name]"
    *   **Subtitle**: e.g., "Department of [Department Name]"
    *   **Date of Generation**: Current date.
    *   **Report Period**: e.g., "For All Recorded Sessions" or specific date range if implemented.
    *   **Table(s)**:
        *   Preferably, one table per attendance window/session for clarity, or a continuous table.
        *   Columns: Student Name, Student Email, Check-in Time, Status (Present, Late, Absent).
        *   Header for each session: "Session: [Window Date] - [Window Start Time]"
    *   **Summary (Optional)**: Overall attendance rate for the course at the end.
*   **Implementation Sketch**:
    1.  Fetch data similarly to the XLSX version.
    2.  Create an `io.BytesIO` buffer.
    3.  Initialize `SimpleDocTemplate(buffer, pagesize=letter, title="Attendance Report")`.
    4.  Prepare a list of `Flowables` (the "story").
    5.  Define `ParagraphStyle` for titles, headers, normal text.
    6.  Define `TableStyle` for table headers and data cells (borders, alignment, fonts).
    7.  Iterate through attendance windows for the course:
        a.  Add a `Paragraph` for the session header.
        b.  Prepare table data (list of lists) for the current session's attendees.
        c.  Create a `Table` object with the data and style. Add to story.
        d.  Add a `Spacer` if needed.
    8.  Build the PDF: `doc.build(story)`.
    9.  Return an `HttpResponse` with `buffer.getvalue()`, correct `Content-Type`, and `Content-Disposition`.

### 8.5. Utility Classes/Functions

To promote DRY (Don't Repeat Yourself) principles and simplify report generation in views:

*   **`generate_xlsx_response(dataframe: pd.DataFrame, filename: str, sheet_name: str = 'Sheet1') -> HttpResponse:`**
    *   Takes a `pandas` DataFrame, desired filename, and sheet name.
    *   Handles `io.BytesIO` buffer creation, writing DataFrame to Excel (using `openpyxl`), and returning the `HttpResponse` with correct headers.
    *   Could also accept an optional callback for custom styling via `openpyxl`.

*   **`generate_pdf_response(story: list, filename: str, title: str = "Report") -> HttpResponse:`**
    *   Takes a ReportLab "story" (list of flowables), desired filename, and document title.
    *   Handles `io.BytesIO` buffer, `SimpleDocTemplate` creation, building the PDF, and returning the `HttpResponse`.
    *   Could accept optional parameters for page setup (margins, pagesize) or header/footer functions.

*   **Report-Specific Functions**:
    *   `create_course_attendance_data(course_id: int) -> pd.DataFrame:`
        *   Encapsulates the logic to fetch and structure data for the course attendance report.
    *   `build_course_attendance_pdf_story(course_id: int) -> list:`
        *   Encapsulates logic to fetch data and prepare the ReportLab story for the PDF.
    *   These functions would be called by the API views, which then pass the result to the generic response generators.

### 8.6. Performance Considerations for Large Exports

*   **Synchronous Generation (Current Scope)**: For moderately sized reports (e.g., a few thousand rows in Excel, dozens of pages in PDF), synchronous generation directly within the HTTP request-response cycle is often acceptable and simpler to implement.
*   **Streaming**: Django's `StreamingHttpResponse` can be used if the file is generated in chunks, which can reduce memory usage for very large files, but adds complexity.
*   **Asynchronous Generation (Future Consideration)**:
    *   For very large datasets (e.g., attendance history for an entire department over a year, full system audit logs), synchronous generation can lead to request timeouts and high server load.
    *   In such cases, the preferred approach is:
        1.  The API request (`POST /api/v1/export/request-large-report/`) initiates the report generation.
        2.  The system queues a Celery task to generate the report in the background.
        3.  The API immediately returns an HTTP `202 Accepted` response, possibly with a task ID or a link to check status.
        4.  Once the Celery task completes, the generated file is stored (e.g., in a private cloud storage bucket or a temporary location on the server).
        5.  The user is notified (e.g., via email from the Notification System or a UI update) with a link to download the file.
    *   This approach ensures that the user experience is not impacted by long-running export processes. While acknowledged, this is currently out of scope for the initial implementation unless requirements explicitly demand it for specific reports.
The combination of `pandas`/`openpyxl` for XLSX and `ReportLab` for PDF provides a robust and flexible foundation for meeting the application's data export requirements.

## 9. Security Considerations

Ensuring the security of the Smart Attendance & Analytics Web Application is paramount. This section outlines the key security measures and strategies that will be implemented in the backend.

### 9.1. Authentication - JWT (JSON Web Tokens)

Authentication will be handled using JSON Web Tokens (JWT), providing a stateless and secure method for verifying user identity.

*   **Statelessness**: JWTs are inherently stateless. Once a token is issued, the server does not need to store session information for that token. The token itself contains all necessary information for verification. For enhanced security, such as immediate token revocation upon logout or password change, a token blacklisting mechanism will be considered.
*   **Token Types**:
    *   **Access Token**: Short-lived (e.g., configurable, typically 15 minutes to 1 hour). This token is sent with each request to access protected API endpoints. It contains claims identifying the user and their role.
    *   **Refresh Token**: Long-lived (e.g., configurable, typically 7 to 30 days). This token is used to obtain a new access token when the current one expires, without requiring the user to re-enter their credentials. Refresh tokens must be stored securely by the client (e.g., in an HTTPOnly cookie if the client is browser-based, or in secure storage for mobile applications).
*   **JWT Structure**:
    *   **Header**: Specifies the token type (`JWT`) and the signing algorithm used (e.g., `HS256` or `RS256`). `HS256` (HMAC with SHA-256) will be used for its simplicity and good security, provided a strong secret key is used.
        ```json
        { "alg": "HS256", "typ": "JWT" }
        ```
    *   **Payload (Claims)**: Contains verifiable security statements, such as user identity and permissions. Standard claims like `exp` (expiration time) and `iat` (issued at) will be included, along with custom claims:
        *   `user_id`: The unique identifier of the user from the `Users` table.
        *   `role`: The name of the user's role (e.g., 'admin', 'coordinator', 'student'). This is critical for Role-Based Access Control (RBAC).
        *   `exp`: Expiration timestamp for the token.
        *   `iat`: Timestamp of when the token was issued.
        *   `jti`: JWT ID, a unique identifier for the token. This can be used for token blacklisting if implemented.
        ```json
        {
            "user_id": 123,
            "role": "coordinator",
            "exp": 1678886400, // Example expiration timestamp
            "iat": 1678882800, // Example issued-at timestamp
            "jti": "unique_token_identifier_string"
        }
        ```
    *   **Signature**: Verifies that the sender of the JWT is who it says it is and ensures that the message wasn't changed along the way. It is generated by signing the encoded header, the encoded payload, and a secret.
        `HMACSHA256(base64UrlEncode(header) + "." + base64UrlEncode(payload), secret_key)`
*   **Authentication Flow**:
    1.  **Login**: The user submits their credentials (e.g., email and password) to the `/api/v1/auth/login/` endpoint.
    2.  **Validation**: The server validates these credentials against the `Users` table, checking the hashed password.
    3.  **Token Issuance**: Upon successful validation, the server generates a JWT access token and a refresh token. Both tokens are signed using a strong, unique `SECRET_KEY` (managed via environment variables).
    4.  **Token Transmission**: The access and refresh tokens are returned to the client in the response body. The client is responsible for securely storing these tokens. The access token can be stored in memory (e.g., JavaScript variable), while the refresh token should be stored more persistently and securely (e.g., HTTPOnly cookie for web clients, or encrypted secure storage for mobile apps).
    5.  **Accessing Protected Resources**: For subsequent requests to protected API endpoints, the client includes the access token in the `Authorization` header using the `Bearer` scheme: `Authorization: Bearer <access_token>`.
    6.  **Token Verification**: On receiving a request, DRF's JWT authentication middleware (e.g., `rest_framework_simplejwt.authentication.JWTAuthentication`) automatically extracts the token. It verifies the token's signature using the `SECRET_KEY` and checks the `exp` claim to ensure it hasn't expired. If the token is valid, the user associated with the `user_id` claim is authenticated, and `request.user` and `request.auth` (the token object) are populated.
    7.  **Token Refresh**: When the access token expires (client receives a `401 Unauthorized` error), the client sends its refresh token to the `/api/v1/auth/token/refresh/` endpoint. The server validates the refresh token (checks if it's expired or revoked). If valid, a new access token is issued and returned to the client. If the refresh token is invalid or expired, the user must re-authenticate by providing their credentials again.
*   **Token Revocation/Blacklisting (Enhanced Security)**:
    *   While JWTs are stateless, effective and immediate revocation (e.g., upon user logout, password change, or administrative action disabling a user) requires a blacklist.
    *   A common strategy is to store the `jti` (JWT ID) claim of revoked tokens in a fast-access data store like Redis. The blacklist entry should have an expiry time matching the original token's remaining validity to prevent the blacklist from growing indefinitely.
    *   Custom DRF permission or authentication logic will be needed to check if a presented token's `jti` is in this blacklist. `django-rest-framework-simplejwt` provides mechanisms for blacklisting.
*   **Secret Key Management**: The `SECRET_KEY` used for signing JWTs is critical. It must be:
    *   Strong and cryptographically random.
    *   Unique for this application.
    *   Kept strictly confidential. It will be managed using environment variables (e.g., loaded from a `.env` file in development and set directly in the production environment) and **must not** be hardcoded into the source code.

### 9.2. Authorization - Role-Based Access Control (RBAC)

Authorization determines what an authenticated user is allowed to do. The system will implement RBAC using Django REST Framework's permission system.

*   **Role Definitions**: User roles (`Super Admin`, `Admin`, `Coordinator/Faculty`, `Student`) are clearly defined and stored in the `Roles` table in the database. The `role` claim in the JWT reflects the user's assigned role.
*   **Permission Mapping**: Permissions are associated with these roles. The "API Specification" section (specifically 5.6. Permissions Summary Table) provides a high-level overview of which roles can perform what actions on various resources.
*   **Implementation in DRF**:
    *   **Custom Permission Classes**: We will create custom DRF permission classes that check `request.user.role.name` (derived from the authenticated user object, which gets its role from the JWT `role` claim).
        ```python
        # backend/permissions.py (Conceptual Example)
        from rest_framework.permissions import BasePermission

        class IsAdminRole(BasePermission):
            message = "Only users with the 'Admin' role can perform this action."
            def has_permission(self, request, view):
                return request.user and request.user.is_authenticated and hasattr(request.user, 'role') and request.user.role.name == 'admin'

        class IsCoordinatorRole(BasePermission):
            message = "Only users with the 'Coordinator' role can perform this action."
            def has_permission(self, request, view):
                return request.user and request.user.is_authenticated and hasattr(request.user, 'role') and request.user.role.name == 'coordinator'
        
        class IsStudentRole(BasePermission):
            message = "Only users with the 'Student' role can perform this action."
            def has_permission(self, request, view):
                return request.user and request.user.is_authenticated and hasattr(request.user, 'role') and request.user.role.name == 'student'

        class IsCourseCoordinatorOrAdmin(BasePermission):
            message = "Only Admins or the assigned Coordinator can perform this action."
            def has_object_permission(self, request, view, obj): # obj is the Course instance
                if request.user.role.name == 'admin':
                    return True
                # Assuming obj is a Course and has a 'coordinators' M2M field or similar link
                return request.user.role.name == 'coordinator' and request.user in obj.coordinators.all()
        ```
    *   **View-Level and Object-Level Permissions**:
        *   **View-Level Permissions**: Applied at the APIView or ViewSet level using the `permission_classes` attribute. These control access to the entire endpoint or resource (e.g., only Admins can list all users).
        *   **Object-Level Permissions**: Implemented by overriding the `has_object_permission(self, request, view, obj)` method in a custom permission class. This is used to control access to specific instances of a model (e.g., a Coordinator can only update or delete courses they are directly assigned to manage).
*   **Department-Based Access**: For Coordinators, access to courses, attendance windows, and related data will typically be restricted to those within their department or those they are explicitly assigned to. This will be enforced through:
    *   Filtering querysets in views (e.g., `Course.objects.filter(department=request.user.department)`).
    *   Object-level permissions that check the `department_id` of the resource against the user's department (if coordinators are tied to a single department) or their specific course assignments.

### 9.3. Other Security Measures

Beyond authentication and authorization, several other security practices are essential:

*   **HTTPS**: All communication between clients (web/mobile) and the backend API must be encrypted using HTTPS. This will be enforced at the Nginx reverse proxy or load balancer level, which will handle SSL/TLS termination.
*   **Input Validation**:
    *   DRF serializers will be used for all incoming data validation. This includes checking data types, lengths, formats, and ensuring values are within expected ranges or choices.
    *   This is a primary defense against malformed requests and potential injection attacks (though the ORM handles SQLi primarily).
*   **Protection Against Common Web Vulnerabilities**:
    *   **SQL Injection (SQLi)**: Django's ORM inherently protects against most SQLi vulnerabilities by using parameterized queries. Raw SQL queries will be avoided. If absolutely necessary, they must use parameterization and extreme caution.
    *   **Cross-Site Scripting (XSS)**: The API primarily deals with JSON data, which significantly reduces XSS risks compared to server-rendered HTML. However, if any API responses could be directly rendered as HTML by the client, ensure proper escaping on the client-side. Django templates (if used for any server-side HTML, e.g., admin interface) have auto-escaping.
    *   **Cross-Site Request Forgery (CSRF)**: Django's built-in CSRF protection is primarily for session-based authentication. For JWT-based APIs where tokens are sent in the `Authorization` header, CSRF is generally not an issue for the API itself. However, ensure the frontend client correctly handles tokens to prevent other vulnerabilities.
*   **Error Handling**:
    *   The backend will be configured to not expose sensitive information (e.g., stack traces, internal configurations, raw error messages from databases) in API responses, especially in production. DRF's default exception handling converts errors into structured JSON responses. Debug mode (`DEBUG=True`) will be disabled in production.
*   **Dependency Management**:
    *   Regularly update all third-party libraries and Django itself to their latest stable versions to patch known vulnerabilities.
    *   Tools like `pip-audit` or GitHub's Dependabot will be used to monitor dependencies for known security issues.
*   **Environment Variable Management**:
    *   All sensitive configuration data (e.g., `SECRET_KEY`, database credentials, email server passwords, external API keys) will be stored as environment variables.
    *   A `.env` file will be used for local development (and added to `.gitignore`), while production environments will use platform-specific mechanisms for setting environment variables (e.g., Docker environment variables, Heroku config vars, AWS Parameter Store).
*   **Rate Limiting**:
    *   Implement rate limiting on API endpoints, especially sensitive ones like login (`/api/v1/auth/login/`), password reset (`/api/v1/auth/password/reset/`), QR code validation, and registration.
    *   This helps protect against brute-force attacks, dictionary attacks, and denial-of-service (DoS) attempts. DRF's built-in throttling or libraries like `django-ratelimit` can be used.
*   **Security Headers**:
    *   The Nginx reverse proxy will be configured to send security-enhancing HTTP headers, such as:
        *   `Strict-Transport-Security (HSTS)`: Enforces HTTPS.
        *   `X-Content-Type-Options: nosniff`: Prevents MIME-sniffing.
        *   `X-Frame-Options: DENY`: Protects against clickjacking.
        *   `Content-Security-Policy (CSP)`: Helps prevent XSS and other injection attacks (more relevant for frontends, but can be set for API responses too).
*   **Regular Security Audits**:
    *   Plan for periodic security reviews of the codebase and infrastructure.
    *   Consider automated security scanning tools and, budget permitting, manual penetration testing before major releases or annually.
*   **Logging and Monitoring**:
    *   Implement comprehensive logging of API requests, responses, errors, and significant security events (e.g., failed logins, authorization failures, password changes).
    *   Monitor logs for suspicious activity. This is crucial for detecting and investigating potential security incidents. (Refer to the "Monitoring and Logging" section for more details).

By implementing these security considerations comprehensively, we aim to build a robust and trustworthy backend system.

## 10. Sample Code (Django/DRF/Celery)

This section provides illustrative Python code snippets for key components of the backend. These are conceptual and serve to demonstrate the intended structure and logic. They may require further refinement, imports, and error handling in the actual implementation.

### 10.1. Custom User Model and Role Model (models.py)

```python
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone

class Role(models.Model):
    ADMIN = 'admin'
    COORDINATOR = 'coordinator'
    STUDENT = 'student'
    ROLE_CHOICES = [
        (ADMIN, 'Admin'),
        (COORDINATOR, 'Coordinator'),
        (STUDENT, 'Student'),
    ]
    name = models.CharField(max_length=50, choices=ROLE_CHOICES, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.get_name_display()

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, role_name=Role.STUDENT, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        
        # Ensure the role exists before trying to assign it.
        # This is important for data integrity and during initial data migrations/setups.
        try:
            role = Role.objects.get(name=role_name)
        except Role.DoesNotExist:
            # Fallback or error handling:
            # Option 1: Raise an error if a role is critical for user creation.
            # raise ValueError(f"Role '{role_name}' does not exist. Please create it first.")
            # Option 2: Try to get/create the role (less strict, useful for dev/testing but be careful in prod)
            # role, _ = Role.objects.get_or_create(name=role_name, defaults={'description': f'{role_name.capitalize()} role'})
            # For this example, let's assume roles are pre-populated or raise an error.
             raise ValueError(f"Role '{role_name}' not found. Ensure roles are populated.")


        user = self.model(email=email, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        # Superuser is always an Admin by role
        return self.create_user(email, password, role_name=Role.ADMIN, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    REGISTRATION_PENDING = 'pending'
    REGISTRATION_APPROVED = 'approved'
    REGISTRATION_REJECTED = 'rejected'
    REGISTRATION_STATUS_CHOICES = [
        (REGISTRATION_PENDING, 'Pending Approval'),
        (REGISTRATION_APPROVED, 'Approved'),
        (REGISTRATION_REJECTED, 'Rejected'),
    ]

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    
    # Ensure roles are protected from deletion if users are assigned to them.
    # Null=True allows for users (like superuser initially) not having a role via this FK immediately,
    # but it should typically be set. Blank=True if form validation allows it.
    role = models.ForeignKey(Role, on_delete=models.PROTECT, null=True, blank=True) 
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False) # For Django admin access
    is_verified = models.BooleanField(default=False) # Email verification
    
    registration_status = models.CharField(
        max_length=20,
        choices=REGISTRATION_STATUS_CHOICES,
        null=True, blank=True # Applicable mainly for coordinators during their approval process
    )
    
    date_joined = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    # REQUIRED_FIELDS typically includes fields prompted for when creating a user via createsuperuser.
    # Role is handled by our custom manager.
    REQUIRED_FIELDS = ['first_name', 'last_name'] 

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    # Add relevant properties or methods, e.g., to check role easily
    @property
    def is_admin(self):
        return self.role and self.role.name == Role.ADMIN
    
    @property
    def is_coordinator(self):
        return self.role and self.role.name == Role.COORDINATOR

    @property
    def is_student(self):
        return self.role and self.role.name == Role.STUDENT
```

### 10.2. Course, AttendanceWindow, AttendanceRecord Models (models.py - partial)

```python
# Continuing in models.py
# Assuming User and Role models are defined above

class Department(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    # head = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='headed_department', limit_choices_to={'role__name': Role.COORDINATOR})


    def __str__(self):
        return self.name

class Course(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses')
    # Coordinators are users with the 'coordinator' role.
    coordinators = models.ManyToManyField(User, related_name='coordinated_courses', limit_choices_to={'role__name': Role.COORDINATOR}, blank=True)
    # Enrolled students are users with the 'student' role.
    enrolled_students = models.ManyToManyField(User, related_name='enrolled_courses', limit_choices_to={'role__name': Role.STUDENT}, blank=True)
    
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

class AttendanceWindow(models.Model):
    SCHEDULED = 'scheduled'
    OPEN = 'open'
    CLOSED = 'closed'
    EXTENDED = 'extended' # Optional, can also be handled by just changing end_time and keeping status 'open'
    STATUS_CHOICES = [
        (SCHEDULED, 'Scheduled'), (OPEN, 'Open'),
        (CLOSED, 'Closed'), (EXTENDED, 'Extended')
    ]
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='attendance_windows')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=SCHEDULED)
    # Optional: flag to prevent re-sending notifications for reminders
    # reminder_sent = models.BooleanField(default=False) 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
        
    def __str__(self):
        return f"{self.course.name} ({self.start_time.strftime('%Y-%m-%d %H:%M')})"

class QRCode(models.Model):
    # OneToOneField ensures only one active QR code per attendance window.
    attendance_window = models.OneToOneField(AttendanceWindow, on_delete=models.CASCADE, related_name='qr_code')
    # Store the secure random token, not the image itself.
    qr_data = models.CharField(max_length=255, unique=True, help_text="Secure random token for QR code") 
    expires_at = models.DateTimeField() # Should align with window.end_time for validation consistency.
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"QR for {self.attendance_window}"

class AttendanceRecord(models.Model):
    PRESENT = 'present'
    LATE = 'late'
    # ABSENT status is typically implicit: an enrolled student with no AttendanceRecord for a given window.
    STATUS_CHOICES = [ (PRESENT, 'Present'), (LATE, 'Late') ]

    attendance_window = models.ForeignKey(AttendanceWindow, on_delete=models.CASCADE, related_name='attendance_records')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendance_records', limit_choices_to={'role__name': Role.STUDENT})
    timestamp = models.DateTimeField(default=timezone.now) # Actual check-in time
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    class Meta:
        unique_together = ('attendance_window', 'student') # Prevent duplicate check-ins for the same student in the same window.
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.student.email} - {self.status} for {self.attendance_window.course.code} at {self.timestamp}"
```

### 10.3. QR Generation/Validation Utility (utils.py or services.py)

```python
import secrets
from django.utils import timezone
from django.db import transaction
# Assuming models are in an app named, e.g., 'core_app'
# from core_app.models import QRCode, AttendanceWindow, Course, User, AttendanceRecord, Role 

# Placeholder for actual model imports - replace 'YourModelApp' with the actual app name
# from YourModelApp.models import QRCode, AttendanceWindow, Course, User, Role, AttendanceRecord

def generate_qr_token():
    """Generates a cryptographically secure URL-safe random token."""
    return secrets.token_urlsafe(32)

@transaction.atomic
def create_qr_code_for_window(attendance_window: AttendanceWindow):
    """
    Creates a new QR code for the given attendance window.
    Deletes any existing QR code for this window to ensure only one is active.
    """
    # Ensure previous QR for this window is deleted.
    QRCode.objects.filter(attendance_window=attendance_window).delete()
    
    token = generate_qr_token()
    qr = QRCode.objects.create(
        attendance_window=attendance_window,
        qr_data=token,
        expires_at=attendance_window.end_time  # Align QR code expiry with window end time
    )
    return qr

def validate_qr_and_create_attendance(qr_data_token: str, student: User):
    """
    Validates the QR code data and, if valid, creates an attendance record for the student.
    Returns a tuple (bool_success, message_or_record_object).
    """
    if not student.is_student: # Or check role name
        return False, "Only students can check in."

    try:
        # Use select_related for efficiency, as we'll access window and course details.
        qr_code = QRCode.objects.select_related('attendance_window__course').get(qr_data=qr_data_token)
        window = qr_code.attendance_window
        course = window.course

        # 1. Check QR Code Expiry (redundant if window status check is robust, but good for defense in depth)
        if qr_code.expires_at < timezone.now():
            return False, "QR Code has expired."

        # 2. Check Attendance Window Status
        if window.status != AttendanceWindow.OPEN: # Assuming 'EXTENDED' is also handled as 'OPEN' or window.end_time is updated
            return False, f"Attendance window is currently {window.get_status_display()}."

        # 3. Check if student is enrolled in the course
        if not course.enrolled_students.filter(id=student.id).exists():
            return False, "You are not enrolled in this course."

        # 4. Check for duplicate check-in
        if AttendanceRecord.objects.filter(attendance_window=window, student=student).exists():
            return False, "You have already checked in for this session."

        # 5. Determine attendance status (Present or Late)
        # Example: 5-minute grace period. This should ideally be a configurable setting.
        grace_period_duration_minutes = 5 
        grace_period_end = window.start_time + timezone.timedelta(minutes=grace_period_duration_minutes)
        
        current_time = timezone.now()
        attendance_status = AttendanceRecord.LATE if current_time > grace_period_end else AttendanceRecord.PRESENT
        
        # Create the attendance record within a transaction (if not already handled by a view-level transaction)
        with transaction.atomic():
            record = AttendanceRecord.objects.create(
                attendance_window=window,
                student=student,
                status=attendance_status,
                timestamp=current_time # Record the actual check-in time
            )
        return True, record
    
    except QRCode.DoesNotExist:
        return False, "Invalid QR Code provided."
    except Exception as e: 
        # It's good practice to log the actual exception 'e' here for debugging.
        # logger.error(f"Unexpected error during check-in for student {student.id} with QR data {qr_data_token}: {e}")
        return False, "An unexpected error occurred. Please try again or contact support."

```

### 10.4. DRF Serializers (serializers.py - partial)

```python
from rest_framework import serializers
# from .models import User, Course, AttendanceWindow, Role, Department # and other models

# Placeholder for actual model imports
# from YourModelApp.models import User, Course, AttendanceWindow, Role, Department

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['name', 'description']

class UserRegistrationSerializer(serializers.ModelSerializer):
    # Allow client to pass role name (e.g., "student", "coordinator")
    role = serializers.SlugRelatedField(
        slug_field='name', 
        queryset=Role.objects.all(),
        # error_messages for role not found can be customized here
    )
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['id', 'email', 'password', 'first_name', 'last_name', 'role']
        read_only_fields = ['id']

    def create(self, validated_data):
        role_instance = validated_data.pop('role') # role instance from SlugRelatedField
        
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            role_name=role_instance.name # Pass the role name string to manager
        )
        
        # Specific logic for coordinator registration
        if user.role.name == Role.COORDINATOR:
            user.registration_status = User.REGISTRATION_PENDING
            user.is_active = False # Or True, depending on admin approval policy
            user.save()
        return user

class UserDetailSerializer(serializers.ModelSerializer): # For retrieving user details
    role = RoleSerializer(read_only=True) # Show nested role details
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'role', 'is_active', 'is_verified', 'registration_status', 'date_joined']


class CourseSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    # To show more detail for coordinators/students, you could use UserDetailSerializer
    # coordinators = UserDetailSerializer(many=True, read_only=True)
    # enrolled_students = UserDetailSerializer(many=True, read_only=True)
    
    # For assigning by ID during create/update:
    coordinators = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.filter(role__name=Role.COORDINATOR), required=False)
    department = serializers.PrimaryKeyRelatedField(queryset=Department.objects.all())


    class Meta:
        model = Course
        fields = [
            'id', 'code', 'name', 'department', 'department_name', 
            'start_date', 'end_date', 'coordinators', 'enrolled_students'
        ]
        read_only_fields = ['id', 'department_name', 'enrolled_students'] # enrolled_students managed by separate endpoint usually

class AttendanceWindowSerializer(serializers.ModelSerializer):
    # qr_code_data = serializers.CharField(source='qr_code.qr_data', read_only=True) # Conditional display in view
    course_name = serializers.CharField(source='course.name', read_only=True)

    class Meta:
        model = AttendanceWindow
        fields = ['id', 'course', 'course_name', 'start_time', 'end_time', 'status'] # 'qr_code_data' can be added selectively
        read_only_fields = ['id', 'course_name']

class AttendanceCheckInSerializer(serializers.Serializer):
    qr_data = serializers.CharField(max_length=255, help_text="The token scanned from the QR code.")
    # location_data = serializers.JSONField(required=False) # Example for future use if location tracking is added
    
    def validate_qr_data(self, value):
        # Basic validation, more complex validation happens in the service/utility function
        if not value:
            raise serializers.ValidationError("QR data cannot be empty.")
        return value
```

### 10.5. DRF ViewSet Example (views.py - partial)

```python
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
# from .models import Course, AttendanceWindow, User, Role
# from .serializers import CourseSerializer, AttendanceWindowSerializer, AttendanceCheckInSerializer, UserDetailSerializer
# from .permissions import IsAdminRole, IsCoordinatorRole, IsStudentRole, IsCourseCoordinatorOrAdmin # Custom permissions
# from .utils import validate_qr_and_create_attendance, create_qr_code_for_window

# Placeholder for actual imports
# from YourModelApp.models import Course, AttendanceWindow, User, Role
# from YourModelApp.serializers import CourseSerializer, AttendanceWindowSerializer, AttendanceCheckInSerializer, UserDetailSerializer
# from YourModelApp.permissions import IsAdminRole, IsCoordinatorRole, IsStudentRole, IsCourseCoordinatorOrAdmin
# from YourModelApp.utils import validate_qr_and_create_attendance, create_qr_code_for_window


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all().select_related('department').prefetch_related('coordinators', 'enrolled_students')
    serializer_class = CourseSerializer
    # permission_classes = [permissions.IsAuthenticated] # Base permission

    def get_permissions(self):
        """Assign permissions based on action."""
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'manage_windows']: # manage_windows is a hypothetical custom action
             return [permissions.IsAuthenticated(), IsCourseCoordinatorOrAdmin()] # Custom permission for object-level
        # Default: Create, Delete - Admin only
        return [permissions.IsAuthenticated(), IsAdminRole()] 

    def get_queryset(self):
        """Filter queryset based on user role."""
        user = self.request.user
        if user.is_anonymous:
            return Course.objects.none()
        if user.is_admin: # Assumes User model has is_admin property
            return Course.objects.all().select_related('department').prefetch_related('coordinators', 'enrolled_students')
        if user.is_coordinator: # Assumes User model has is_coordinator property
            # Coordinators see courses they coordinate or are in their department(s) - adjust as per exact logic
            return Course.objects.filter(models.Q(coordinators=user) | models.Q(department__in=user.coordinated_departments.all())).distinct().select_related('department')
        if user.is_student: # Assumes User model has is_student property
            return user.enrolled_courses.all().select_related('department')
        return Course.objects.none()
            
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsStudentRole])
    def enroll(self, request, pk=None):
        course = self.get_object()
        student = request.user # request.user is the student due to IsStudentRole permission
        if student in course.enrolled_students.all():
            return Response({'message': 'You are already enrolled in this course.'}, status=status.HTTP_400_BAD_REQUEST)
        course.enrolled_students.add(student)
        # Potentially trigger a notification here
        return Response({'message': f'Successfully enrolled in {course.name}.'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsStudentRole])
    def unenroll(self, request, pk=None):
        course = self.get_object()
        student = request.user
        if student not in course.enrolled_students.all():
            return Response({'message': 'You are not enrolled in this course.'}, status=status.HTTP_400_BAD_REQUEST)
        course.enrolled_students.remove(student)
        return Response({'message': f'Successfully un-enrolled from {course.name}.'}, status=status.HTTP_200_OK)

class AttendanceViewSet(viewsets.GenericViewSet): 
    permission_classes = [permissions.IsAuthenticated] # Base permission for all actions

    @action(detail=False, methods=['post'], serializer_class=AttendanceCheckInSerializer, 
            permission_classes=[permissions.IsAuthenticated, IsStudentRole]) # Only students can check-in
    def check_in(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        qr_data = serializer.validated_data['qr_data']
        
        # The validate_qr_and_create_attendance utility handles all logic
        success, result_or_message = validate_qr_and_create_attendance(qr_data, request.user)
        
        if success:
            # result_or_message is the AttendanceRecord instance
            record = result_or_message
            return Response({
                "message": "Successfully checked in.",
                "record_id": record.id,
                "course": record.attendance_window.course.name,
                "status": record.get_status_display(),
                "timestamp": record.timestamp
            }, status=status.HTTP_201_CREATED)
        else:
            # result_or_message is the error message string
            return Response({"error": result_or_message}, status=status.HTTP_400_BAD_REQUEST)

    # Example: Action for a coordinator to get QR code for a window
    @action(detail=True, methods=['get'], serializer_class=AttendanceWindowSerializer, 
            url_path='window-qr/(?P<window_pk>[^/.]+)', # Custom URL for a nested-like resource
            permission_classes=[permissions.IsAuthenticated, IsCourseCoordinatorOrAdmin]) # Or specific coordinator permission
    def get_window_qr_code(self, request, pk=None, window_pk=None): # pk here would be course_id if nested under CourseViewSet
        try:
            # Assuming 'pk' is course_id passed from a CourseViewSet or similar
            # window = AttendanceWindow.objects.get(pk=window_pk, course_id=pk)
            # For this example, let's assume window_pk is the direct ID of the AttendanceWindow
            window = AttendanceWindow.objects.select_related('qr_code').get(pk=window_pk)
            # self.check_object_permissions(request, window.course) # Check permission on the course
            
            if not hasattr(window, 'qr_code') or not window.qr_code:
                 # If QR code doesn't exist, maybe create it on-the-fly
                 qr_instance = create_qr_code_for_window(window)
            else:
                 qr_instance = window.qr_code

            # Ensure QR code is not expired or window is still relevant
            if qr_instance.expires_at < timezone.now() and window.status == AttendanceWindow.CLOSED:
                 # Option to regenerate if expired and user has rights
                 # qr_instance = create_qr_code_for_window(window)
                 pass # Or just return existing expired one

            return Response({
                "attendance_window_id": window.id,
                "course_name": window.course.name,
                "qr_data": qr_instance.qr_data,
                "expires_at": qr_instance.expires_at,
                "window_status": window.get_status_display()
            })
        except AttendanceWindow.DoesNotExist:
            return Response({"error": "Attendance window not found."}, status=status.HTTP_404_NOT_FOUND)
        # except QRCode.DoesNotExist: # Handled by check or creation
        #     return Response({"error": "QR Code not found for this window."}, status=status.HTTP_404_NOT_FOUND)

```

### 10.6. Celery Task Example (tasks.py)

```python
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
# from .models import User, AttendanceWindow, Course, AttendanceRecord, Notifications, Role # and other models

# Placeholder for actual model imports
# from YourModelApp.models import User, AttendanceWindow, Notifications, Role

@shared_task(bind=True, max_retries=3, default_retry_delay=5 * 60) # bind=True to access self, retry in 5 mins
def send_email_task(self, user_id, subject, message_body, notification_type, notification_record_id=None):
    try:
        user = User.objects.get(id=user_id)
        # Do not send if no email, or user is inactive, or email not verified (optional policy)
        if not user.email or not user.is_active: # or not user.is_verified:
            if notification_record_id:
                # Update notification record to reflect failure due to user state
                Notifications.objects.filter(id=notification_record_id).update(status='failed_user_state')
            return f"Email not sent to user {user_id}: User has no email, is inactive, or email not verified."

        send_mail(
            subject,
            message_body, # Plain text message body
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False, # Raise exception on failure to trigger retry
            # html_message=... # Optionally add HTML content
        )
        if notification_record_id:
            Notifications.objects.filter(id=notification_record_id).update(status='sent', sent_time=timezone.now())
        return f"Email for '{notification_type}' sent to {user.email}"
    except User.DoesNotExist:
        # Log error: User not found, no point in retrying
        if notification_record_id:
             Notifications.objects.filter(id=notification_record_id).update(status='failed_user_not_found')
        return f"User with ID {user_id} not found. Cannot send email."
    except Exception as exc:
        # Log error: self.request.id is the Celery task ID
        # logger.error(f"Error sending email task {self.request.id} to user {user_id}: {exc}")
        if notification_record_id:
             # Mark as failed temporarily, retry might change it
             Notifications.objects.filter(id=notification_record_id).update(status='failed_retrying')
        raise self.retry(exc=exc) # Celery will retry based on task settings

@shared_task
def process_class_reminders():
    """
    Finds upcoming attendance windows and queues individual email reminder tasks for enrolled students.
    This task is intended to be run periodically by Celery Beat.
    """
    now = timezone.now()
    # Define the time window for reminders (e.g., classes starting in 15 to 20 minutes from now)
    reminder_start_boundary = now + timezone.timedelta(minutes=15)
    reminder_end_boundary = now + timezone.timedelta(minutes=20) # Adjust window as needed

    upcoming_windows = AttendanceWindow.objects.filter(
        status=AttendanceWindow.SCHEDULED, # Only for scheduled windows
        start_time__gte=reminder_start_boundary,
        start_time__lt=reminder_end_boundary,
        # reminder_sent=False  # Add a flag to AttendanceWindow model to avoid duplicate reminders
    ).select_related('course')

    for window in upcoming_windows:
        students_to_notify = window.course.enrolled_students.filter(is_active=True, role__name=Role.STUDENT) # Ensure student is active
        
        for student in students_to_notify:
            if student.email: # Check if student has an email
                subject = f"Reminder: Upcoming Class - {window.course.name}"
                message = (
                    f"Dear {student.first_name},\n\n"
                    f"This is a reminder for your class '{window.course.name}' "
                    f"scheduled to start at {window.start_time.strftime('%Y-%m-%d %H:%M')}.\n\n"
                    f"Please be ready to check in.\n\n"
                    f"Thank you."
                )
                notification_type = 'class_reminder'
                
                # Create a Notification record in the DB
                # notification = Notifications.objects.create(
                #    user=student,
                #    type=notification_type,
                #    message=message, # Or a summary
                #    status='pending',
                #    scheduled_time=(window.start_time - timezone.timedelta(minutes=15)) # Intended send time
                # )
                
                # Schedule the email task with ETA (Estimated Time of Arrival)
                # send_email_task.apply_async(
                #    args=[student.id, subject, message, notification_type, notification.id],
                #    eta=notification.scheduled_time 
                # )
                # For simplicity in this example, sending immediately if within window:
                send_email_task.delay(student.id, subject, message, notification_type)


        # Mark the window as reminders_sent to prevent duplicate processing
        # window.reminder_sent = True
        # window.save(update_fields=['reminder_sent'])
    if not upcoming_windows.exists():
        return "No upcoming windows found for reminders in the current slot."
    return f"Processed class reminders for {upcoming_windows.count()} windows."

```

### 10.7. Coordinator Approval Action (Conceptual - views.py)

```python
# This action would typically be part of a UserViewSet, accessible by Admins.
# from rest_framework.decorators import action
# from rest_framework.response import Response
# from rest_framework import status
# from .permissions import IsAdminRole # Assuming a UserViewSet with pk as user_id
# from .models import User, Role, Notifications 
# from .tasks import send_email_task

# @action(detail=True, methods=['post'], permission_classes=[IsAdminRole])
def approve_coordinator_registration(self, request, pk=None): # 'self' if in a ViewSet, pk is user_id
    try:
        user_to_approve = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

    if not user_to_approve.role or user_to_approve.role.name != Role.COORDINATOR:
        return Response({'error': 'This user is not pending approval as a Coordinator.'}, status=status.HTTP_400_BAD_REQUEST)
    
    if user_to_approve.registration_status == User.REGISTRATION_APPROVED:
        return Response({'message': 'Coordinator registration is already approved.'}, status=status.HTTP_200_OK)

    user_to_approve.registration_status = User.REGISTRATION_APPROVED
    user_to_approve.is_active = True # Activate the user upon approval
    user_to_approve.save(update_fields=['registration_status', 'is_active', 'updated_at'])

    # Send notification email
    subject = "Coordinator Registration Approved"
    message = (
        f"Dear {user_to_approve.first_name},\n\n"
        f"Your registration as a Coordinator for the Smart Attendance System has been approved. "
        f"You can now log in and access coordinator functionalities.\n\n"
        f"Thank you."
    )
    notification_type = 'registration_approved'
    
    # Create a Notification DB record (optional, but good for tracking)
    # notification = Notifications.objects.create(
    #    user=user_to_approve, 
    #    type=notification_type, 
    #    message="Registration approved by admin.", # Internal log message
    #    status='pending'
    # )
    # send_email_task.delay(user_to_approve.id, subject, message, notification_type, notification.id)
    send_email_task.delay(user_to_approve.id, subject, message, notification_type) # Simplified call

    return Response({'message': 'Coordinator registration approved successfully.'}, status=status.HTTP_200_OK)
```

### 10.8. Bulk Export View Example (views.py - partial)

```python
import pandas as pd
from io import BytesIO
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
# from rest_framework.decorators import action # If this is an action in a ViewSet
# from rest_framework.permissions import IsAuthenticated
# from .models import Course, AttendanceRecord, User
# from .permissions import IsCourseCoordinatorOrAdmin # Custom permission

# This could be a method in a CourseViewSet or a dedicated APIView.
# @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated, IsCourseCoordinatorOrAdmin], url_path='export-attendance-xlsx')
def export_course_attendance_xlsx(self, request, pk=None): # 'self' if in a class, pk is course_id
    course = get_object_or_404(Course, pk=pk)
    
    # Permission check (example if using DRF's check_object_permissions)
    # self.check_object_permissions(request, course) 

    # Fetch attendance records related to this course.
    # Optimize by selecting related student and window details to avoid N+1 queries.
    attendance_data = AttendanceRecord.objects.filter(attendance_window__course=course) \
                                          .select_related('student', 'attendance_window') \
                                          .order_by('attendance_window__start_time', 'student__last_name', 'student__first_name')
    
    if not attendance_data.exists():
        return HttpResponse(f"No attendance data found for course: {course.name}.", status=200) # Or 404 if preferred

    # Prepare data for DataFrame
    data_list = []
    for record in attendance_data:
        data_list.append({
            'Student Name': f"{record.student.first_name} {record.student.last_name}",
            'Student Email': record.student.email,
            'Window Start Time': record.attendance_window.start_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
            'Check-in Time': record.timestamp.strftime('%Y-%m-%d %H:%M:%S %Z'),
            'Status': record.get_status_display(), # Uses the choice display name
            'Course Code': course.code,
            'Course Name': course.name,
        })
    
    df = pd.DataFrame(data_list)
    
    # Create XLSX file in memory
    output_buffer = BytesIO()
    # Use with statement to ensure ExcelWriter is properly closed
    with pd.ExcelWriter(output_buffer, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=f"{course.code}_Attendance", index=False)
        # You can add more sheets or apply styling here if needed using writer.book or writer.sheets
    
    output_buffer.seek(0) # Rewind the buffer to the beginning
    
    response = HttpResponse(
        output_buffer.read(), # Read the buffer content
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{course.code}_attendance_report_{timezone.now().strftime("%Y%m%d")}.xlsx"'
    
    return response
```

These snippets should offer a foundational understanding of how different parts of the Django backend might be structured and interact.
