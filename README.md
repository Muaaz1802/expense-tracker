# Expense Tracker

A modern, feature-rich expense tracking API built with **FastAPI** and **PostgreSQL**, designed to help users manage personal finances efficiently. Track expenses, organize them by categories, set budgets, and generate insightful financial reports.

## Overview

The Expense Tracker API provides a complete backend solution for expense management with user authentication, categorization, budgeting, and comprehensive reporting features. It supports multiple payment methods, offers advanced filtering and pagination, and delivers insightful financial analytics.

### Key Features

- **User Authentication** - Secure JWT-based authentication with refresh token support
- **Expense Management** - Create, read, update, and delete expenses with rich metadata
- **Category Management** - Organize expenses with custom categories and color coding
- **Budget Planning** - Set budgets with period-based alerts and threshold monitoring
- **Financial Reports** - Generate summaries, category breakdowns, and export to CSV
- **Advanced Filtering** - Filter by date range, amount, payment method, and category
- **Pagination & Sorting** - Efficient data retrieval with customizable sorting
- **Payment Methods** - Support for Cash, Credit Card, Debit Card, UPI, Net Banking

---

## Deployed Link

>
> ```
<!-- > Production: https://your-domain.com -->

## Local Setup Instructions

### Prerequisites

- Python 3.10+
- PostgreSQL 12+
- pip (Python package manager)
- Git

### Step 1: Clone the Repository

```bash
git clone git@github.com:Muaaz1802/expense-tracker.git
# or
git clone https://github.com/Muaaz1802/expense-tracker.git
cd expense-tracker
```

### Step 2: Create a Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Linux/macOS:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Create a `.env` file in the project root directory:

```env
# Database Configuration
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/expense_tracker

# Security
# generate using 
python -c "import secrets; print(secrets.token_hex(32))"

SECRET_KEY=your-secret-key-here-min-32-chars
```

**Database Setup:**

```bash
# Create a PostgreSQL database
createdb expense_tracker

# Run migrations
alembic upgrade head
```

### Step 5: Run the Application

```bash
# Start the development server
uvicorn app.main:app --reload

# Server will be available at http://localhost:8000
```

### Step 6: Access the API

- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **Alternative Documentation**: http://localhost:8000/redoc (ReDoc)
- **Home Page**: http://localhost:8000

---

## API Documentation

> **Authentication Required**: All endpoints require a JWT token in the `Authorization` header:
> ```
> Authorization: Bearer <access_token>
> ```

### API Routes

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---|
| **Authentication** | | | |
| `POST` | `/api/v1/auth/register` | Register a new user | No |
| `POST` | `/api/v1/auth/login` | Login and get access/refresh tokens | No |
| `POST` | `/api/v1/auth/refresh` | Refresh access token | Yes |
| **Expenses** | | | |
| `GET` | `/api/v1/expenses` | List expenses with filters & pagination | Yes |
| `POST` | `/api/v1/expenses` | Create a new expense | Yes |
| `PUT` | `/api/v1/expenses/{expense_id}` | Update an expense (full update) | Yes |
| `PATCH` | `/api/v1/expenses/{expense_id}` | Partially update an expense | Yes |
| `DELETE` | `/api/v1/expenses/{expense_id}` | Delete an expense | Yes |
| **Categories** | | | |
| `GET` | `/api/v1/categories` | List all user categories | Yes |
| `POST` | `/api/v1/categories` | Create a new category | Yes |
| `PUT` | `/api/v1/categories/{category_id}` | Update a category | Yes |
| `DELETE` | `/api/v1/categories/{category_id}` | Delete a category | Yes |
| **Budgets** | | | |
| `GET` | `/api/v1/budgets` | List all user budgets | Yes |
| `POST` | `/api/v1/budgets` | Create a new budget | Yes |
| `PUT` | `/api/v1/budgets/{budget_id}` | Update a budget | Yes |
| `DELETE` | `/api/v1/budgets/{budget_id}` | Delete a budget | Yes |
| **Reports** | | | |
| `GET` | `/api/v1/reports/summary` | Get expense summary (with date filters) | Yes |
| `GET` | `/api/v1/reports/by-category` | Get expenses breakdown by category | Yes |
| `GET` | `/api/v1/reports/export` | Export expenses to CSV | Yes |

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend Framework** | FastAPI 0.135+ |
| **Database** | PostgreSQL 12+ |
| **ORM** | SQLAlchemy 2.0 |
| **Authentication** | JWT (PyJWT) |
| **Server** | Uvicorn |
| **Async Support** | asyncpg, asyncio |
| **Password Hashing** | Passlib + bcrypt |
| **Validation** | Pydantic 2.0 |
| **Migration Tool** | Alembic |

---

## Project Structure

```
expense-tracker/
├── app/
│   ├── core/              # Security & authentication logic
│   ├── models/            # SQLAlchemy ORM models
│   ├── routers/           # API endpoint definitions
│   ├── schemas/           # Pydantic request/response schemas
│   ├── services/          # Business logic layer
│   ├── config.py          # Configuration settings
│   ├── database.py        # Database connection setup
│   ├── dependencies.py    # Dependency injection
│   └── main.py            # FastAPI app initialization
├── alembic/               # Database migrations
├── templates/             # HTML templates
├── requirements.txt       # Python dependencies
├── alembic.ini            # Alembic configuration
└── .env                   # Environment variables (local only)
```

---

## Security Features

- **Password Hashing**: Passwords are hashed using bcrypt
- **JWT Authentication**: Secure token-based authentication
- **Refresh Tokens**: Separate refresh tokens for enhanced security
- **CORS Enabled**: Cross-Origin Resource Sharing configured
- **Input Validation**: Pydantic schemas validate all inputs
- **Database Connection Pooling**: Async connection management

---

## Deployment Considerations

### Environment Variables
Ensure the following are set in production:

```env
DATABASE_URL=postgresql+asyncpg://user:password@host:port/dbname
SECRET_KEY=<strong-random-key-min-32-chars>
DEBUG=false
```

### Database Migrations
```bash
# Apply migrations in production
alembic upgrade head
```

### Running in Production
```bash
# Use Gunicorn with Uvicorn workers
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

