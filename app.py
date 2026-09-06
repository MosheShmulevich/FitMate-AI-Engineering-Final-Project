import uuid

import streamlit as st

from agent import ask_fitmate
from database import (
    init_db,
    get_all_users,
    get_user_profile,
    get_user_progress,
    create_user,
    update_user,
    save_workout_plan,
    get_latest_workout_plan,
)


# ==================================================
# Page Setup
# ==================================================

st.set_page_config(
    page_title="FitMate",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()


# ==================================================
# RTL
# ==================================================

st.markdown(
    """
    <style>
        .stApp {
            direction: rtl;
        }

        section[data-testid="stSidebar"] {
            direction: rtl;
        }

        input,
        textarea {
            direction: rtl !important;
            text-align: right !important;
        }

        div[data-testid="stChatMessage"] {
            direction: rtl;
            text-align: right;
        }

        div[data-testid="stMarkdownContainer"] {
            text-align: right;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==================================================
# User Initialization
# ==================================================

if "user_id" not in st.session_state:
    users = get_all_users()

    if users:
        st.session_state.user_id = users[0][0]
    else:
        st.session_state.user_id = create_user(
            name="משתמש חדש",
            goal="עלייה במסת שריר",
            experience_level="Beginner",
            training_days=3,
            session_duration=60,
            equipment="חדר כושר מלא",
        )

USER_ID = st.session_state.user_id


# ==================================================
# Session State
# ==================================================

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "plan_thread_id" not in st.session_state:
    st.session_state.plan_thread_id = str(uuid.uuid4())

if "workout_plan" not in st.session_state:
    latest_plan = get_latest_workout_plan(USER_ID)

    if latest_plan:
        st.session_state.workout_plan = latest_plan[3]
        st.session_state.workout_plan_created_at = latest_plan[2]
    else:
        st.session_state.workout_plan = None
        st.session_state.workout_plan_created_at = None


# ==================================================
# Profile
# ==================================================

profile = get_user_profile(USER_ID)


# ==================================================
# Sidebar
# ==================================================

st.sidebar.title("💪 FitMate")
st.sidebar.caption("המאמן האישי החכם שלך")
st.sidebar.divider()
st.sidebar.subheader("👤 פרופיל מתאמן")

level_labels = {
    "Beginner": "מתחיל",
    "Intermediate": "בינוני",
    "Advanced": "מתקדם",
}

levels = list(level_labels.keys())

with st.sidebar.form("profile_form"):
    name = st.text_input(
        "שם",
        value=profile[1] or "",
    )

    goal = st.text_input(
        "מטרת האימון",
        value=profile[2] or "",
    )

    level_index = (
        levels.index(profile[3])
        if profile[3] in levels
        else 0
    )

    experience_level = st.selectbox(
        "רמת ניסיון",
        levels,
        index=level_index,
        format_func=lambda value: level_labels[value],
    )

    training_days = st.number_input(
        "מספר אימונים בשבוע",
        min_value=1,
        max_value=7,
        value=int(profile[4] or 3),
    )

    session_duration = st.number_input(
        "משך אימון בדקות",
        min_value=15,
        max_value=180,
        value=int(profile[5] or 60),
        step=5,
    )

    equipment = st.text_input(
        "ציוד זמין",
        value=profile[6] or "",
    )

    save_profile = st.form_submit_button(
        "💾 שמור פרופיל",
        use_container_width=True,
        type="primary",
    )

if save_profile:
    update_user(
        USER_ID,
        name,
        goal,
        experience_level,
        training_days,
        session_duration,
        equipment,
    )

    profile = get_user_profile(USER_ID)

    st.sidebar.success(
        "הפרופיל נשמר בהצלחה ✅"
    )

st.sidebar.divider()

if st.sidebar.button(
    "＋ שיחה חדשה",
    use_container_width=True,
):
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.rerun()


# ==================================================
# Header
# ==================================================

title_col, status_col = st.columns(
    [4, 1],
    vertical_alignment="center",
)

with title_col:
    st.title("FitMate 💪")
    st.caption(
        "מאמן כושר אישי מבוסס בינה מלאכותית"
    )

with status_col:
    st.success("● המתאמן מחובר")

st.write(
    f"ברוך הבא, **{profile[1]}** 👋"
)


# ==================================================
# Dashboard
# ==================================================

progress = get_user_progress(USER_ID)

total_volume = sum(
    (row[4] or 0)
    * (row[5] or 0)
    * (row[6] or 0)
    for row in progress
)

metric1, metric2, metric3, metric4 = st.columns(4)

with metric1:
    with st.container(border=True):
        st.caption("🎯 מטרה")
        st.subheader(
            profile[2] or "לא הוגדרה"
        )

with metric2:
    with st.container(border=True):
        st.caption("📅 אימונים בשבוע")
        st.subheader(
            f"{profile[4]} אימונים"
        )

with metric3:
    with st.container(border=True):
        st.caption("⏱️ משך אימון")
        st.subheader(
            f"{profile[5]} דקות"
        )

with metric4:
    with st.container(border=True):
        st.caption("📈 נפח אימון מתועד")
        st.subheader(
            f"{total_volume:,.0f} ק״ג"
        )

st.divider()


# ==================================================
# Navigation
# ==================================================

chat_tab, plan_tab, progress_tab = st.tabs(
    [
        "💬 המאמן שלי",
        "🏋️ תוכנית האימון שלי",
        "📈 ההתקדמות שלי",
    ]
)


# ==================================================
# Chat
# ==================================================

with chat_tab:
    left, right = st.columns([3, 1])

    with left:
        st.subheader("💬 דבר עם FitMate")
        st.caption(
            "שאל שאלות, קבל המלצות "
            "או שמור את הביצועים שלך."
        )

    with right:
        if st.button(
            "נקה שיחה",
            use_container_width=True,
        ):
            st.session_state.thread_id = str(
                uuid.uuid4()
            )
            st.session_state.messages = []
            st.rerun()

    if not st.session_state.messages:
        with st.container(border=True):
            st.markdown(
                "#### 👋 איך אפשר לעזור?"
            )

            st.write("אפשר לנסות למשל:")
            st.write("• מהי תדירות אימון?")
            st.write("• שמור שביצעתי היום Bench Press")
            st.write("• מה ההתקדמות האחרונה שלי?")

    for message in st.session_state.messages:
        with st.chat_message(
            message["role"]
        ):
            st.markdown(
                message["content"]
            )

    user_message = st.chat_input(
        "כתוב הודעה ל-FitMate..."
    )

    if user_message:
        st.session_state.messages.append(
            {
                "role": "user",
                "content": user_message,
            }
        )

        with st.chat_message("user"):
            st.markdown(user_message)

        internal_message = f"""
Active trainee user_id: {USER_ID}

Use get_user_profile_tool with user_id {USER_ID}
when profile information is relevant.

Use get_user_progress_tool with user_id {USER_ID}
when training history is relevant.

Use save_user_progress_tool with user_id {USER_ID}
when the trainee asks to save workout progress.

User message:
{user_message}
"""

        with st.chat_message("assistant"):
            with st.spinner(
                "FitMate חושב..."
            ):
                try:
                    response = ask_fitmate(
                        message=internal_message,
                        thread_id=st.session_state.thread_id,
                    )

                except Exception as error:
                    response = (
                        "אירעה שגיאה בזמן עיבוד הבקשה.\n\n"
                        f"`{error}`"
                    )

            st.markdown(response)

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": response,
            }
        )


# ==================================================
# Workout Plan
# ==================================================

with plan_tab:
    st.subheader(
        "🏋️ תוכנית האימון שלי"
    )

    st.caption(
        "FitMate יבנה תוכנית אישית לפי הפרופיל "
        "שלך והידע המקצועי במערכת."
    )

    st.write(
        "### הפרופיל שעליו תיבנה התוכנית"
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        with st.container(border=True):
            st.caption("🎯 מטרה")
            st.write(
                profile[2] or "לא הוגדרה"
            )

    with c2:
        with st.container(border=True):
            st.caption("🏋️ רמת ניסיון")
            st.write(
                level_labels.get(
                    profile[3],
                    profile[3]
                )
            )

    with c3:
        with st.container(border=True):
            st.caption("📅 אימונים בשבוע")
            st.write(
                f"{profile[4]} אימונים"
            )

    c4, c5 = st.columns(2)

    with c4:
        with st.container(border=True):
            st.caption("⏱️ זמן לכל אימון")
            st.write(
                f"{profile[5]} דקות"
            )

    with c5:
        with st.container(border=True):
            st.caption("🏟️ ציוד")
            st.write(
                profile[6] or "לא הוגדר"
            )

    st.write("")

    limitations = st.text_area(
        "מגבלות או העדפות מיוחדות",
        placeholder=(
            "לדוגמה: לא אוהב סקוואט, "
            "מעדיף מכונות, אין מגבלות מיוחדות..."
        ),
        help=(
            "אם אין מגבלות או העדפות, "
            "אפשר להשאיר ריק."
        ),
    )

    generate_plan = st.button(
        "✨ בנה / עדכן תוכנית אימון",
        type="primary",
        use_container_width=True,
    )

    if generate_plan:
        limitations_text = (
            limitations.strip()
            if limitations.strip()
            else "לא דווחו מגבלות או העדפות מיוחדות."
        )

        plan_request = f"""
Create a personalized workout plan for trainee
user_id {USER_ID}.

You MUST:
1. Use get_user_profile_tool with user_id {USER_ID}.
2. Use search_fitness_knowledge before creating the plan.
3. Follow the Workout Planning Skill.
4. Base professional training decisions on the FitMate knowledge base.
5. Answer in Hebrew.
6. Create exactly {profile[4]} training days.
7. Keep each workout appropriate for approximately {profile[5]} minutes.
8. Use the available equipment from the profile.
9. Present the final plan clearly using Markdown.
10. For every training day include:
    - Day name
    - Exercises
    - Sets
    - Repetitions
    - Rest time
    - Short notes when relevant
11. Do NOT show source document names, page numbers,
    similarity scores, retrieval details, or technical RAG information
    in the final user-facing answer.
12. You may use retrieved sources internally to build the plan,
    but the final answer should look like a clean fitness product.

Reported limitations or preferences:
{limitations_text}

Do not ask for additional information.
The profile and limitations information above
should be treated as the required planning inputs.
"""

        with st.spinner(
            "FitMate בונה עבורך תוכנית..."
        ):
            try:
                workout_plan = ask_fitmate(
                    message=plan_request,
                    thread_id=st.session_state.plan_thread_id,
                )

                save_workout_plan(
                    USER_ID,
                    workout_plan,
                )

                latest_plan = get_latest_workout_plan(
                    USER_ID
                )

                st.session_state.workout_plan = (
                    latest_plan[3]
                )

                st.session_state.workout_plan_created_at = (
                    latest_plan[2]
                )

                st.success(
                    "התוכנית נבנתה ונשמרה בהצלחה ✅"
                )

            except Exception as error:
                st.error(
                    "אירעה שגיאה בבניית התוכנית."
                )
                st.code(str(error))

    if st.session_state.workout_plan:
        st.divider()

        plan_header, plan_date = st.columns(
            [3, 1],
            vertical_alignment="center",
        )

        with plan_header:
            st.subheader(
                "📋 התוכנית שלך"
            )

        with plan_date:
            if st.session_state.workout_plan_created_at:
                formatted_date = (
                    st.session_state
                    .workout_plan_created_at
                    .replace("T", " ")
                )

                st.caption(
                    f"נשמרה: {formatted_date}"
                )

        with st.container(border=True):
            st.markdown(
                st.session_state.workout_plan
            )

    else:
        st.info(
            "עדיין לא נבנתה תוכנית אימון. "
            "לחץ על הכפתור למעלה כדי ליצור אחת."
        )


# ==================================================
# Progress
# ==================================================

with progress_tab:
    st.subheader(
        "📈 היסטוריית האימונים"
    )

    st.caption(
        "כאן ניתן לראות את הביצועים "
        "ש-FitMate שמר עבורך."
    )

    if not progress:
        st.info(
            "עדיין לא נשמרו אימונים."
        )

    else:
        for row in progress:
            date = row[2]
            exercise = row[3]
            sets = row[4]
            reps = row[5]
            weight = row[6]
            notes = row[7]

            volume = (
                sets * reps * weight
                if sets and reps and weight
                else 0
            )

            with st.container(border=True):
                header_col, date_col = st.columns(
                    [3, 1],
                    vertical_alignment="center",
                )

                with header_col:
                    st.subheader(
                        f"🏋️ {exercise}"
                    )

                with date_col:
                    st.caption(
                        f"📅 {date}"
                    )

                c1, c2, c3, c4 = st.columns(4)

                c1.metric(
                    "סטים",
                    sets,
                )

                c2.metric(
                    "חזרות",
                    reps,
                )

                c3.metric(
                    "משקל",
                    f"{weight:g} ק״ג",
                )

                c4.metric(
                    "נפח אימון",
                    f"{volume:,.0f} ק״ג",
                )

                if notes:
                    st.caption(
                        f"הערות: {notes}"
                    )