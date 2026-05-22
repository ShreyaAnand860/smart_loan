# SmartLoan

SmartLoan is a full-stack Django fintech application for AI-powered loan eligibility, application review, document verification, EMI management, dashboards, and REST APIs.

## Stack

- Django 5, Django REST Framework, Simple JWT
- SQLite for development, PostgreSQL-ready through `DATABASE_URL`
- Scikit-learn, Pandas, NumPy for loan approval prediction
- Bootstrap, custom CSS, responsive dashboards, Chart.js
- Docker and production-oriented environment settings

## Quick Start

```bash
cd smartloan
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

Demo accounts created by `seed_data`:

- `customer` / `SmartLoan@123`
- `officer` / `SmartLoan@123`

## Required Run Commands

The project is designed to run after:

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

`seed_data` is optional but recommended because it creates loan categories and demo users.

## AI Model

The ML package lives in `ml_model/`. It includes:

- Synthetic sample dataset
- Logistic Regression training
- Random Forest training
- Best-model selection
- Joblib persistence
- Approval probability, risk score, risk level, and rejection reasons

The saved model is generated automatically on first prediction if missing. You can train it manually:

```bash
python -m ml_model.train_model
```

## Features

- Register, login, logout, forgot password
- Customer, loan officer, and admin roles
- Loan application form with PAN/Aadhaar validation
- AI eligibility prediction
- Officer approval/rejection workflow
- Secure document upload validation
- EMI calculator and EMI schedule generation
- Payment, credit score, and notification models
- Customer, officer, and admin dashboard metrics
- Admin panel filters and CSV exports
- REST APIs with JWT auth and throttling
- Dark/light responsive fintech UI

## Docker

```bash
cd docker
docker compose up --build
```

This starts Django with PostgreSQL.

## Production Notes

Set a strong `DJANGO_SECRET_KEY`, disable `DJANGO_DEBUG`, configure `DJANGO_ALLOWED_HOSTS`, set `DATABASE_URL`, and use a real email backend. Behind HTTPS, set `SESSION_COOKIE_SECURE=True`, `CSRF_COOKIE_SECURE=True`, `SECURE_SSL_REDIRECT=True`, and an HSTS value such as `SECURE_HSTS_SECONDS=31536000`. Static files are collected in the Docker image; for high-traffic production, serve media from object storage.
