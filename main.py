from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from db import (
    init_db,
    save_assessment,
    get_latest_assessment,
    save_breakdown,
    save_answers,
    save_screen_time_log,
    get_user_screen_time_logs,
    delete_screen_time_log
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


def calculate_dimensions_30(answers: list[int]) -> dict:
    overload = sum(answers[0:10])      # Q1-Q10
    invasion = sum(answers[10:20])     # Q11-Q20
    complexity = sum(answers[20:30])   # Q21-Q30

    return {
        "overload": overload,
        "invasion": invasion,
        "complexity": complexity
    }


@app.get("/")
def home():
    return FileResponse("index.html")

@app.get("/login")
def login_page():
    return FileResponse("login.html")

@app.get("/assessment")
def assessment_page():
    return FileResponse("assessment.html")

@app.get("/results")
def results_page():
    return FileResponse("results.html")

@app.get("/journal")
def journal_page():
    return FileResponse("journal.html")


@app.post("/submit-survey")
def submit_survey(data: dict):
    return {"received_answers": data}

def get_primary_dimension(dimensions: dict) -> str:
    max_score = max(dimensions.values())

    highest = [name for name, score in dimensions.items() if score == max_score]

    if len(highest) == 1:
        return highest[0]

    return "mixed"

def get_personalised_advice(primary_dimension: str, category: str) -> dict:

    # OVERLOAD
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

        else:  # high
            return {
                "title": "High Techno-Overload",
                "cause": "You are likely overwhelmed by constant digital demands and information overload.",
                "advice": "Reduce your workload where possible, take structured breaks, and create strict boundaries around when you engage with technology."
            }

    # INVASION
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
                "advice": "Set 'offline hours', reduce evening screen use, and avoid checking notifications late at night."
            }

        else:  # high
            return {
                "title": "High Techno-Invasion",
                "cause": "Technology is significantly interfering with your personal life and rest time.",
                "advice": "Create strict digital boundaries, use app limits, and schedule regular screen-free periods to recover."
            }

    # COMPLEXITY
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

        else:  # high
            return {
                "title": "High Techno-Complexity",
                "cause": "You are likely experiencing stress due to complex or difficult-to-use systems.",
                "advice": "Simplify your digital environment, use familiar tools, and allow extra time to learn new systems gradually."
            }

    # MIXED
    else:
        return {
            "title": "Mixed Technostress Profile",
            "cause": "Your stress is spread across multiple areas such as overload, invasion, and complexity.",
            "advice": "Try combining strategies: reduce workload, set boundaries with technology, and simplify your digital tasks."
        }
    
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


# =========================
# SCREEN TIME JOURNAL
# =========================

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

import os

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
