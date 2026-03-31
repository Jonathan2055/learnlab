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
python -m venv .venv
```
Now activate your virtual environment:
on linux:
```bash
source .venv/bin/activate
```
on windows:

(in command prompt)
``` bash
venv\Scripts\activate.bat
```
(in Powershell)
```bash
.\venv\Scripts\Activate.ps1
```
Install requirements
```bash
pip install -r requirements.txt
```
Create an initial admin (superuser) But no need because down there is some demo data I have created.
```bash
python3 manage.py createsuperuser
```
run the dev server
```bash
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
#### Admin's Dashboard
- Create a users (Teacher, Student) 
- Create class 
- Assign both users to the classes
- Create courses
  
#### Teacher's Dashboard
- add learning materials 
- create task and assign to group when it is group based
- give feedback on submissions
- view students portifolio
#### Student's Dashboard
- see courses
- view learning materials
- View tasks
- Make submissions
- View Grades
- View and Download Portifolios

### Demo Data
- Admin dashboard: 	Username = Administrator 
       	Password = Munyeshuri@2005
- Teacher dashboard: 	Username = Emmanuel 
       	Password = Teacher@1 
- Student dashboard: 	Username = muvunyi 
       	Password = Student@1 





