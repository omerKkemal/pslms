<!-- LOGO IMAGE - Add your logo here -->
<p align="center">
  <img src="screen_shot/logo.png" alt="pslms Logo" width="200">
</p>

<!-- MAIN TITLE -->
<p align="center">
  <img src="https://img.shields.io/badge/pslms-PRIMARY%20SCHOOL%20LMS-4CAF50?style=for-the-badge&logo=flask&logoColor=white&labelColor=1a1a2e" alt="pslms">
</p>

<!-- MODULE BADGES - CLEAN HEADER -->
<p align="center">
  <img src="https://img.shields.io/badge/Module-Admin%20Panel-4CAF50?style=flat-square&logo=admin">
  <img src="https://img.shields.io/badge/Module-Student%20Portal-2196F3?style=flat-square&logo=student">
  <img src="https://img.shields.io/badge/Module-Teacher%20Dashboard-FF9800?style=flat-square&logo=teacher">
  <img src="https://img.shields.io/badge/Module-Public%20Pages-9C27B0?style=flat-square&logo=web">
  <img src="https://img.shields.io/badge/Module-Authentication-607D8B?style=flat-square&logo=auth">
  <img src="https://img.shields.io/badge/Module-Event%20Handler-F44336?style=flat-square&logo=event">
</p>

<!-- SPECIFIED BADGES ONLY -->
<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0-4CAF50?style=for-the-badge&logo=git&logoColor=white&labelColor=1a1a2e">
  <img src="https://img.shields.io/badge/Flask-2.0+-000000?style=for-the-badge&logo=flask&logoColor=white&labelColor=1a1a2e">
  <img src="https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white&labelColor=1a1a2e">
  <img src="https://img.shields.io/badge/SQLite-3-003B57?style=for-the-badge&logo=sqlite&logoColor=white&labelColor=1a1a2e">
  <img src="https://img.shields.io/badge/license-MIT-green?style=for-the-badge&logo=open-source&logoColor=white&labelColor=1a1a2e">
</p>

<!-- REPO STATS BADGES -->
<p align="center">
  <img src="https://api.visitorbadge.io/api/visitors?path=omerKkemal%2FWork&countColor=%234CAF50&style=for-the-badge" alt="Visitors">
  <img src="https://img.shields.io/github/stars/omerKkemal/Work?style=for-the-badge&logo=github&color=gold&labelColor=1a1a2e" alt="Stars">
  <img src="https://img.shields.io/github/forks/omerKkemal/Work?style=for-the-badge&logo=github&color=blue&labelColor=1a1a2e" alt="Forks">
</p>

---

<!-- ASCII ART HEADER -->
<pre align="center">
              ╔═══════════════════════════════════════════════════════╗
              ║  ██████╗ ███████╗██╗     ███╗   ███╗███████╗          ║
              ║  ██╔══██╗██╔════╝██║     ████╗ ████║██╔════╝          ║
              ║  ██████╔╝███████╗██║     ██╔████╔██║███████╗          ║
              ║  ██╔═══╝ ╚════██║██║     ██║╚██╔╝██║╚════██║          ║
              ║  ██║     ███████║███████╗██║ ╚═╝ ██║███████║          ║
              ║  ╚═╝     ╚══════╝╚══════╝╚═╝     ╚═╝╚══════╝          ║
              ║                                                       ║
              ║        Primary School Learning Management System v1.0 ║
              ║              Flask-based Modular School Management    ║
              ╚═══════════════════════════════════════════════════════╝
</pre>

---

## 📋 NAVIGATION MENU

<p align="center">
  <a href="#overview"><img src="https://img.shields.io/badge/Overview-4CAF50?style=for-the-badge&logo=readme&logoColor=white"></a>
  <a href="#features"><img src="https://img.shields.io/badge/Features-2196F3?style=for-the-badge&logo=readme&logoColor=white"></a>
  <a href="#installation"><img src="https://img.shields.io/badge/Installation-FF9800?style=for-the-badge&logo=readme&logoColor=white"></a>
  <a href="#directory-structure"><img src="https://img.shields.io/badge/Directory%20Structure-9C27B0?style=for-the-badge&logo=readme&logoColor=white"></a>
  <a href="#usage"><img src="https://img.shields.io/badge/Usage-607D8B?style=for-the-badge&logo=readme&logoColor=white"></a>
  <a href="#author"><img src="https://img.shields.io/badge/Author-F44336?style=for-the-badge&logo=readme&logoColor=white"></a>
  <a href="#license"><img src="https://img.shields.io/badge/License-green?style=for-the-badge&logo=readme&logoColor=white"></a>
