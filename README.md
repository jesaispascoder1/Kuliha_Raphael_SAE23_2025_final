# Le_Backlog - Game Collection Manager

**Le_Backlog** is a web application  that helps you manage your video game collection. Keep track of your games, their status, share them with friends, and discover new games through public listings and suggestions.

-----------------------------------------------------------------------------------------------------------------------------------------------


## Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Option](#installation-without-internet)
- [Database Configuration](#database-configuration)
- [Running the Application](#running-the-application)
- [Usage & URLs](#Urls)
- [CSV Import Format](#csv-import-format)
- [Security](#security)
- [Error Handling](#error-handling)

-----------------------------------------------------------------------------------------------------------------------------------------------

## Features

-Personal game list: add, manage, and track your games (manual entry or from public list)
-Game status management: Not Started, In Progress, Completed, Abandoned
-Public game list
-Game suggestion system (users can suggest games to the admin)
-Random game picker (from personal or public list)
-Game sharing between users
-CSV import/export functionality for games
-Admin interface: CRUD for games and users, suggestions, CSV import/export
-Statistics and data visualization (charts)
-User authentication system

-----------------------------------------------------------------------------------------------------------------------------------------------

## Project Structure
Kuliha_Raphael_SAE23_2025_final/
│
├── app.py               # Main web app entry point (CherryPy)
├── schema.sql           # SQL dump: table creation, constraints, initial data
│
├── /templates/          # HTML (Jinja2) templates
│   ├── index.html
│   ├── ma_liste.html
│   └── admin.html
│
├── libs/                # Required dependencies 
│
├── /db/
│   ├── models.py        # Data access, all database operations
│   └── init_db.py       # Script to initialize database (tables, sample data)
│
├── test.csv             # Example of valid CSV
├── requirements.txt     # Python dependencies
└── README.md            # This documentation (English)

-----------------------------------------------------------------------------------------------------------------------------------------------

## Prerequisites

Before installing the application, make sure you have:

1. Python 3.8 or higher installed
   - Download from [Python.org](https://www.python.org/downloads/)
   - Make sure to check "Add Python to PATH" during installation on Windows

2. pip (Python package installer)
   - Usually comes with Python, but if not installed:
   ```bash
   # On Windows:
   python -m ensurepip --default-pip
   # On Linux:
   sudo apt-get install python3-pip  # For Ubuntu/Debian
   sudo dnf install python3-pip      # For Fedora
   ```

3. MySQL Server installed
   - Download from [MySQL Community Downloads](https://dev.mysql.com/downloads/mysql/)
   - Remember to note down the root password during installation

-----------------------------------------------------------------------------------------------------------------------------------------------

## Installation

1. **Extract** the project folder (`KulihA_Raphael_SAE23_2025`).

2. **Open a terminal in the project root** (where `app.py` is).

3. **(Recommended)** Setup a Python virtual environment:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

4. **Install dependencies**:
```bash
pip install -r requirements.txt
```
or 

Install the required dependencies individually:
```bash
pip install cherrypy>=18.8.0
pip install jinja2>=3.1.2
pip install mysql-connector-python>=8.0.33
pip install bcrypt>=4.0.1
pip install matplotlib>=3.7.1
```

### [Option]
## Installation without Internet

If you have no Internet access (for example in an exam room), a folder `libs/` is provided in the ZIP.

To install all dependencies without any online connection, use:
```bash
pip install --break-system-packages --no-index --find-links=libs -r requirements.txt
```

-----------------------------------------------------------------------------------------------------------------------------------------------

## Database Configuration

1. Install MySQL Server if not already installed

2. [Option] Create a new database:
```sql
CREATE DATABASE sae23_kuliha CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

3. Update the database configuration in `db/models.py` and `db/init_db.py`:
```python
DB_CONFIG = {
    'host': "localhost",
    'user': "your_username",
    'password': "your_password",
    'database': "sae23_kuliha",
    'charset': "utf8mb4",
    'use_unicode': True
}
```

4. Initialize the database by running:
```bash
python init_db.py
```
_(You should see a confirmation message in the terminal)_
This script will create all necessary tables and populate them with initial data.

-----------------------------------------------------------------------------------------------------------------------------------------------

## Running the Application

Start the web server:
```bash
python app.py
```

The application will be available at `http://localhost:8080`

-----------------------------------------------------------------------------------------------------------------------------------------------

## URLs

- Public interface: `http://localhost:8080/`
- Administration interface: `http://localhost:8080/admin` (only accessible after logging in as an administrator through the public interface)

-----------------------------------------------------------------------------------------------------------------------------------------------

## CSV Import Format

To import games via CSV, use the following format:
```csv
Titre,Description,Temps,Genre,Editeur,Plateforme
Game Title,Game Description,10,Action,Publisher,Platform
```

Fields:
- Titre: Game title (required)
- Description: Game description (optional)
- Temps: Average completion time in hours (optional)
- Genre: Game genre (optional)
- Editeur: Publisher (optional)
- Plateforme: Platform (optional)

-----------------------------------------------------------------------------------------------------------------------------------------------

## Security

- Passwords are hashed using bcrypt
- Session management is handled by CherryPy
- Admin privileges are required for administrative functions
- CSRF protection is implemented for forms

-----------------------------------------------------------------------------------------------------------------------------------------------

## Error Handling

The application includes comprehensive error handling for:
- Database connection issues
- Authentication failures
- Invalid data submissions
- File upload errors
- Permission issues