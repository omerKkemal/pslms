<!-- LOGO IMAGE -->
<p align="center">
  <img src="screen_shot/logo.png" alt="pslms Logo" width="200">
</p>

<!-- MAIN TITLE -->
<p align="center">
  <img src="https://img.shields.io/badge/pslms-PRIMARY%20SCHOOL%20LMS-4CAF50?style=for-the-badge&logo=flask&logoColor=white&labelColor=1a1a2e" alt="pslms">
</p>

<!-- MODULE BADGES -->
<p align="center">
  <img src="https://img.shields.io/badge/Module-Admin%20Panel-4CAF50?style=flat-square&logo=admin">
  <img src="https://img.shields.io/badge/Module-Student%20Portal-2196F3?style=flat-square&logo=student">
  <img src="https://img.shields.io/badge/Module-Teacher%20Dashboard-FF9800?style=flat-square&logo=teacher">
  <img src="https://img.shields.io/badge/Module-Public%20Pages-9C27B0?style=flat-square&logo=web">
  <img src="https://img.shields.io/badge/Module-Authentication-607D8B?style=flat-square&logo=auth">
  <img src="https://img.shields.io/badge/Module-Event%20Handler-F44336?style=flat-square&logo=event">
</p>

<!-- VERSION BADGES -->
<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0-4CAF50?style=for-the-badge&logo=git&logoColor=white&labelColor=1a1a2e">
  <img src="https://img.shields.io/badge/Flask-2.0+-000000?style=for-the-badge&logo=flask&logoColor=white&labelColor=1a1a2e">
  <img src="https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white&labelColor=1a1a2e">
  <img src="https://img.shields.io/badge/SQLite-3-003B57?style=for-the-badge&logo=sqlite&logoColor=white&labelColor=1a1a2e">
  <img src="https://img.shields.io/badge/license-MIT-green?style=for-the-badge&logo=open-source&logoColor=white&labelColor=1a1a2e">
</p>

<!-- REPO STATS -->
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
              ║              Because schools need digital chaos too   ║
              ╚═══════════════════════════════════════════════════════╝
</pre>

---

## NAVIGATION MENU

<p align="center">
  <a href="#overview"><img src="https://img.shields.io/badge/Overview-4CAF50?style=for-the-badge&logo=readme&logoColor=white"></a>
  <a href="#features"><img src="https://img.shields.io/badge/Features-2196F3?style=for-the-badge&logo=readme&logoColor=white"></a>
  <a href="#screenshots"><img src="https://img.shields.io/badge/Screenshots-FF5722?style=for-the-badge&logo=readme&logoColor=white"></a>
  <a href="#installation"><img src="https://img.shields.io/badge/Installation-FF9800?style=for-the-badge&logo=readme&logoColor=white"></a>
  <a href="#directory-structure"><img src="https://img.shields.io/badge/Directory%20Structure-9C27B0?style=for-the-badge&logo=readme&logoColor=white"></a>
  <a href="#usage"><img src="https://img.shields.io/badge/Usage-607D8B?style=for-the-badge&logo=readme&logoColor=white"></a>
  <a href="#author"><img src="https://img.shields.io/badge/Author-F44336?style=for-the-badge&logo=readme&logoColor=white"></a>
  <a href="#license"><img src="https://img.shields.io/badge/License-green?style=for-the-badge&logo=readme&logoColor=white"></a>
</p>

---

## OVERVIEW

**pslms** is a Flask-based school management system. Because apparently managing a school with spreadsheets wasn't painful enough.  
It handles users, events, roles, and all the other stuff that makes primary schools run (or fall apart).  

Built with modular blueprints so you can pretend your code is organized.  
Supports Admin, Student, Teacher, and Public roles – because everyone needs to feel special.

---

## FEATURES (or "things it does when it's not crashing")

### Role-Based Access Control

| Role | Access Level | Features |
|:-----|:-------------|:---------|
| **Admin** | Full System Access | Dashboard, student/teacher management, section/subject assignment, resource management – basically everything |
| **Teacher** | Teaching Tools | Teacher dashboard, class management, student grading, resource sharing (for the responsible adults) |
| **Student** | Learning Portal | Student dashboard, view assignments, access learning materials (the reason this exists) |
| **Public** | Limited Access | View public pages, home, about, contact information (for the curious) |

### Core Features

| Feature | Description |
|:--------|:------------|
| **Modular Blueprint Architecture** | Flask blueprints because one big file is for amateurs |
| **Automated Database Setup** | Init script that does all the boring work for you |
| **Cross-Platform Setup** | Works on Linux, macOS, and Windows – because diversity |
| **Event Handling System** | For notifications, errors, and telling you when you messed up |
| **Logging System** | Because you'll want to know what broke and when |
| **Excel Integration** | For exporting data and pretending you're productive |
| **User Authentication** | Secure login/logout because security is a thing |