</p>

---

## OVERVIEW

**pslms (Primary School Learning Management System)** is a modular Flask-based web application for managing users and events in a school setting. It supports roles such as **Admin, Student, Teacher, and Public**. The app includes user authentication, event handling, database setup, and logging, with scripts to automate environment and database initialization.

The system is designed to be scalable, maintainable, and easy to deploy, making it ideal for primary schools looking to digitize their administrative and learning processes.

---

## FEATURES

### Role-Based Access Control

| Role | Access Level | Features |
|:-----|:-------------|:---------|
| **Admin** | Full System Access | Dashboard, student/teacher management, section/subject assignment, resource management |
| **Teacher** | Teaching Tools | Teacher dashboard, class management, student grading, resource sharing |
| **Student** | Learning Portal | Student dashboard, view assignments, access learning materials |
| **Public** | Limited Access | View public pages, home, about, contact information |

### Core Features

| Feature | Description |
|:--------|:------------|
| **Modular Blueprint Architecture** | Flask blueprints for Admin, Student, Teacher, Public, and Login modules |
| **Automated Database Setup** | Python initialization script (`init.py`) for creating tables, admin account, and default subjects |
| **Cross-Platform Setup** | Shell script (`init.sh`) for Linux, macOS, and Windows environment initialization |
| **Event Handling System** | Dedicated event module for system notifications, error messages, and success alerts |
| **Logging System** | Automatic log directory creation for organized data management |
| **Excel Integration** | Excel directory creation for data export and reporting |
| **User Authentication** | Secure login/logout functionality for all user roles |

---

## INSTALLATION

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Git (for cloning the repository)

### Step-by-Step Installation

#### Step 1: Clone the repository

```bash
git clone https://github.com/omerKkemal/Work.git
cd Work
```

#### Step 2: Set up a virtual environment

