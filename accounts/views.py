from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Student, Note
from openai import OpenAI
import json


# Student Registration
def student_register(request):

    if request.method == "GET":
        storage = messages.get_messages(request)
        list(storage)

    if request.method == "POST":

        full_name = request.POST.get("full_name")
        usn = request.POST.get("usn")
        email = request.POST.get("email")
        department = request.POST.get("department")
        semester = request.POST.get("semester")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if email:
            email = email.strip().lower()

        if usn:
            usn = usn.strip()

        if not all([
            full_name,
            usn,
            email,
            department,
            semester,
            password,
            confirm_password
        ]):
            messages.error(
                request,
                "Please fill in all the fields."
            )
            return render(request, "register.html")

        if password != confirm_password:
            messages.error(
                request,
                "Passwords do not match."
            )
            return render(request, "register.html")

        if Student.objects.filter(
            email__iexact=email
        ).exists():
            messages.error(
                request,
                "Email already registered."
            )
            return render(request, "register.html")

        if Student.objects.filter(
            usn=usn
        ).exists():
            messages.error(
                request,
                "USN already registered."
            )
            return render(request, "register.html")

        student = Student(
            full_name=full_name,
            usn=usn,
            email=email,
            department=department,
            semester=semester,
            password=password
        )

        student.save()

        messages.success(
            request,
            "Registration successful! Please login."
        )

        return redirect("student_login")

    return render(request, "register.html")


# Student Login
def student_login(request):

    if request.method == "POST":

        email = request.POST.get("email")
        password = request.POST.get("password")

        if email:
            email = email.strip().lower()

        if password:
            password = password.strip()

        try:

            student = Student.objects.get(
                email__iexact=email,
                password=password
            )

            request.session["student_id"] = student.id
            request.session["student_name"] = student.full_name

            return redirect("student_dashboard")

        except Student.DoesNotExist:

            messages.error(
                request,
                "Invalid Email or Password"
            )

    return render(request, "login.html")


# Student Dashboard
def student_dashboard(request):

    if "student_id" not in request.session:
        return redirect("student_login")

    name = request.session.get("student_name")

    return render(
        request,
        "dashboard.html",
        {"name": name}
    )


# Home
def home(request):

    return render(
        request,
        "home.html"
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

                client = OpenAI()

                response = client.responses.create(
                    model="gpt-5.6",
                    input=f"""
You are an AI tutor for students.

Answer the student's question clearly and
in simple language.

Student's question:
{question}
"""
                )

                answer = response.output_text

            except Exception as e:

                print("CHATBOT ERROR:", e)

                answer = (
                    "Sorry, something went wrong. "
                    "Please try again."
                )

        else:

            answer = "Please enter a question."

    return render(
        request,
        "chatbot.html",
        {"answer": answer}
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
        {"notes": notes}
    )


# AI Quiz Generator
def quiz(request):

    if "student_id" not in request.session:
        return redirect("student_login")

    quiz_data = None
    error = None

    if request.method == "POST":

        topic = request.POST.get("topic")

        print("QUIZ REQUEST RECEIVED")
        print("TOPIC:", topic)

        if not topic:

            error = "Please enter a topic."

        else:

            try:

                print("Starting OpenAI quiz generation...")

                client = OpenAI()

                response = client.responses.create(
                    model="gpt-5.6",
                    input=f"""
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
                )

                print("OpenAI response received.")

                output = response.output_text

                print("RAW AI RESPONSE:")
                print(output)

                if not output:
                    raise ValueError(
                        "AI returned an empty response."
                    )

                output = output.strip()

                # Remove markdown code block if present
                if output.startswith("```json"):
                    output = output[7:]

                elif output.startswith("```"):
                    output = output[3:]

                if output.endswith("```"):
                    output = output[:-3]

                output = output.strip()

                print("CLEANED AI RESPONSE:")
                print(output)

                quiz_data = json.loads(output)

                print("JSON converted successfully.")

                if "questions" not in quiz_data:
                    raise ValueError(
                        "The AI response does not contain questions."
                    )

                if len(quiz_data["questions"]) != 5:
                    raise ValueError(
                        "The AI did not generate exactly 5 questions."
                    )

                request.session["quiz_data"] = quiz_data

                print("QUIZ GENERATED SUCCESSFULLY.")

            except Exception as e:

                print("QUIZ ERROR:", repr(e))

                error = (
                    "Quiz Error: "
                    + str(e)
                )

    return render(
        request,
        "quiz.html",
        {
            "quiz_data": quiz_data,
            "error": error
        }
    )