---

## SCREENSHOTS (because reading is hard)

<div align="center">

|                         |                         |
|:-----------------------:|:-----------------------:|
| ![Home](screen_shoots/home.png) | ![Login](screen_shoots/login.png) |
| **Home Page**<br>Welcome to the chaos | **Login Page**<br>Enter if you dare |
| ![Admin Panel](screen_shoots/admin_panel.png) | ![Dashboard](screen_shoots/Dashbord.png) |
| **Admin Panel**<br>Where the magic happens | **Dashboard**<br>Numbers that make you feel important |

</div>

---

## INSTALLATION (the part you actually care about)

### Prerequisites

- Python 3.8+ (because older versions are for dinosaurs)
- pip (obviously)
- Git (if you know how to use it)

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

#### Step 4: Initialize the database

```bash
bash init.sh
```

This script does everything. Because I'm nice like that.

---

## DIRECTORY STRUCTURE (the organized chaos)

```
Work/
│
├── app.py                          # The main event
├── init.py                         # Setup wizard
├── init.sh                          # Cross-platform magic
├── requirements.txt                   # Things you need
│
├── admin/                             # Admin stuff
├── student/                           # Student stuff
├── teacher/                           # Teacher stuff
├── login/                             # Login stuff
├── public/                            # Public stuff
├── event/                             # Event stuff
├── database/                          # Database stuff
├── utility/                           # Helper stuff
├── data/                              # Data files
├── static/                            # Pretty stuff
├── logs/                              # Error stuff
├── excel/                              # Export stuff
└── note/                               # Optional stuff
```

Yes, it's a lot of stuff. Deal with it.

---

## USAGE (the point of all this)

### Starting the Application

```bash
python app.py
```

On first run, you'll be prompted to set up admin credentials and default subjects.  
Don't skip it. You'll regret it.

### Accessing the Application

```
http://127.0.0.1:5000/
```

### Default User Roles

| Role | Credentials |
|:-----|:------------|
| **Admin** | Set during initialization |
| **Teacher** | Created by admin |
| **Student** | Created by admin or teacher |

### Available Routes

| URL | Access | Description |
|:----|:-------|:------------|
| `/` | Public | Home page – the gateway to everything |
| `/about` | Public | About page – because people are curious |
| `/login` | Public | Login page – enter if you dare |
| `/admin/*` | Admin Only | Admin dashboard – where the power lies |
| `/teacher/*` | Teacher Only | Teacher dashboard – for the responsible ones |
| `/student/*` | Student Only | Student portal – the reason this exists |

---

## TECH STACK (the things that make it work)

| Technology | Version | Purpose |
|:-----------|:-------:|:--------|
| Flask | 2.0+ | Web framework – the backbone |
| Python | 3.8+ | The language I pretend to know |
| SQLite | 3.x | Database – where data goes to die |
| Jinja2 | - | Template engine – makes HTML bearable |
| HTML5 | - | Frontend structure – the skeleton |
| CSS3 | - | Styling – makes it pretty |
| JavaScript | ES6 | Frontend magic – makes it interactive |

---

## FUTURE IMPROVEMENTS (maybe someday)

| Feature | Description |
|:--------|:------------|
| **Attendance System** | Track who showed up and who didn't |
| **Gradebook** | Comprehensive grading with analytics (for the overachievers) |
| **Parent Portal** | Because parents want to know what their kids are doing |
| **Calendar Integration** | School events without the paper calendar |
| **Messaging System** | Talk to teachers without leaving the app |
| **Report Cards** | Automated report generation (no more manual work) |
| **Mobile App** | Because everyone's on their phone anyway |
| **API Integration** | For the nerds who want to build on top |

---

## AUTHOR (the one to blame)

**Omer Kemal** – Full Stack Developer, caffeine addict, and professional bug creator.

- GitHub: [@omerKkemal](https://github.com/omerKkemal)
- Website: [https://www.omerkemal.com](https://www.omerkemal.com)
- Twitter: [@omerKkemal](https://twitter.com/omerKkemal)
- LinkedIn: [omer-kemal](https://linkedin.com/in/omer-kemal)

Found a bug? Open an issue.  
Rude comments? Go touch grass.

---

## LICENSE

MIT License – do whatever you want. Just don't blame me when it breaks.

Copyright (c) 2024 Omer Kemal

---

<!-- FOOTER -->

<p align="center">
  <img src="https://img.shields.io/badge/pslms-Primary%20School%20LMS-4CAF50?style=for-the-badge">
  <img src="https://img.shields.io/badge/Flask-2.0+-000000?style=for-the-badge">
  <br>
  <sub>© 2024 pslms. MIT License. Go outside. Touch grass. Or don't. I'm not your mom.</sub>
</p>
