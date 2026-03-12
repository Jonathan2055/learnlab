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

## Next steps

Planned additions:

- Teacher dashboard: course materials, task assignment, submission review
- Student dashboard: course/assignment views, submissions, portfolio
- Course and enrollment models and admin tooling