**Linux / macOS:**
```bash
python -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

#### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

#### Step 4: Initialize the database and environment

```bash
bash init.sh
```

This script will:
- Run the Python initialization script (`init.py`)
- Create necessary database tables
- Set up default admin account
- Insert default subjects
- Create required directories (logs, excel, etc.)
- Launch the application

---

## DIRECTORY STRUCTURE

```
Work/
│
├── 📄 app.py                          # Main Flask application entry point
├── 📄 init.py                          # Python initialization script
├── 📄 init.sh                           # Cross-platform setup script
├── 📄 requirements.txt                   # Python dependencies
│
├── 📂 admin/                             # Admin module (blueprint)
│   ├── 📄 __init__.py
│   ├── 📄 routes.py                       # Admin routes
│   └── 📂 templates/                       # Admin templates
│
├── 📂 student/                           # Student module (blueprint)
│   ├── 📄 __init__.py
│   ├── 📄 routes.py                       # Student routes
│   └── 📂 templates/                       # Student templates
│
├── 📂 teacher/                           # Teacher module (blueprint)
│   ├── 📄 __init__.py
│   ├── 📄 routes.py                       # Teacher routes
│   └── 📂 templates/                       # Teacher templates
│
├── 📂 login/                             # Authentication module (blueprint)
│   ├── 📄 __init__.py
│   └── 📄 routes.py                       # Login/logout routes
│
├── 📂 public/                            # Public module (blueprint)
│   ├── 📄 __init__.py
│   └── 📄 routes.py                       # Public routes (home, about)
│
├── 📂 event/                             # Event handling module
│   ├── 📄 __init__.py
│   └── 📄 event.py                        # Error and success handlers
│
├── 📂 database/                          # Database management
│   ├── 📄 __init__.py
│   ├── 📄 setup.py                        # Table creation
│   └── 📄 seed.py                          # Default data insertion
│
├── 📂 utility/                           # Helper functions
│   ├── 📄 __init__.py
│   ├── 📄 setting.py                       # Configuration settings
│   ├── 📄 processer.py                     # Data processors
│   └── 📄 filters.py                       # Template filters
│
├── 📂 data/                               # Static data files
│   ├── 📄 subjects.json
│   └── 📄 grades.json
│
├── 📂 static/                             # Static assets
│   ├── 📂 css/
│   ├── 📂 js/
│   └── 📂 images/
│
├── 📂 logs/                               # Application logs (auto-generated)
│   └── 📄 app.log
│
├── 📂 excel/                              # Excel exports (auto-generated)
│
└── 📂 note/                               # Optional note-taking feature
```

---

## USAGE

### Starting the Application

```bash
python app.py
```

On first run, follow the prompts in the terminal to complete the setup, such as:
- Inserting default subjects
- Configuring admin credentials
- Setting up academic terms

### Accessing the Application

Once running, the application will be accessible at:

```
http://127.0.0.1:5000/
```

### Default User Roles

| Role | Default Credentials (after setup) |
|:-----|:----------------------------------|
| **Admin** | Set during initialization |
| **Teacher** | Created by admin |
| **Student** | Created by admin or teacher |

### Available Routes

| URL | Access | Description |
|:----|:-------|:------------|
| `/` | Public | Home page |
| `/about` | Public | About page |
| `/login` | Public | Login page for all users |
| `/admin/*` | Admin Only | Admin dashboard and management |
| `/teacher/*` | Teacher Only | Teacher dashboard and tools |
| `/student/*` | Student Only | Student portal |

---

## TECH STACK

| Technology | Version | Purpose |
|:-----------|:-------:|:--------|
| Flask | 2.0+ | Web framework |
| Python | 3.8+ | Core programming language |
| SQLite | 3.x | Database |
| Jinja2 | - | Template engine |
| HTML5 | - | Frontend structure |
| CSS3 | - | Styling |
| JavaScript | ES6 | Frontend interactions |

---

## FUTURE IMPROVEMENTS

| Feature | Description |
|:--------|:------------|
| **Attendance System** | Track student attendance with reports |
| **Gradebook** | Comprehensive grading system with analytics |
| **Parent Portal** | Dedicated access for parents to monitor children |
| **Calendar Integration** | School event calendar with reminders |
| **Messaging System** | Internal communication between teachers and parents |
| **Report Cards** | Automated report card generation |
| **Mobile App** | Companion mobile application |
| **API Integration** | RESTful API for third-party integrations |

---

## AUTHOR

<div align="center">
  
**Omer Kemal**  
*Full Stack Developer & Education Technology Specialist*

| Platform | Link |
|:---------|:-----|
| GitHub | [@omerKkemal](https://github.com/omerKkemal) |
| Website | [https://www.omerkemal.com](https://www.omerkemal.com) |
| Twitter | [@omerKkemal](https://twitter.com/omerKkemal) |
| LinkedIn | [omer-kemal](https://linkedin.com/in/omer-kemal) |

For questions, feedback, or contributions, please open an issue on GitHub or contact through the channels above.

</div>

---

## LICENSE

This project is licensed under the **MIT License**.

```
MIT License

Copyright (c) 2024 Omer Kemal

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

<!-- FOOTER -->
<p align="center">
    <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=400&size=16&duration=3000&pause=500&color=4CAF50&center=true&vCenter=true&width=400&lines=Primary+School+Learning+Management;Built+with+Flask+and+Python;Open+Source+Education+Project;Empowering+Schools+Digitally" alt="Footer Typing SVG" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/pslms-Primary%20School%20LMS-4CAF50?style=for-the-badge">
  <img src="https://img.shields.io/badge/Flask-2.0+-000000?style=for-the-badge">
  <br>
  <sub>© 2024 pslms. MIT License.</sub>
</p>

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&height=100&section=footer&gradient=4CAF50,2196F3,FF9800"/>
</p>
