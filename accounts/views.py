from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Student, Note, Assignment, Attendance, Progress

from openai import OpenAI
from groq import Groq

import json


# Home Page
def home(request):
    return render(request, "home.html")


# Student Registration
def student_register(request):

    if request.method == "POST":

        full_name = request.POST.get("full_name")
        usn = request.POST.get("usn")
        email = request.POST.get("email")
        department = request.POST.get("department")
        semester = request.POST.get("semester")
        password = request.POST.get("password")

        if Student.objects.filter(email=email).exists():

            messages.error(
                request,
                "Email already registered."
            )

            return redirect("student_register")

        Student.objects.create(
            full_name=full_name,
            usn=usn,
            email=email,
            department=department,
            semester=semester,
            password=password
        )

        messages.success(
            request,
            "Registration successful! Please login."
        )

        return redirect("student_login")

    return render(
        request,
        "register.html"
    )


# Student Login
def student_login(request):

    if request.method == "POST":

        email = request.POST.get("email")
        password = request.POST.get("password")

        try:

            student = Student.objects.get(
                email=email,
                password=password
            )

            request.session["student_id"] = student.id
            request.session["student_name"] = student.full_name

            return redirect("student_dashboard")

        except Student.DoesNotExist:

            messages.error(
                request,
                "Invalid email or password."
            )

    return render(
        request,
        "login.html"
    )


# Student Dashboard
def student_dashboard(request):

    if "student_id" not in request.session:
        return redirect("student_login")

    name = request.session.get(
        "student_name"
    )

    return render(
        request,
        "dashboard.html",
        {
            "name": name
        }
    )


# Student Logout
def student_logout(request):

    request.session.flush()

    return redirect("student_login")


# AI Chatbot
def chatbot(request):

    answer = None

    if request.method == "POST":

        question = request.POST.get("question")

        if question:

            try:

                print("CHATBOT REQUEST RECEIVED")
                print("QUESTION:", question)

                client = Groq()

                response = client.chat.completions.create(

                    model="openai/gpt-oss-20b",

                    messages=[
                        {
                            "role": "user",
                            "content": f"""
You are a simple AI tutor for college students.

Answer the student's question in very simple
and easy-to-understand English.

Follow these rules:

1. Keep the answer short and clear.
2. Use simple English.
3. Explain difficult terms in easy words.
4. Use small examples when helpful.
5. Use bullet points or numbered points.
6. Do not give unnecessary information.
7. Do not give very long tables.
8. Avoid advanced technical language unless necessary.
9. For academic questions, give an exam-friendly answer.
10. Give only the information needed to understand
the question.
11. At the end, give a short "In simple words" line.
12. Do not make the answer unnecessarily long.

Student's question:

{question}
"""
                        }
                    ]
                )

                answer = (
                    response
                    .choices[0]
                    .message
                    .content
                )

                print("CHATBOT RESPONSE RECEIVED")

            except Exception as e:

                print(
                    "CHATBOT ERROR:",
                    repr(e)
                )

                answer = (
                    "Sorry, something went wrong. "
                    "Please try again."
                )

        else:

            answer = (
                "Please enter a question."
            )

    return render(
        request,
        "chatbot.html",
        {
            "answer": answer
        }
    )


# Study Materials
def study_materials(request):

    if "student_id" not in request.session:
        return redirect("student_login")

    notes = Note.objects.all().order_by(
        "-uploaded_at"
    )

    return render(
        request,
        "study_materials.html",
        {
            "notes": notes
        }
    )


