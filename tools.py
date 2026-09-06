from datetime import date

from langchain_core.tools import tool

from database import (
    init_db,
    get_user_profile,
    save_progress,
    get_user_progress,
)


init_db()


@tool
def calculate_training_volume(
    sets: int,
    reps: int,
    weight: float
) -> float:
    """Calculate training volume using sets × reps × weight."""

    return sets * reps * weight


@tool
def get_user_profile_tool(
    user_id: int
) -> dict:
    """Retrieve the trainee profile from the FitMate database."""

    user = get_user_profile(user_id)

    if not user:
        return {
            "error": "User not found"
        }

    return {
        "id": user[0],
        "name": user[1],
        "goal": user[2],
        "experience_level": user[3],
        "training_days": user[4],
        "session_duration": user[5],
        "equipment": user[6],
    }


@tool
def save_user_progress_tool(
    user_id: int,
    exercise: str,
    sets: int,
    reps: int,
    weight: float,
    notes: str = "",
) -> str:
    """
    Save today's workout progress for a trainee.

    The current date is generated automatically by the system.
    Do not ask the user or the language model to provide today's date.
    """

    current_date = date.today().isoformat()

    save_progress(
        user_id=user_id,
        date=current_date,
        exercise=exercise,
        sets=sets,
        reps=reps,
        weight=weight,
        notes=notes,
    )

    return (
        f"Progress saved successfully "
        f"for {current_date}."
    )


@tool
def get_user_progress_tool(
    user_id: int
) -> list:
    """Retrieve previous workout progress for a trainee."""

    rows = get_user_progress(user_id)

    return [
        {
            "id": row[0],
            "user_id": row[1],
            "date": row[2],
            "exercise": row[3],
            "sets": row[4],
            "reps": row[5],
            "weight": row[6],
            "notes": row[7],
        }
        for row in rows
    ]


FITMATE_TOOLS = [
    calculate_training_volume,
    get_user_profile_tool,
    save_user_progress_tool,
    get_user_progress_tool,
]