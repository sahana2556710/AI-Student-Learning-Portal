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


class Assignment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to="assignments/")
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    status = models.CharField(
        max_length=10,
        choices=[
            ("Present", "Present"),
            ("Absent", "Absent"),
        ]
    )

    def __str__(self):
        return f"{self.student.full_name} - {self.date} - {self.status}"


class Progress(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    topic = models.CharField(max_length=200)
    score = models.IntegerField()
    total_questions = models.IntegerField(default=5)
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.full_name} - {self.topic} - {self.score}/{self.total_questions}"
def my_progress(request):
    if "student_id" not in request.session:
        return redirect("student_login")

    student = Student.objects.get(
        id=request.session["student_id"]
    )

    progress = Progress.objects.filter(
        student=student
    ).order_by("-completed_at")

    total_quizzes = progress.count()

    total_score = sum(p.score for p in progress)
    total_questions = sum(p.total_questions for p in progress)

    percentage = (
        round((total_score / total_questions) * 100, 2)
        if total_questions > 0 else 0
    )

    return render(request, "my_progress.html", {
        "name": student.full_name,
        "progress": progress,
        "total_quizzes": total_quizzes,
        "percentage": percentage,
    })