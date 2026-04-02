"""
=============================================================
 Social Adaptability and Introversion-Extraversion Survey
 Westminster International University in Tashkent
 Module: Fundamentals of Programming — 4BUIS008C (Level 4)
 Project 1 — Psychological State Survey
=============================================================
 Survey topic  : Social Adaptability & I/E Tendencies in University Life
 Interface     : Streamlit web application
 Persistence   : JSON (primary), CSV, TXT
 Questions     : Loaded from external questions.json at runtime
=============================================================
"""

import streamlit as st
import json
import csv
import os
import re
import tempfile
from datetime import datetime


# ══════════════════════════════════════════════════════════════
#  SECTION 1 — GLOBAL CONSTANTS  (demonstrates all 10 variable types)
# ══════════════════════════════════════════════════════════════

APP_TITLE:      str       = "University Social Adaptability Survey"   # str
QUESTION_COUNT: int       = 20                                        # int
MAX_SCORE:      float     = 80.0                                      # float
SCORE_BANDS:    list      = [16, 32, 47, 63, 80]                      # list
STATE_LABELS:   tuple     = (                                         # tuple
    "Deep Introversion",
    "Introverted",
    "Ambivert",
    "Extroverted",
    "Social Dependency",
)
QUESTION_IDS:   range     = range(1, QUESTION_COUNT + 1)              # range
APP_READY:      bool      = False                                     # bool
SESSION_LOG:    dict      = {}                                        # dict
VALID_FORMATS:  set       = {"json", "csv", "txt"}                    # set
LOCKED_BANDS:   frozenset = frozenset({16, 32, 47, 63, 80})          # frozenset


# ══════════════════════════════════════════════════════════════
#  SECTION 2 — SURVEY RESULT CLASS
# ══════════════════════════════════════════════════════════════

class SurveyResult:
    """
    Stores and formats a completed survey result.
    Encapsulates participant info, answers, score, and classification.
    """

    def __init__(self, surname, given_name, date_of_birth,
                 student_id, total_score, label,
                 description, advice, answers_detail):
        self.surname       = surname
        self.given_name    = given_name
        self.date_of_birth = date_of_birth
        self.student_id    = student_id
        self.total_score   = total_score
        self.max_score     = int(MAX_SCORE)
        self.label         = label
        self.description   = description
        self.advice        = advice
        self.answers       = answers_detail
        self.timestamp     = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self):
        """Convert result to a serialisable dictionary."""
        return {
            "surname":       self.surname,
            "given_name":    self.given_name,
            "date_of_birth": self.date_of_birth,
            "student_id":    self.student_id,
            "total_score":   self.total_score,
            "max_score":     self.max_score,
            "result":        self.label,
            "description":   self.description,
            "advice":        self.advice,
            "timestamp":     self.timestamp,
            "answers":       self.answers,
        }

    def score_percentage(self):
        """Return score as a percentage of the maximum possible score."""
        return round((self.total_score / MAX_SCORE) * 100, 1)


# ══════════════════════════════════════════════════════════════
#  SECTION 3 — LOAD QUESTIONS FROM EXTERNAL FILE
# ══════════════════════════════════════════════════════════════

