# Student Course Management API

A secure REST API for managing students, courses, and enrollments. Built with FastAPI, SQLAlchemy, SQLite, JWT authentication, and role-based access control.

## Features

- Student registration with secure password hashing
- JWT-based login
- Admin and student roles
- Admin-only course creation
- Student course enrollment
- Duplicate enrollment prevention
- Course capacity validation
- Student-specific enrollment history
- Interactive Swagger API documentation

## Tech Stack

- Python
- FastAPI
- SQLAlchemy
- SQLite
- Pydantic
- JWT (`python-jose`)
- Argon2 password hashing (`pwdlib`)
- Uvicorn

## API Endpoints

| Method | Endpoint | Access | Description |
| --- | --- | --- | --- |
| GET | `/` | Public | API welcome message |
| GET | `/health` | Public | Health check |
| POST | `/students` | Public | Register a student |
| POST | `/auth/login` | Public | Log in and receive JWT token |
| GET | `/students` | Admin | View all students |
| GET | `/courses` | Public | View all courses |
| POST | `/courses` | Admin | Create a course |
| POST | `/enrollments` | Student/Admin | Enroll in a course |
| GET | `/enrollments/me` | Student/Admin | View own enrollments |
| GET | `/enrollments` | Admin | View all enrollments |

## Run Locally

```bash
py -3.13 -m venv .venv