# AI Quiz Generator
def quiz(request):

    if "student_id" not in request.session:
        return redirect("student_login")

    quiz_data = None
    error = None
    score = None
    submitted = False

    if request.method == "POST":

        # Submit Quiz
        if request.POST.get("action") == "submit_quiz":

            quiz_data = request.session.get(
                "quiz_data"
            )

            if not quiz_data:

                error = (
                    "Quiz session expired. "
                    "Please generate a new quiz."
                )

            else:

                score = 0
                submitted = True

                for index, question in enumerate(
                    quiz_data["questions"],
                    start=1
                ):

                    selected_answer = request.POST.get(
                        f"question_{index}"
                    )

                    correct_answer = question[
                        "answer"
                    ]

                    if selected_answer == correct_answer:
                        score += 1

                # Get logged-in student
                student = Student.objects.get(
                    id=request.session["student_id"]
                )

                # Get quiz topic
                topic = request.session.get(
                    "quiz_topic",
                    "Quiz"
                )

                # Save quiz result
                Progress.objects.create(
                    student=student,
                    topic=topic,
                    score=score,
                    total_questions=len(
                        quiz_data["questions"]
                    )
                )

                print("QUIZ SUBMITTED")
                print(
                    "SCORE:",
                    score,
                    "/",
                    len(
                        quiz_data["questions"]
                    )
                )

        # Generate New Quiz
        else:

            topic = request.POST.get(
                "topic"
            )

            print(
                "QUIZ REQUEST RECEIVED"
            )

            print(
                "TOPIC:",
                topic
            )

            if not topic:

                error = (
                    "Please enter a topic."
                )

            else:

                try:

                    print(
                        "Starting Groq quiz generation..."
                    )

                    client = Groq()

                    response = client.chat.completions.create(

                        model="openai/gpt-oss-20b",

                        messages=[
                            {
                                "role": "user",
                                "content": f"""
Create exactly 5 multiple-choice questions
for a college student on this topic:

{topic}

Return ONLY valid JSON.

Use exactly this structure:

{{
    "questions": [
        {{
            "question": "Question text",
            "options": [
                "Option A",
                "Option B",
                "Option C",
                "Option D"
            ],
            "answer": "Option A"
        }}
    ]
}}

The answer must be exactly one of the
four options.

Do not use markdown.
Do not use code blocks.
Do not write anything except JSON.
"""
                            }
                        ]
                    )

                    print(
                        "Groq response received."
                    )

                    output = (
                        response
                        .choices[0]
                        .message
                        .content
                    )

                    print(
                        "RAW AI RESPONSE:"
                    )

                    print(output)

                    if not output:

                        raise ValueError(
                            "AI returned an empty response."
                        )

                    output = output.strip()

                    if output.startswith(
                        "```json"
                    ):

                        output = output[7:]

                    elif output.startswith(
                        "```"
                    ):

                        output = output[3:]

                    if output.endswith(
                        "```"
                    ):

                        output = output[:-3]

                    output = output.strip()

                    print(
                        "CLEANED AI RESPONSE:"
                    )

                    print(output)

                    quiz_data = json.loads(
                        output
                    )

                    print(
                        "JSON converted successfully."
                    )

                    if "questions" not in quiz_data:

                        raise ValueError(
                            "The AI response does not contain questions."
                        )

                    if len(
                        quiz_data["questions"]
                    ) != 5:

                        raise ValueError(
                            "The AI did not generate exactly 5 questions."
                        )

                    # Save quiz data
                    request.session[
                        "quiz_data"
                    ] = quiz_data

                    # Save quiz topic
                    request.session[
                        "quiz_topic"
                    ] = topic

                    print(
                        "QUIZ GENERATED SUCCESSFULLY."
                    )

                except Exception as e:

                    print(
                        "QUIZ ERROR:",
                        repr(e)
                    )

                    error = (
                        "Quiz Error: "
                        + str(e)
                    )

    return render(
        request,
        "quiz.html",
        {
            "quiz_data": quiz_data,
            "error": error,
            "score": score,
            "submitted": submitted
        }
    )


# PDF Question Answering
def pdf_qa(request):

    answer = None
    error = None

    if request.method == "POST":

        pdf_file = request.FILES.get("pdf_file")
        question = request.POST.get("question")

        if not pdf_file:

            error = "Please select a PDF file."

        elif not question:

            error = "Please enter a question."

        elif not pdf_file.name.lower().endswith(".pdf"):

            error = "Please upload a PDF file only."

        else:

            try:

                from pypdf import PdfReader

                # Read PDF
                reader = PdfReader(pdf_file)

                text = ""

                for page in reader.pages:

                    page_text = page.extract_text()

                    if page_text:

                        text += page_text + "\n"

                if not text.strip():

                    error = (
                        "Could not extract text from this PDF."
                    )

                else:

                    # Keep the text within a reasonable size
                    text = text[:20000]

                    # Send PDF content and question to Groq AI
                    client = Groq()

                    response = client.chat.completions.create(

                        model="openai/gpt-oss-20b",

                        messages=[
                            {
                                "role": "user",
                                "content": f"""
You are an AI tutor.

Answer the student's question using ONLY the information
provided from the PDF below.

Keep the answer simple, clear and easy to understand.

PDF CONTENT:
{text}

STUDENT QUESTION:
{question}

Give a short and useful answer.
"""
                            }
                        ]
                    )

                    answer = (
                        response
                        .choices[0]
                        .message
                        .content
                    )

            except Exception as e:

                error = f"Error: {str(e)}"

    return render(
        request,
        "pdf_qa.html",
        {
            "answer": answer,
            "error": error,
        }
    )