def load_questions(filepath="questions.json"):
    global APP_READY

    base_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_dir, filepath)

    with open(full_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    APP_READY = True
    return data


# ══════════════════════════════════════════════════════════════
#  SECTION 4 — INPUT VALIDATION FUNCTIONS
# ══════════════════════════════════════════════════════════════

def validate_name(name):
    """
    Validate a surname or given name string.

    Rules:
      - Only letters (a-z, A-Z), hyphens (-), apostrophes ('), and spaces.
      - No digits or other punctuation.
      - Minimum 2 characters after stripping whitespace.
      - Handles: O'Connor, Smith-Jones, Mary Ann.

    Uses a FOR LOOP to inspect each character individually.
    Returns (is_valid: bool, error_message: str).
    """
    name = name.strip()

    if len(name) < 2:
        return False, "Must be at least 2 characters long."

    # FOR LOOP — checks every character in the name
    for char in name:
        if not (char.isalpha() or char in (" ", "-", "'")):
            return False, (
                f"Invalid character '{char}'. "
                "Only letters, hyphens ( - ), apostrophes ( ' ), and spaces are allowed."
            )

    return True, ""


def validate_dob(dob):
    """
    Validate a date of birth string.

    Rules:
      - Format must be DD/MM/YYYY.
      - Day, month, year must be numerically valid.
      - Date must not be in the future.
      - Date must not be before 1900.

    Uses IF / ELIF / ELSE for range checks.
    Returns (is_valid: bool, error_message: str).
    """
    dob = dob.strip()

    if not re.match(r"^\d{2}/\d{2}/\d{4}$", dob):
        return False, "Format must be DD/MM/YYYY  (e.g. 15/03/2003)."

    day   = int(dob[0:2])
    month = int(dob[3:5])
    year  = int(dob[6:10])

    if month < 1 or month > 12:
        return False, "Month must be between 01 and 12."

    days_per_month = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    max_day = days_per_month[month - 1]

    if day < 1 or day > max_day:
        return False, f"Day must be between 01 and {max_day} for the given month."

    current_year = datetime.now().year
    if year < 1900 or year > current_year:
        return False, f"Year must be between 1900 and {current_year}."

    try:
        birth_date = datetime(year, month, day)
    except ValueError:
        return False, "This date does not exist (e.g. 30/02/2003 is invalid)."

    if birth_date > datetime.now():
        return False, "Date of birth cannot be in the future."

    return True, ""


def validate_student_id(sid):
    """
    Validate a student ID number.

    Rules:
      - Must contain digits only (0-9).
      - No letters, spaces, or punctuation allowed.
      - Minimum length of 4 digits.

    Uses a FOR LOOP to inspect each character individually.
    Returns (is_valid: bool, error_message: str).
    """
    sid = sid.strip()

    if len(sid) < 4:
        return False, "Student ID must be at least 4 digits long."

    # FOR LOOP — checks every character is a digit
    for char in sid:
        if not char.isdigit():
            return False, (
                f"Invalid character '{char}'. "
                "Student ID must contain digits only."
            )

    return True, ""


def validate_all_inputs(surname, given_name, dob, student_id):
    """
    Run all four validation checks and collect any error messages.

    Uses a WHILE LOOP to iterate through each validation rule
    until all checks are complete.
    Returns a list of error strings (empty list means all inputs are valid).
    """
    checks = [
        ("Surname",       validate_name,       surname),
        ("Given name",    validate_name,       given_name),
        ("Date of birth", validate_dob,        dob),
        ("Student ID",    validate_student_id, student_id),
    ]

    errors = []
    index  = 0

    # WHILE LOOP — iterates through all validation rules
    while index < len(checks):
        field_label, validator_fn, value = checks[index]
        is_valid, message = validator_fn(value)
        if not is_valid:
            errors.append(f"**{field_label}:** {message}")
        index += 1

    return errors


# ══════════════════════════════════════════════════════════════
#  SECTION 5 — SCORING AND CLASSIFICATION
# ══════════════════════════════════════════════════════════════

def calculate_score(answer_indices, questions):
    """
    Sum up the scores for each selected answer.
    Each question has a 'scores' list — the selected index maps to a score.
    Uses a FOR LOOP to iterate through every answer.
    Returns the total score as an integer.
    """
    total = 0
    # FOR LOOP — iterates through each answer index
    for i, idx in enumerate(answer_indices):
        score = questions[i]["scores"][idx]
        total += score
    return total


def classify_result(score):
    """
    Map a total score to one of 5 psychological states.
    Score range: 0-80  (20 questions x max 4 points each).

    Band breakdown:
      0-16  : Deep Introversion
      17-32 : Introverted
      33-47 : Ambivert
      48-63 : Extroverted
      64-80 : Social Dependency

    Uses IF / ELIF / ELSE conditional statements.
    Returns (label: str, description: str, advice: str).
    """
    if score <= 16:
        label       = "Deep Introversion"
        description = (
            "You show strong introverted tendencies and significant social "
            "withdrawal. Social situations feel consistently draining or uncomfortable."
        )
        advice = (
            "Consider speaking with a university counsellor or a trusted friend. "
            "Gradual, low-pressure social engagement can help build confidence over time."
        )

    elif score <= 32:
        label       = "Introverted"
        description = (
            "You have a clear preference for solitude and selective social engagement. "
            "You recharge through quiet time and favour smaller, meaningful interactions."
        )
        advice = (
            "This is a stable personality orientation. Seek out smaller group settings "
            "that align with your interests to maintain social wellbeing without overwhelm."
        )

    elif score <= 47:
        label       = "Ambivert"
        description = (
            "You sit comfortably in the middle of the introversion-extraversion spectrum. "
            "You adapt well to both social and solo settings depending on context."
        )
        advice = (
            "Your flexibility is a strength. Continue balancing social engagement with "
            "personal time — this balance is associated with high psychological wellbeing."
        )

    elif score <= 63:
        label       = "Extroverted"
        description = (
            "You have a strong preference for social interaction and thrive in group "
            "settings. You draw energy from being around others."
        )
        advice = (
            "Your social nature is an asset in university life. Be mindful of "
            "scheduling personal downtime to prevent overstimulation."
        )

    else:
        label       = "Social Dependency"
        description = (
            "You show very high social tendencies and may find it difficult to spend "
            "time alone. You may rely on social interaction for emotional regulation."
        )
        advice = (
            "Consider practising mindfulness or solo activities to build independence. "
            "A balance between social and alone time supports long-term mental wellbeing."
        )

    return label, description, advice


# ══════════════════════════════════════════════════════════════
#  SECTION 6 — FILE PERSISTENCE (SAVE / LOAD)
# ══════════════════════════════════════════════════════════════

def save_as_json(result, filepath):
    """
    Save a SurveyResult to a well-formatted JSON file.
    JSON is the primary format: lightweight, human-readable,
    easy to reload, and widely supported.
    Returns the filepath string.
    """
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, indent=4, ensure_ascii=False)
    return filepath


