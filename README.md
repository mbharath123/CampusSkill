# CampusSkill – Student Skill Sharing & Learning Management System

A complete, database-driven peer-to-peer skill sharing platform built with **Python Flask** and **MySQL** for a DBMS capstone project.

---

## Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.10+ |
| MySQL Server | 8.0+ |
| pip | Latest |

---

## Quick Setup (Windows / VS Code)

### 1. Clone / open the project
```
cd campusskill
```

### 2. Create a virtual environment
```powershell
python -m venv venv
venv\Scripts\activate
```

### 3. Install Python dependencies
```powershell
pip install -r requirements.txt
```

### 4. Configure environment variables
Copy `.env.example` to `.env` and fill in your MySQL credentials:
```powershell
copy .env.example .env
```
Edit `.env`:
```
SECRET_KEY=any-long-random-string-here
DB_HOST=localhost
DB_PORT=3306
DB_NAME=campusskill
DB_USER=root
DB_PASSWORD=your_mysql_root_password
```

### 5. Create the MySQL database and tables
Open MySQL Workbench or run:
```powershell
mysql -u root -p < schema.sql
```
Or paste the contents of `schema.sql` into MySQL Workbench and execute.

### 6. Start the Flask application
```powershell
python app.py
```

### 7. Access the website
Open your browser and go to: **http://localhost:5000**

---

## Demo Accounts

| Email | Password |
|-------|----------|
| alice@demo.campusskill | Demo@1234 |
| bob@demo.campusskill | Demo@1234 |
| carol@demo.campusskill | Demo@1234 |

---

## Project Structure

```
campusskill/
├── app.py              ← Main Flask application (all routes)
├── config.py           ← Configuration class
├── db.py               ← MySQL connection pool helper
├── schema.sql          ← Database schema + sample data
├── requirements.txt    ← Python dependencies
├── .env.example        ← Environment variable template
├── README.md           ← This file
├── templates/
│   ├── base.html
│   ├── app_layout.html ← Authenticated page shell (sidebar + topbar)
│   ├── index.html      ← Landing page
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── profile.html
│   ├── public_profile.html
│   ├── skills.html
│   ├── explore.html
│   ├── requests.html
│   ├── sessions.html
│   ├── feedback.html
│   └── error.html
└── static/
    ├── css/style.css   ← Complete stylesheet
    └── js/main.js      ← Frontend interactions
```

---

## Features

- **Authentication** – Secure registration & login with bcrypt password hashing
- **Profile Management** – Edit name, department, year, bio
- **Skill Management** – Add / edit / delete skills with category & proficiency level
- **Explore Skills** – Search & filter by name, category, or level
- **Learning Requests** – Send, accept, reject, and cancel requests
- **Session Scheduling** – Schedule, edit, complete, or cancel sessions
- **Ratings & Feedback** – Star ratings and written feedback per session
- **Dashboard** – Live statistics from MySQL aggregate queries

---

## Troubleshooting

| Problem | Solution |
|---------|---------|
| `mysql.connector.errors.DatabaseError` | Check `.env` DB credentials and ensure MySQL is running |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` in the activated venv |
| Port 5000 in use | Change `port=5000` in `app.py` to `5001` |
| `schema.sql` error | Ensure MySQL ≥ 8.0; run `DROP DATABASE campusskill;` before re-running |
| Blank page / 500 error | Set `FLASK_DEBUG=1` in `.env` for detailed error output |