# Assignment Submission
def assignment(request):

    message = None
    error = None

    if "student_id" not in request.session:

        return redirect("student_login")

    student_id = request.session.get(
        "student_id"
    )

    if request.method == "POST":

        title = request.POST.get(
            "title"
        )

        assignment_file = request.FILES.get(
            "assignment_file"
        )

        if not title:

            error = (
                "Please enter the assignment title."
            )

        elif not assignment_file:

            error = (
                "Please select an assignment file."
            )

        else:

            try:

                student = Student.objects.get(
                    id=student_id
                )

                Assignment.objects.create(
                    student=student,
                    title=title,
                    file=assignment_file
                )

                message = (
                    "Assignment submitted successfully! 🎉"
                )

            except Student.DoesNotExist:

                error = (
                    "Student account not found."
                )

            except Exception as e:

                error = f"Error: {str(e)}"

    return render(
        request,
        "assignment.html",
        {
            "message": message,
            "error": error,
        }
    )


# Attendance
def attendance(request):

    if "student_id" not in request.session:

        return redirect("student_login")

    student_id = request.session.get(
        "student_id"
    )

    try:

        student = Student.objects.get(
            id=student_id
        )

        attendance_records = Attendance.objects.filter(
            student=student
        ).order_by("-date")

        present_count = attendance_records.filter(
            status="Present"
        ).count()

        absent_count = attendance_records.filter(
            status="Absent"
        ).count()

        return render(
            request,
            "attendance.html",
            {
                "attendance_records": attendance_records,
                "present_count": present_count,
                "absent_count": absent_count,
            }
        )

    except Student.DoesNotExist:

        return redirect("student_login")
def progress(request):

    if "student_id" not in request.session:
        return redirect("student_login")

    student_id = request.session.get("student_id")

    try:
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        return redirect("student_login")

    progress_records = Progress.objects.filter(
        student=student
    ).order_by("-completed_at")

    total_quizzes = progress_records.count()

    total_score = sum(
        item.score for item in progress_records
    )

    total_questions = sum(
        item.total_questions for item in progress_records
    )

    if total_questions > 0:
        average_percentage = round(
            (total_score / total_questions) * 100,
            1
        )
    else:
        average_percentage = 0

    return render(
        request,
        "progress.html",
        {
            "student": student,
            "progress_records": progress_records,
            "total_quizzes": total_quizzes,
            "total_score": total_score,
            "total_questions": total_questions,
            "average_percentage": average_percentage,
        }
    )
# Certificate Generation
from django.utils import timezone

def certificate(request):
    if "student_id" not in request.session:
        return redirect("student_login")

    try:
        student = Student.objects.get(
            id=request.session["student_id"]
        )
    except Student.DoesNotExist:
        return redirect("student_login")

    course = request.GET.get("course", "")

    return render(request, "certificate.html", {
        "student": student,
        "course": course,
        "date": timezone.localdate(),
    })

# Leaderboard
def leaderboard(request):
    if "student_id" not in request.session:
        return redirect("student_login")

    students = Student.objects.all()
    leaderboard_data = []

    for student in students:
        records = Progress.objects.filter(student=student)

        total_score = sum(item.score for item in records)
        total_questions = sum(
            item.total_questions for item in records
        )

        if total_questions > 0:
            leaderboard_data.append({
                "name": student.full_name,
                "total_score": total_score,
                "total_questions": total_questions,
                "percentage": round(
                    total_score / total_questions * 100, 1
                ),
            })

    leaderboard_data.sort(
        key=lambda item: item["total_score"],
        reverse=True
    )

    for rank, item in enumerate(leaderboard_data, start=1):
        item["rank"] = rank

    return render(
        request,
        "leaderboard.html",
        {"leaderboard": leaderboard_data}
    )