def save_as_csv(result, filepath):
    """
    Save a SurveyResult to a CSV file.
    Writes a summary block followed by a per-question answer table.
    Returns the filepath string.
    """
    data = result.to_dict()
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["=== SURVEY SUMMARY ==="])
        writer.writerow(["Field", "Value"])
        for key in ["surname", "given_name", "date_of_birth",
                    "student_id", "total_score", "max_score",
                    "result", "description", "advice", "timestamp"]:
            writer.writerow([key.replace("_", " ").title(), data[key]])
        writer.writerow([])
        writer.writerow(["=== ANSWERS ==="])
        writer.writerow(["#", "Question", "Selected Option", "Points"])
        for i, ans in enumerate(data["answers"], 1):
            writer.writerow([i, ans["question"], ans["selected_option"], ans["score"]])
    return filepath


def save_as_txt(result, filepath):
    """
    Save a SurveyResult to a plain text file.
    Produces a clearly formatted human-readable report.
    Returns the filepath string.
    """
    data = result.to_dict()
    sep  = "=" * 62
    lines = [
        sep,
        "   UNIVERSITY SOCIAL ADAPTABILITY SURVEY — RESULTS REPORT",
        sep,
        f"  Name          : {data['surname']}, {data['given_name']}",
        f"  Date of Birth : {data['date_of_birth']}",
        f"  Student ID    : {data['student_id']}",
        f"  Completed     : {data['timestamp']}",
        "-" * 62,
        f"  Score         : {data['total_score']} / {data['max_score']}  "
        f"({result.score_percentage()}%)",
        f"  Result        : {data['result']}",
        "",
        "  Description:",
        f"  {data['description']}",
        "",
        "  Recommendation:",
        f"  {data['advice']}",
        "-" * 62,
        "  QUESTION-BY-QUESTION ANSWERS",
        "-" * 62,
    ]
    for i, ans in enumerate(data["answers"], 1):
        lines.append(f"  Q{i:02d}. {ans['question']}")
        lines.append(f"       -> {ans['selected_option']}  [{ans['score']} pts]")
    lines.append(sep)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return filepath


