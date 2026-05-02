from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse
import hmac
import hashlib
import os
from fastapi.staticfiles import StaticFiles

from db import (
    init_db,
    save_assessment,
    get_latest_assessment,
    get_all_assessments,
    save_breakdown,
    save_answers,
    save_screen_time_log,
    get_user_screen_time_logs,
    delete_screen_time_log,
    create_user,
    verify_user
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

SECRET_KEY = "change-this-secret-key"

def create_session_token(email: str) -> str:
    signature = hmac.new(
        SECRET_KEY.encode(),
        email.encode(),
        hashlib.sha256
    ).hexdigest()

    return f"{email}|{signature}"


def get_logged_in_user(request: Request):
    token = request.cookies.get("technomind_session")

    if not token or "|" not in token:
        return None

    email, signature = token.split("|", 1)

    expected_signature = hmac.new(
        SECRET_KEY.encode(),
        email.encode(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_signature):
        return None

    return email

app.mount("/static", StaticFiles(directory="static"), name="static")


def calculate_dimensions_30(answers: list[int]) -> dict:
    overload = sum(answers[0:10])
    invasion = sum(answers[10:20])
    complexity = sum(answers[20:30])

    return {
        "overload": overload,
        "invasion": invasion,
        "complexity": complexity
    }


def get_primary_dimension(dimensions: dict) -> str:
    max_score = max(dimensions.values())
    highest = [name for name, score in dimensions.items() if score == max_score]

    if len(highest) == 1:
        return highest[0]

    return "mixed"


def get_personalised_advice(primary_dimension: str, category: str) -> dict:
    if primary_dimension == "overload":
        if category == "low":
            return {
                "title": "Mild Techno-Overload",
                "cause": "You occasionally experience pressure from digital tasks, but it is still manageable.",
                "advice": "Try keeping a simple daily task list and avoid multitasking when possible to stay focused."
            }
        elif category == "medium":
            return {
                "title": "Moderate Techno-Overload",
                "cause": "You may be dealing with too many digital demands such as messages, deadlines, and notifications.",
                "advice": "Try time-blocking your tasks, turning off non-essential notifications, and focusing on one task at a time."
            }
        else:
            return {
                "title": "High Techno-Overload",
                "cause": "You are likely overwhelmed by constant digital demands and information overload.",
                "advice": "Reduce your workload where possible, take structured breaks, and create strict boundaries around when you engage with technology."
            }

    elif primary_dimension == "invasion":
        if category == "low":
            return {
                "title": "Mild Techno-Invasion",
                "cause": "Technology slightly overlaps with your personal time, but it is mostly under control.",
                "advice": "Try maintaining clear boundaries between work/study and personal time."
            }
        elif category == "medium":
            return {
                "title": "Moderate Techno-Invasion",
                "cause": "You may find it difficult to switch off from technology, even during rest time.",
                "advice": "Set offline hours, reduce evening screen use, and avoid checking notifications late at night."
            }
        else:
            return {
                "title": "High Techno-Invasion",
                "cause": "Technology is significantly interfering with your personal life and rest time.",
                "advice": "Create strict digital boundaries, use app limits, and schedule regular screen-free periods to recover."
            }

    elif primary_dimension == "complexity":
        if category == "low":
            return {
                "title": "Mild Techno-Complexity",
                "cause": "You occasionally find digital systems slightly confusing.",
                "advice": "Take your time learning tools and focus on one system at a time."
            }
        elif category == "medium":
            return {
                "title": "Moderate Techno-Complexity",
                "cause": "You may feel stressed when learning or adapting to new technologies.",
                "advice": "Break tasks into smaller steps, use tutorials, and avoid switching between too many platforms."
            }
        else:
            return {
                "title": "High Techno-Complexity",
                "cause": "You are likely experiencing stress due to complex or difficult-to-use systems.",
                "advice": "Simplify your digital environment, use familiar tools, and allow extra time to learn new systems gradually."
            }

    else:
        return {
            "title": "Mixed Technostress Profile",
            "cause": "Your stress is spread across multiple areas such as overload, invasion, and complexity.",
            "advice": "Try combining strategies: reduce workload, set boundaries with technology, and simplify your digital tasks."
        }



@app.get("/")
def home():
    return FileResponse("index.html")


@app.get("/login")
def login_page():
    return FileResponse("login.html")


@app.get("/signup")
def signup_page():
    return FileResponse("signup.html")


@app.get("/assessment")
def assessment_page(request: Request):
    if not get_logged_in_user(request):
        return RedirectResponse("/login")
    
    return FileResponse("assessment.html")

@app.get("/all-assessments")
def all_assessments():
    return {
        "assessments": get_all_assessments()
    }


@app.get("/results")
def results_page():
    return FileResponse("results.html")


@app.get("/journal")
def journal_page(request: Request):
    if not get_logged_in_user(request):
        return RedirectResponse("/login")
    
    return FileResponse("journal.html")

@app.post("/auth/signup")
def auth_signup(data: dict):
    required_fields = ["firstName", "lastName", "email", "password"]

    for field in required_fields:
        if field not in data or not str(data[field]).strip():
            return JSONResponse(
                {"error": "Please fill in all fields."},
                status_code=400
            )

    try:
        create_user(
            first_name=data["firstName"].strip(),
            last_name=data["lastName"].strip(),
            email=data["email"].strip(),
            password=data["password"]
        )

        return {"message": "Account created successfully"}

    except Exception:
        return JSONResponse(
            {"error": "Account could not be created. This email may already exist."},
            status_code=400
        )

@app.post("/auth/login")
def auth_login(data: dict):
    if "email" not in data or "password" not in data:
        return JSONResponse(
            {"error": "Please enter your email and password."},
            status_code=400
        )

    user = verify_user(
        email=data["email"].strip(),
        password=data["password"]
    )

    if not user:
        return JSONResponse(
            {"error": "Invalid email or password."},
            status_code=401
        )

    response = JSONResponse({
        "message": "Login successful",
        "user": {
            "email": user["email"],
            "firstName": user["first_name"],
            "lastName": user["last_name"]
        }
    })

    response.set_cookie(
        key="technomind_session",
        value=create_session_token(user["email"]),
        httponly=True,
        samesite="lax"
    )

    return response


@app.post("/auth/logout")
def auth_logout():
    response = JSONResponse({"message": "Logged out successfully"})
    response.delete_cookie("technomind_session")
    return response


@app.post("/submit-survey")
def submit_survey(data: dict):
    return {"received_answers": data}


@app.post("/score")
def calculate_score(data: dict):
    if "answers" not in data:
        return {"error": "Missing 'answers' field"}

    answers = data["answers"]

    if not isinstance(answers, list):
        return {"error": "'answers' must be a list"}

    if len(answers) != 30:
        return {"error": "Expected 30 answers"}

    total = sum(answers)
    dims = calculate_dimensions_30(answers)

    if total <= 60:
        category = "low"
    elif total <= 105:
        category = "medium"
    else:
        category = "high"

    primary_dimension = get_primary_dimension(dims)
    advice_info = get_personalised_advice(primary_dimension, category)

    assessment_id = save_assessment(total_score=total, category=category)
    save_answers(assessment_id, answers)
    save_breakdown(
        assessment_id,
        overload=dims["overload"],
        invasion=dims["invasion"],
        complexity=dims["complexity"]
    )

    return {
        "assessment_id": assessment_id,
        "score": total,
        "category": category,
        "dimensions": dims,
        "primary_dimension": primary_dimension,
        "advice_title": advice_info["title"],
        "advice_cause": advice_info["cause"],
        "advice_text": advice_info["advice"]
    }


@app.get("/latest")
def latest():
    latest_row = get_latest_assessment()
    return {"latest": latest_row}


@app.post("/save-demo")
def save_demo():
    assessment_id = save_assessment(total_score=12, category="medium")
    return {"saved_assessment_id": assessment_id}


@app.post("/screen-time")
def add_screen_time(data: dict):
    if "user_email" not in data or "log_date" not in data or "hours_used" not in data:
        return {"error": "Missing required fields"}

    try:
        hours_used = float(data["hours_used"])
    except ValueError:
        return {"error": "hours_used must be a number"}

    if hours_used < 0 or hours_used > 24:
        return {"error": "hours_used must be between 0 and 24"}

    save_screen_time_log(
        user_email=data["user_email"],
        log_date=data["log_date"],
        hours_used=hours_used,
        note=data.get("note", "")
    )

    return {"message": "Screen time log saved successfully"}


@app.get("/screen-time/{user_email}")
def get_screen_time(user_email: str):
    logs = get_user_screen_time_logs(user_email)
    return {"logs": logs}


@app.delete("/screen-time")
def remove_screen_time(data: dict):
    if "user_email" not in data or "log_date" not in data:
        return {"error": "Missing required fields"}

    deleted = delete_screen_time_log(
        user_email=data["user_email"],
        log_date=data["log_date"]
    )

    if not deleted:
        return {"error": "Entry not found"}

    return {"message": "Entry deleted successfully"}



if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
