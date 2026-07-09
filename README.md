<!-- LOGO IMAGE -->
<p align="center">
  <img src="screen_shot/logo.png" alt="pslms Logo" width="200">
</p>

<p align="center">
  <strong>pslms</strong><br>
  <em>Because spreadsheets are for amateurs</em>
</p>

---

## Welcome to the Circus

This is pslms – a Flask-based school management system that I built because someone asked me to and I couldn't say no.  
It handles students, teachers, admins, events, and all the other nonsense that comes with running a primary school.

Is it perfect? No.  
Does it work? Mostly.  
Will I fix the bugs? Eventually.  

---

## Why Does This Exist?

Let's be honest – managing a school with paper and Excel is a nightmare.  
Someone had to do something about it. That someone was me.  
Now you can manage students, teachers, classes, and subjects without losing your mind.

**What it does:**
- Lets admins control everything (because someone has to)
- Gives teachers tools to manage classes (they deserve it)
- Gives students access to learning materials (the whole point)
- Lets the public see what's happening (transparency or whatever)

**What it doesn't do:**
- Make you coffee
- Grade papers for you
- Fix your life choices

---

## The Cast of Characters

| Role | What They Can Do | Why They're Here |
|:-----|:-----------------|:-----------------|
| **Admin** | Everything. Literally everything. | Someone has to keep the chaos in check |
| **Teacher** | Manage classes, grade students, share resources | The actual heroes of this story |
| **Student** | View assignments, access materials | The reason this whole thing exists |
| **Public** | Look at the homepage, maybe read the about page | For the curious ones |

---

## The Mess Inside (Directory Structure)

```
Work/
│
├── app.py                          # Where it all begins
├── init.py                         # Does the boring setup stuff
├── init.sh                         # For people who hate typing
├── requirements.txt                # Things you need (yes, all of them)
│
├── admin/                          # The boss's office
├── student/                        # The kids' corner
├── teacher/                        # The grown-ups' zone
├── login/                          # The gatekeeper
├── public/                         # The window to the world
├── event/                          # Where errors go to haunt you
├── database/                       # Where your data sleeps
├── utility/                        # The unsung heroes
├── data/                           # The boring stuff
├── static/                         # The pretty stuff
├── logs/                           # Your new best friends
├── excel/                          # For the spreadsheet lovers
└── note/                           # If you feel like writing
```

I know it's a lot. Just roll with it.

---

## Getting It Running (Without Breaking Everything)

### What You Need

- Python 3.8 or higher (no excuses)
- pip (I shouldn't have to tell you this)
- Git (you know what it is)

### Step 1: Get The Code

```bash
git clone https://github.com/omerKkemal/Work.git
cd Work
```

### Step 2: Hide Your Dependencies

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

### Step 3: Install The Noise

```bash
pip install -r requirements.txt
```

### Step 4: Let The Magic Happen

```bash
bash init.sh
```

This does everything.  
Database creation, default data, admin account – the works.  
If you skip this, you'll have a bad time.

---

## Starting The Thing

```bash
python app.py
```

Then open your browser and go to:

```
http://127.0.0.1:5000/
```

Congrats. You made it.

---

## Where You Can Go

| URL | Who Can Go | What's There |
|:----|:-----------|:-------------|
| `/` | Anyone | The homepage – start here |
| `/about` | Anyone | The "about" page – if you care |
| `/login` | Anyone with credentials | Where you prove you belong |
| `/admin/*` | Admins only | Where the power lives |
| `/teacher/*` | Teachers only | Where the teaching happens |
| `/student/*` | Students only | Where the learning happens |

---

## Screenshots (Because You Asked)

<div align="center">

|                         |                         |
|:-----------------------:|:-----------------------:|
| ![Home](screen_shoots/home.png) | ![Login](screen_shoots/login.png) |
| **Home Page** | **Login Page** |
| ![Admin Panel](screen_shoots/admin_panel.png) | ![Dashboard](screen_shoots/Dashbord.png) |
| **Admin Panel** | **Dashboard** |

</div>

They look fine. Stop asking.

---

## What's Under The Hood

| Technology | What It Does |
|:-----------|:-------------|
| Flask | Makes the web part work |
| Python | The language I'm stuck with |
| SQLite | Where data lives (for now) |
| Jinja2 | Makes HTML bearable |
| HTML5 | The skeleton |
| CSS3 | Makes it not ugly |
| JavaScript | Makes it do things |

---

## What's Next (Maybe)

Some day, if I feel like it:

- Attendance tracking – because someone has to know who showed up
- Gradebooks – for the number crunchers
- Parent portals – because parents are nosy
- Calendars – so you know what day it is
- Messaging – because emails are too slow
- Report cards – automated, because manual is for peasants
- Mobile apps – because everyone's on their phone

---

## The Person Behind This

**Omer Kemal** – developer, caffeine addict, and occasional sleeper.

- GitHub: [omerKkemal](https://github.com/omerKkemal)
- Website: [omerkemal.com](https://www.omerkemal.com)

Found a bug? Tell me.  
Want to help? Send a PR.  
Just being rude? Go away.

---

## The Legal Stuff

MIT License – use it, modify it, break it. Just don't blame me.

Copyright (c) 2024 Omer Kemal

---

<p align="center">
  <sub>Made with caffeine, frustration, and questionable life choices.</sub>
  <br>
  <sub>Go outside. Touch grass. I'll still be here. Coding. Crying.</sub>
</p>