def load_results_from_file(filepath):
    """
    Load and parse a previously saved results file.
    Supports JSON, CSV, and TXT formats.
    Uses IF / ELIF / ELSE to branch by file extension.
    Returns a dictionary of result data.
    """
    ext = filepath.rsplit(".", 1)[-1].lower()

    if ext == "json":
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    elif ext == "csv":
        rows = {}
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) == 2 and row[0] not in ("Field", ""):
                    rows[row[0]] = row[1]
        return rows

    elif ext == "txt":
        with open(filepath, "r", encoding="utf-8") as f:
            return {"raw_content": f.read()}

    else:
        return {"error": f"Unsupported format: '.{ext}'"}


def format_loaded_results(data):
    """
    Format loaded result data into a readable Markdown string.
    Handles JSON (full dict), CSV (flat dict), and TXT (raw string).
    """
    if "error" in data:
        return f"**Error:** {data['error']}"

    if "raw_content" in data:
        return f"```\n{data['raw_content']}\n```"

    name      = (f"{data.get('surname', data.get('Surname', '?'))}, "
                 f"{data.get('given_name', data.get('Given Name', '?'))}")
    score     = data.get("total_score",  data.get("Total Score",  "N/A"))
    max_s     = data.get("max_score",    data.get("Max Score",    80))
    result    = data.get("result",       data.get("Result",       "N/A"))
    desc      = data.get("description",  data.get("Description",  ""))
    advice    = data.get("advice",       data.get("Advice",       ""))
    timestamp = data.get("timestamp",    data.get("Timestamp",    ""))
    sid       = data.get("student_id",   data.get("Student Id",   "N/A"))

    md = f"""
### Loaded Survey Results

| Field | Value |
|---|---|
| **Name** | {name} |
| **Student ID** | {sid} |
| **Score** | {score} / {max_s} |
| **Result** | {result} |
| **Completed** | {timestamp} |

**Description:** {desc}

**Recommendation:** {advice}
"""
    answers = data.get("answers", [])
    if answers:
        md += "\n---\n**Question-by-question answers:**\n\n"
        for i, ans in enumerate(answers, 1):
            md += (f"**Q{i}.** {ans.get('question', '')}  \n"
                   f"-> *{ans.get('selected_option', '')}* "
                   f"[{ans.get('score', '')} pts]\n\n")
    return md


# ══════════════════════════════════════════════════════════════
#  SECTION 7 — STREAMLIT USER INTERFACE
# ══════════════════════════════════════════════════════════════

