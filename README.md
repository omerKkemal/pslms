# Work

## Overview

pslms is a modular Flask-based web application for managing users and events in a school setting. It supports roles such as Admin, Student, Teacher, and Public. The app includes user authentication, event handling, database setup, and logging, with scripts to automate environment and database initialization.

## Features

- Modular Flask blueprints (Admin, Student, Teacher, Public, Login)
- Automated database setup and initialization (`init.py`, `init.sh`)
- Cross-platform environment setup script (Linux, macOS, Windows)
- Logging and Excel directory creation for organized data management
- Blueprint registration for scalable feature extension

## Installation

1. **Clone the repository:**
    ```bash
    git clone https://github.com/omerKkemal/Work.git
    cd Work
    ```

2. **Set up a virtual environment and install dependencies:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

3. **Initialize the database and environment:**
    ```bash
    bash init.sh
    ```
    - This will run the Python initialization and launch the app.

## Usage

- Start the Flask app:
    ```bash
    python app.py
    ```
- On first run, follow prompts in the terminal to complete setup (e.g., inserting default subjects).
- The app will be accessible at `http://127.0.0.1:5000/` by default.

## Directory Structure and Explanation

- `app.py` — Main Flask application entry point, where all blueprints are registered.
- `init.py` — Python initialization script for setting up database tables, admin account, and required directories.
- `init.sh` — Shell script for environment setup and app initialization (cross-platform).
- `admin/` — Handles all admin features: dashboard, student/teacher management, section/subject assignment, resource management, and more.
- `student/` — Contains routes and logic for student-specific features (e.g., student dashboard).
- `teacher/` — Contains routes and logic for teacher-specific features (e.g., teacher dashboard).
- `login/` — Handles user authentication (login/logout) for all roles.
- `public/` — Provides public-facing routes and pages (e.g., home, about).
- `event/` — Handles system notifications and pages, such as unauthorized, error, and success messages.
- `database/` — All database setup and management code: directory creation, table creation, admin account, and default subject insertion.
- `utility/` — Utility functions and helpers, including settings, data processors, and template filters used by other modules.
- `data/` — Stores static data files (JSON, etc.) used for configuration, such as subjects and grades.
- `static/` — Holds static files like CSS, JavaScript, and images for web templates.
- `note/` — (Optional) Likely used for note-taking or related features.
- `public/` (as folder) — May contain static or additional public-facing assets.
- `__pycache__/` — Python's cache directory for compiled bytecode (auto-generated).

## Author

- Omer Kemal  
- [GitHub](https://github.com/johndoe)  
- [Website](https://www.johndoe.com)  
- [Twitter](https://twitter.com/JohnDoe)

## License

See the `LICENSE` file for details.

---

**Note:**  
- Update social and contact links as needed.  
- For a full file list and latest changes, visit the [repository on GitHub](https://github.com/omerKkemal/Work).
