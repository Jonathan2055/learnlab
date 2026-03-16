from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("login/", views.login_view, name="login"),
    path("admin-login/", views.login_view, {"admin_login": True}, name="admin_login"),
    path("logout/", views.logout_view, name="logout"),
    # Admin
    path("admin/dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("admin/users/<int:user_id>/edit/", views.admin_user_edit, name="admin_user_edit"),
    path("admin/users/<int:user_id>/delete/", views.admin_user_delete, name="admin_user_delete"),
    path("admin/classes/create/", views.admin_class_create, name="admin_class_create"),
    path("admin/classes/<int:classroom_id>/", views.admin_class_detail, name="admin_class_detail"),
    path("admin/classes/<int:course_id>/edit/", views.admin_class_edit, name="admin_class_edit"),
    path("admin/classes/<int:course_id>/delete/", views.admin_class_delete, name="admin_class_delete"),
    path("admin/classes/<int:classroom_id>/courses/create/", views.admin_course_create, name="admin_course_create"),
    path("admin/courses/<int:course_id>/edit/", views.admin_course_edit, name="admin_course_edit"),
    path("admin/courses/<int:course_id>/delete/", views.admin_course_delete, name="admin_course_delete"),
    # Teacher
    path("teacher/dashboard/", views.teacher_dashboard, name="teacher_dashboard"),
    path("teacher/classes/<int:classroom_id>/", views.teacher_class_detail, name="teacher_class_detail"),
    path("teacher/courses/<int:course_id>/", views.teacher_course_detail, name="teacher_course_detail"),
    path("teacher/courses/<int:course_id>/materials/upload/", views.teacher_material_upload, name="teacher_material_upload"),
    path("teacher/materials/<int:material_id>/delete/", views.teacher_material_delete, name="teacher_material_delete"),
    path("teacher/courses/<int:course_id>/tasks/create/", views.teacher_task_create, name="teacher_task_create"),
    path("teacher/tasks/<int:task_id>/", views.teacher_task_detail, name="teacher_task_detail"),
    path("teacher/tasks/<int:task_id>/edit/", views.teacher_task_edit, name="teacher_task_edit"),
    path("teacher/tasks/<int:task_id>/delete/", views.teacher_task_delete, name="teacher_task_delete"),
    path("teacher/tasks/<int:task_id>/groups/create/", views.teacher_task_group_create, name="teacher_task_group_create"),
    path("teacher/submissions/<int:submission_id>/grade/", views.teacher_submission_grade, name="teacher_submission_grade"),
    # Student
    path("student/dashboard/", views.student_dashboard, name="student_dashboard"),
    path("student/courses/<int:course_id>/", views.student_course_detail, name="student_course_detail"),
    path("student/tasks/<int:task_id>/", views.student_task_detail, name="student_task_detail"),
    path("student/portfolio/", views.student_portfolio, name="student_portfolio"),
    path("student/portfolio/pdf/", views.student_portfolio_pdf, name="student_portfolio_pdf"),
]