def build_app():
    """
    Construct the complete Streamlit web application.
    Loads questions from external file, builds all UI components,
    and wires up all event handlers via session state.
    """

    # ── Page config ───────────────────────────────────────────
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="🎓",
        layout="centered",
    )

    # ── Session state initialisation ──────────────────────────
    if "step" not in st.session_state:
        st.session_state.step = "details"          # details | questions | results
    if "confirmed_details" not in st.session_state:
        st.session_state.confirmed_details = {}
    if "survey_result" not in st.session_state:
        st.session_state.survey_result = None
    if "result_bytes" not in st.session_state:
        st.session_state.result_bytes = None
    if "result_filename" not in st.session_state:
        st.session_state.result_filename = ""

    # ── Load questions ────────────────────────────────────────
    questions = load_questions("questions.json")

    # ── Header ───────────────────────────────────────────────
    st.title(f"🎓 {APP_TITLE}")
    st.markdown("### Westminster International University in Tashkent — 4BUIS008C")
    st.divider()

    # ── Mode selector ─────────────────────────────────────────
    mode = st.radio(
        "Select an option to get started",
        options=["Start a new survey", "Load existing results"],
        horizontal=True,
    )

    st.divider()

    # ══════════════════════════════════════════════════════════
    # PANEL A — NEW SURVEY
    # ══════════════════════════════════════════════════════════
    if mode == "Start a new survey":

        # ── Restart button (shown once past details) ──────────
        if st.session_state.step in ("questions", "results"):
            if st.button("↩ Take the survey again", type="secondary"):
                st.session_state.step = "details"
                st.session_state.confirmed_details = {}
                st.session_state.survey_result = None
                st.session_state.result_bytes = None
                st.session_state.result_filename = ""
                st.rerun()

        # ── STEP 1: Personal Details ──────────────────────────
        st.markdown("## Step 1 — Personal Details")
        st.markdown(
            "All fields are required before the survey will begin.\n\n"
            "- **Name fields:** letters, hyphens, apostrophes, and spaces only.\n"
            "- **Date of birth:** DD/MM/YYYY format.\n"
            "- **Student ID:** digits only."
        )

        col1, col2 = st.columns(2)
        with col1:
            inp_surname = st.text_input(
                "Surname",
                placeholder="e.g. Smith-Jones",
                value=st.session_state.confirmed_details.get("surname", ""),
                disabled=(st.session_state.step != "details"),
            )
        with col2:
            inp_given_name = st.text_input(
                "Given Name",
                placeholder="e.g. Mary Ann",
                value=st.session_state.confirmed_details.get("given_name", ""),
                disabled=(st.session_state.step != "details"),
            )

        col3, col4 = st.columns(2)
        with col3:
            inp_dob = st.text_input(
                "Date of Birth (DD/MM/YYYY)",
                placeholder="e.g. 15/03/2003",
                value=st.session_state.confirmed_details.get("date_of_birth", ""),
                disabled=(st.session_state.step != "details"),
            )
        with col4:
            inp_student_id = st.text_input(
                "Student ID",
                placeholder="e.g. 00123456",
                value=st.session_state.confirmed_details.get("student_id", ""),
                disabled=(st.session_state.step != "details"),
            )

        # Confirm details button — only shown on step 1
        if st.session_state.step == "details":
            if st.button("Confirm Details and Begin Survey", type="primary"):
                errors = validate_all_inputs(
                    inp_surname, inp_given_name, inp_dob, inp_student_id
                )
                if errors:
                    st.error("### Please correct the following:\n\n" +
                             "\n".join(f"- {e}" for e in errors))
                else:
                    st.session_state.confirmed_details = {
                        "surname":       inp_surname.strip(),
                        "given_name":    inp_given_name.strip(),
                        "date_of_birth": inp_dob.strip(),
                        "student_id":    inp_student_id.strip(),
                    }
                    st.session_state.step = "questions"
                    st.rerun()

        # Confirmed banner
        if st.session_state.step in ("questions", "results"):
            st.success("**Details confirmed.** Please answer all 20 questions below.")

        # ── STEP 2: Questions ─────────────────────────────────
        if st.session_state.step in ("questions", "results"):
            st.divider()
            st.markdown("## Step 2 — Survey Questions")
            st.markdown(
                "Read each statement carefully and select the option that "
                "best reflects your experience. There are no right or wrong answers."
            )

            answers = []
            for q in questions:
                chosen = st.radio(
                    f"**Q{q['id']}.** {q['text']}",
                    options=q["options"],
                    index=None,
                    key=f"q_{q['id']}",
                    disabled=(st.session_state.step == "results"),
                )
                answers.append(chosen)

            st.divider()
            st.markdown("## Step 3 — Save Format")
            st.markdown(
                "Choose how your results will be saved. "
                "**JSON** is recommended as it stores the most complete record."
            )
            inp_format = st.radio(
                "File format for saving results",
                options=["JSON", "CSV", "TXT"],
                index=0,
                horizontal=True,
                disabled=(st.session_state.step == "results"),
            )

            # Submit button — only shown on step 2
            if st.session_state.step == "questions":
                if st.button("Submit Survey", type="primary"):
                    # FOR LOOP — check every question has been answered
                    unanswered = []
                    for i, ans in enumerate(answers):
                        if ans is None:
                            unanswered.append(f"Q{i + 1}")

                    if unanswered:
                        st.error(
                            f"**Please answer all questions.**  \n"
                            f"Unanswered: {', '.join(unanswered)}"
                        )
                    else:
                        # Convert selected option text to index, then look up score
                        answer_indices = []
                        for q_idx, selected in enumerate(answers):
                            opts = questions[q_idx]["options"]
                            idx  = opts.index(selected)
                            answer_indices.append(idx)

                        # Calculate total score and classify
                        total = calculate_score(answer_indices, questions)
                        label, description, advice = classify_result(total)

                        # Build answers detail list
                        answers_detail = []
                        for i, (q, idx) in enumerate(zip(questions, answer_indices)):
                            answers_detail.append({
                                "question_id":     q["id"],
                                "question":        q["text"],
                                "selected_option": q["options"][idx],
                                "score":           q["scores"][idx],
                            })

                        # Create SurveyResult object
                        details = st.session_state.confirmed_details
                        result = SurveyResult(
                            surname        = details["surname"],
                            given_name     = details["given_name"],
                            date_of_birth  = details["date_of_birth"],
                            student_id     = details["student_id"],
                            total_score    = total,
                            label          = label,
                            description    = description,
                            advice         = advice,
                            answers_detail = answers_detail,
                        )

                        # Save to chosen format
                        safe_surname = re.sub(r"[^a-zA-Z0-9]", "_", details["surname"])
                        ext          = inp_format.lower()
                        filename     = (
                            f"results_{safe_surname}_{details['student_id']}.{ext}"
                        )
                        tmp_path = os.path.join(tempfile.gettempdir(), filename)

                        if ext == "json":
                            save_as_json(result, tmp_path)
                        elif ext == "csv":
                            save_as_csv(result, tmp_path)
                        else:
                            save_as_txt(result, tmp_path)

                        # Read bytes for download button
                        with open(tmp_path, "rb") as fh:
                            file_bytes = fh.read()

                        # Log to session store
                        SESSION_LOG[result.student_id] = result.to_dict()

                        # Persist result in session state
                        st.session_state.survey_result   = result
                        st.session_state.result_bytes    = file_bytes
                        st.session_state.result_filename = filename
                        st.session_state.step            = "results"
                        st.rerun()

        # ── STEP 4: Results ───────────────────────────────────
        if st.session_state.step == "results":
            result = st.session_state.survey_result
            pct    = result.score_percentage()

            st.divider()
            st.markdown("## Your Results")

            st.markdown(f"## {result.label}")
            st.markdown(f"**Score: {result.total_score} / {int(MAX_SCORE)} ({pct}%)**")
            st.progress(result.total_score / int(MAX_SCORE))
            st.markdown(result.description)
            st.divider()
            st.markdown(f"**Recommendation:**\n\n{result.advice}")
            st.divider()

            mime_map = {
                "json": "application/json",
                "csv":  "text/csv",
                "txt":  "text/plain",
            }
            ext  = st.session_state.result_filename.rsplit(".", 1)[-1].lower()
            mime = mime_map.get(ext, "application/octet-stream")

            st.download_button(
                label="⬇ Download your results file",
                data=st.session_state.result_bytes,
                file_name=st.session_state.result_filename,
                mime=mime,
                type="primary",
            )

    # ══════════════════════════════════════════════════════════
    # PANEL B — LOAD EXISTING RESULTS
    # ══════════════════════════════════════════════════════════
    else:
        st.markdown("## Load Existing Results")
        st.markdown(
            "Upload a previously saved results file to view its contents.  \n"
            "Accepted formats: **JSON**, **CSV**, **TXT**."
        )

        uploaded = st.file_uploader(
            "Upload results file",
            type=["json", "csv", "txt"],
        )

        if st.button("Load and Display Results", type="primary"):
            if uploaded is None:
                st.error("**Please upload a file first.**")
            else:
                # Write uploaded file to a temp path so load_results_from_file
                # can use its extension-based branching logic unchanged
                ext      = uploaded.name.rsplit(".", 1)[-1].lower()
                tmp_path = os.path.join(tempfile.gettempdir(), f"uploaded_result.{ext}")
                with open(tmp_path, "wb") as fh:
                    fh.write(uploaded.read())

                data = load_results_from_file(tmp_path)
                st.markdown(format_loaded_results(data))


# ══════════════════════════════════════════════════════════════
#  SECTION 8 — ENTRY POINT
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    build_app()
else:
    # When run via `streamlit run app.py`, Streamlit calls the module
    # at import time, so we call build_app() at module level too.
    build_app()