# Work

## Overview

Work is a modular Flask-based web application for managing users and events, supporting roles such as Admin, Student, Teacher, and Public. The app includes user authentication, event handling, database setup, and logging, with scripts to automate environment and database initialization.

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

## Directory Structure

- `app.py` — Main Flask application
- `init.py` — Database and directory initialization
- `init.sh` — Environment and app start script
- `admin/`, `student/`, `teacher/`, `login/`, `public/`, `event/` — Feature blueprints
- `database/` — Database management code
- `data/`, `static/`, `public/`, `utility/`, `note/` — Supporting assets and utilities

## Author

- Omer Kemal  
- [GitHub](https://github.com/johndoe)  
- [Website](https://www.johndoe.com)  
- [Twitter](https://twitter.com/JohnDoe)

## License

See the `LICENSE` file for details.

---

**Note:** Update social and contact links as needed. For a full file list and latest changes, visit the [repository on GitHub](https://github.com/omerKkemal/Work).