from django.contrib import admin
from django.urls import path

from django.conf import settings
from django.conf.urls.static import static

from accounts.views import (
    home,
    student_register,
    student_login,
    student_dashboard,
    student_logout,
    chatbot,
    study_materials,
    quiz,
)


urlpatterns = [

    path(
        'admin/',
        admin.site.urls
    ),

    path(
        '',
        home,
        name='home'
    ),

    path(
        'register/',
        student_register,
        name='student_register'
    ),

    path(
        'login/',
        student_login,
        name='student_login'
    ),

    path(
        'dashboard/',
        student_dashboard,
        name='student_dashboard'
    ),

    path(
        'logout/',
        student_logout,
        name='student_logout'
    ),

    path(
        'chatbot/',
        chatbot,
        name='chatbot'
    ),

    path(
        'study-materials/',
        study_materials,
        name='study_materials'
    ),

    path(
        'quiz/',
        quiz,
        name='quiz'
    ),
]


# Serve uploaded files during development
if settings.DEBUG:

    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )