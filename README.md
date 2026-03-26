# LearnLab (Django)

LearnLab is a lightweight learning management prototype built with Django.

This initial version includes:

- Custom user model with **Admin**, **Teacher**, and **Student** roles
- Role-based login with a split-screen LearnLab-style login page
- Separate **Administrator Login** entry point
- Admin dashboard to create Teacher/Student accounts

## Getting started

From the project root (where `manage.py` lives):

```bash
python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
python3 manage.py migrate

# create an initial admin (superuser)
python3 manage.py createsuperuser

# run the dev server
python3 manage.py runserver
```

Then open `http://127.0.0.1:8000/login/` in your browser.

- Use the **Teacher/Student** login page at `/login/`.
- Use the **Administrator Login** link at the bottom to go to `/admin-login/`.
- After a successful Admin login you will be redirected to the custom Admin dashboard.

## How it works
- First start by logging in as administrator using the creadentials set when creating a superuser
- then create teacher and student accounts
- from there create a class and assign both students and teacher

### Use cases
#### Teacher's Dashboard
- Create a course 
- add learning materials 
- create task and assign to group when it is group based
- give feedback 
#### Student's Dashboard
- see courses
- view learning materials 
- View tasks 
- create submission
- see and Download Portfolio