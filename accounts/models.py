from django.db import models


class Student(models.Model):
    full_name = models.CharField(max_length=100)
    usn = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True)
    department = models.CharField(max_length=100)
    semester = models.IntegerField()
    password = models.CharField(max_length=100)

    def __str__(self):
        return self.full_name


class Note(models.Model):
    title = models.CharField(max_length=200)
    subject = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to="notes/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title