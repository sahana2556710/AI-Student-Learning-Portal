from django.contrib import admin

from .models import Student, Note, Assignment, Attendance, Progress


admin.site.register(Student)

admin.site.register(Note)

admin.site.register(Assignment)

admin.site.register(Attendance)

admin.site.register(Progress)