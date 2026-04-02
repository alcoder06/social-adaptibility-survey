"""
=============================================================
 Social Adaptability and Introversion-Extraversion Survey
 Westminster International University in Tashkent
 Module: Fundamentals of Programming — 4BUIS008C (Level 4)
 Project 1 — Psychological State Survey
=============================================================
 Survey topic  : Social Adaptability & I/E Tendencies in University Life
 Interface     : Gradio web application (Hugging Face Spaces)
 Persistence   : JSON (primary), CSV, TXT
 Questions     : Loaded from external questions.json at runtime
=============================================================
"""

import gradio as gr
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
    """
    Load survey questions from an external JSON file at programme startup.
    Separates data from logic — questions can be changed without editing code.
    Returns a list of question dictionaries.
    """
    global APP_READY
    with open(filepath, "r", encoding="utf-8") as f:
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
#  SECTION 7 — GRADIO USER INTERFACE
# ══════════════════════════════════════════════════════════════

def build_app():
    """
    Construct the complete Gradio web application.
    Loads questions from external file, builds all UI components,
    and wires up all event handlers.
    Returns a Gradio Blocks app ready for launch.
    """
    # Load questions from external JSON file at startup
    questions = load_questions("questions.json")

    css = """
    .gradio-container { max-width: 820px !important; margin: 0 auto !important; }
    .question-block   { margin-bottom: 6px; }
    .result-panel     { border-radius: 10px; padding: 8px; }
    footer            { display: none !important; }
    """

    with gr.Blocks(css=css, title=APP_TITLE) as app:

        # ── Header ────────────────────────────────────────────
        gr.Markdown(f"""
# {APP_TITLE}
### Westminster International University in Tashkent — 4BUIS008C
---
""")

        # ── Mode selector ─────────────────────────────────────
        mode_radio = gr.Radio(
            choices=["Start a new survey", "Load existing results"],
            value="Start a new survey",
            label="Select an option to get started",
            interactive=True,
        )

        # ══════════════════════════════════════════════════════
        # PANEL A — NEW SURVEY
        # ══════════════════════════════════════════════════════
        with gr.Column(visible=True) as panel_new:

            # — Step 1: Personal details ———————————————————————
            gr.Markdown("## Step 1 — Personal Details")
            gr.Markdown(
                "All fields are required before the survey will begin.\n\n"
                "- **Name fields:** letters, hyphens, apostrophes, and spaces only.\n"
                "- **Date of birth:** DD/MM/YYYY format.\n"
                "- **Student ID:** digits only."
            )

            with gr.Row():
                inp_surname    = gr.Textbox(
                    label="Surname",
                    placeholder="e.g. Smith-Jones",
                    max_lines=1
                )
                inp_given_name = gr.Textbox(
                    label="Given Name",
                    placeholder="e.g. Mary Ann",
                    max_lines=1
                )
            with gr.Row():
                inp_dob        = gr.Textbox(
                    label="Date of Birth  (DD/MM/YYYY)",
                    placeholder="e.g. 15/03/2003",
                    max_lines=1
                )
                inp_student_id = gr.Textbox(
                    label="Student ID",
                    placeholder="e.g. 00123456",
                    max_lines=1
                )

            out_validation = gr.Markdown(visible=False)
            btn_confirm    = gr.Button(
                "Confirm Details and Begin Survey",
                variant="primary"
            )

            # — Step 2: Questions ——————————————————————————————
            with gr.Column(visible=False) as panel_questions:
                gr.Markdown("---")
                gr.Markdown("## Step 2 — Survey Questions")
                gr.Markdown(
                    "Read each statement carefully and select the option that "
                    "best reflects your experience. There are no right or wrong answers."
                )

                answer_widgets = []
                for q in questions:
                    radio = gr.Radio(
                        choices=q["options"],
                        label=f"Q{q['id']}.  {q['text']}",
                        elem_classes=["question-block"],
                        interactive=True,
                    )
                    answer_widgets.append(radio)

                gr.Markdown("---")
                gr.Markdown("## Step 3 — Save Format")
                gr.Markdown(
                    "Choose how your results will be saved. "
                    "**JSON** is recommended as it stores the most complete record."
                )
                inp_format = gr.Radio(
                    choices=["JSON", "CSV", "TXT"],
                    value="JSON",
                    label="File format for saving results",
                    interactive=True,
                )

                btn_submit = gr.Button(
                    "Submit Survey",
                    variant="primary",
                    size="lg"
                )

            # — Step 4: Results ————————————————————————————————
            with gr.Column(visible=False) as panel_results:
                gr.Markdown("---")
                gr.Markdown("## Your Results")
                out_result_md = gr.Markdown(elem_classes=["result-panel"])
                out_score_bar = gr.Slider(
                    minimum=0, maximum=80, value=0,
                    label="Your Score (out of 80)",
                    interactive=False
                )
                out_file    = gr.File(label="Download your results file")
                btn_restart = gr.Button(
                    "Take the survey again",
                    variant="secondary"
                )

        # ══════════════════════════════════════════════════════
        # PANEL B — LOAD EXISTING RESULTS
        # ══════════════════════════════════════════════════════
        with gr.Column(visible=False) as panel_load:
            gr.Markdown("## Load Existing Results")
            gr.Markdown(
                "Upload a previously saved results file to view its contents.  \n"
                "Accepted formats: **JSON**, **CSV**, **TXT**."
            )
            inp_upload = gr.File(
                label="Upload results file",
                file_types=[".json", ".csv", ".txt"]
            )
            btn_load   = gr.Button("Load and Display Results", variant="primary")
            out_loaded = gr.Markdown()

        # ══════════════════════════════════════════════════════
        # EVENT HANDLERS
        # ══════════════════════════════════════════════════════

        # — Switch mode ————————————————————————————————————————
        def on_mode_change(choice):
            is_new = "new survey" in choice
            return (
                gr.update(visible=is_new),
                gr.update(visible=not is_new),
            )

        mode_radio.change(
            fn=on_mode_change,
            inputs=[mode_radio],
            outputs=[panel_new, panel_load],
        )

        # — Confirm details ————————————————————————————————————
        def on_confirm(surname, given_name, dob, student_id):
            """
            Validate all personal detail inputs.
            Shows question panel only when all inputs pass validation.
            Calls validate_all_inputs() which uses a WHILE loop internally.
            """
            errors = validate_all_inputs(surname, given_name, dob, student_id)

            if errors:
                msg = "### Please correct the following:\n\n" + \
                      "\n".join(f"- {e}" for e in errors)
                return (
                    gr.update(value=msg, visible=True),
                    gr.update(visible=False),
                )

            return (
                gr.update(
                    value="**Details confirmed.** Please answer all 20 questions below.",
                    visible=True,
                ),
                gr.update(visible=True),
            )

        btn_confirm.click(
            fn=on_confirm,
            inputs=[inp_surname, inp_given_name, inp_dob, inp_student_id],
            outputs=[out_validation, panel_questions],
        )

        # — Submit survey ——————————————————————————————————————
        def on_submit(surname, given_name, dob, student_id, fmt, *answers):
            """
            Validate all answers are selected, calculate total score,
            classify psychological state, build SurveyResult object,
            save to chosen file format, and return display components.
            """
            # Check every question has been answered using a FOR LOOP
            unanswered = []
            for i, ans in enumerate(answers):
                if ans is None:
                    unanswered.append(f"Q{i + 1}")

            if unanswered:
                missing = ", ".join(unanswered)
                return (
                    gr.update(visible=False),
                    gr.update(value=f"**Please answer all questions.**  \n"
                                    f"Unanswered: {missing}"),
                    gr.update(value=0),
                    gr.update(value=None),
                )

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
            result = SurveyResult(
                surname        = surname.strip(),
                given_name     = given_name.strip(),
                date_of_birth  = dob.strip(),
                student_id     = student_id.strip(),
                total_score    = total,
                label          = label,
                description    = description,
                advice         = advice,
                answers_detail = answers_detail,
            )

            # Save to chosen format in a temp directory for download
            safe_surname = re.sub(r"[^a-zA-Z0-9]", "_", surname.strip())
            ext          = fmt.lower()
            filename     = f"results_{safe_surname}_{student_id.strip()}.{ext}"
            tmp_path     = os.path.join(tempfile.gettempdir(), filename)

            if ext == "json":
                save_as_json(result, tmp_path)
            elif ext == "csv":
                save_as_csv(result, tmp_path)
            else:
                save_as_txt(result, tmp_path)

            # Log to session store
            SESSION_LOG[result.student_id] = result.to_dict()

            # Build result Markdown display
            pct = result.score_percentage()
            md = f"""
## {label}

**Score: {total} / {int(MAX_SCORE)} ({pct}%)**

{description}

---

**Recommendation:**

{advice}

---
*Results saved as `{filename}` — click the download button below.*
"""
            return (
                gr.update(visible=True),
                gr.update(value=md),
                gr.update(value=total),
                gr.update(value=tmp_path),
            )

        btn_submit.click(
            fn=on_submit,
            inputs=[
                inp_surname, inp_given_name,
                inp_dob, inp_student_id, inp_format,
                *answer_widgets,
            ],
            outputs=[panel_results, out_result_md, out_score_bar, out_file],
        )

        # — Restart ————————————————————————————————————————————
        def on_restart():
            """Reset all inputs and hide question and result panels."""
            blanks = [gr.update(value=None) for _ in answer_widgets]
            return (
                gr.update(value=""),
                gr.update(value=""),
                gr.update(value=""),
                gr.update(value=""),
                gr.update(value="", visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                *blanks,
            )

        btn_restart.click(
            fn=on_restart,
            inputs=[],
            outputs=[
                inp_surname, inp_given_name,
                inp_dob, inp_student_id,
                out_validation, panel_questions, panel_results,
                *answer_widgets,
            ],
        )

        # — Load existing results ——————————————————————————————
        def on_load(file_obj):
            """
            Read an uploaded results file and render its contents.
            Delegates parsing to load_results_from_file() and
            formatting to format_loaded_results().
            """
            if file_obj is None:
                return "**Please upload a file first.**"

            data = load_results_from_file(file_obj.name)
            return format_loaded_results(data)

        btn_load.click(
            fn=on_load,
            inputs=[inp_upload],
            outputs=[out_loaded],
        )

    return app


# ══════════════════════════════════════════════════════════════
#  SECTION 8 — ENTRY POINT
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    survey_app = build_app()
    survey_app.launch(share=True)