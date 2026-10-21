"""
app.py – CampusSkill Flask Application
"""
from flask import (Flask, render_template, redirect, url_for,
                   request, session, flash, jsonify, abort)
from functools import wraps
import bcrypt
from datetime import datetime, date
from config import Config
import db as DB

app = Flask(__name__)
app.config.from_object(Config)

# ─── Auth decorator ────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "student_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def current_user():
    if "student_id" not in session:
        return None
    return DB.query_one("SELECT * FROM students WHERE id=%s", (session["student_id"],))


# ─── Context processor ─────────────────────────────────────────────────────────
@app.context_processor
def inject_user():
    return {"current_user": current_user()}


# ─── Error handlers ────────────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", code=404, message="Page not found."), 404


@app.errorhandler(403)
def forbidden(e):
    return render_template("error.html", code=403, message="Access denied."), 403


@app.errorhandler(500)
def server_error(e):
    return render_template("error.html", code=500,
                           message="Server error. Check your database connection."), 500


# ═══════════════════════════════════════════════════════════════════════════════
#  LANDING
# ═══════════════════════════════════════════════════════════════════════════════
@app.route("/")
def index():
    try:
        popular = DB.query_all("""
            SELECT sk.skill_name, sk.category, sk.proficiency_level,
                   st.full_name, st.department,
                   COALESCE(AVG(f.rating),0) AS avg_rating,
                   COUNT(f.id) AS review_count
            FROM skills sk
            JOIN students st ON sk.student_id = st.id
            LEFT JOIN feedback f ON f.provider_id = st.id
            GROUP BY sk.id
            ORDER BY avg_rating DESC, review_count DESC
            LIMIT 6
        """)
    except Exception:
        popular = []
    return render_template("index.html", popular=popular)


# ═══════════════════════════════════════════════════════════════════════════════
#  AUTHENTICATION
# ═══════════════════════════════════════════════════════════════════════════════
@app.route("/register", methods=["GET", "POST"])
def register():
    if "student_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        full_name     = request.form.get("full_name", "").strip()
        email         = request.form.get("email", "").strip().lower()
        password      = request.form.get("password", "")
        department    = request.form.get("department", "").strip()
        academic_year = request.form.get("academic_year", "").strip()

        errors = []
        if not full_name:
            errors.append("Full name is required.")
        if not email or "@" not in email:
            errors.append("Valid email is required.")
        if len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        if not department:
            errors.append("Department is required.")
        if not academic_year:
            errors.append("Academic year is required.")

        if not errors:
            existing = DB.query_one("SELECT id FROM students WHERE email=%s", (email,))
            if existing:
                errors.append("An account with this email already exists.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("register.html",
                                   form_data=request.form)

        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        try:
            student_id = DB.execute(
                "INSERT INTO students (full_name, email, password, department, academic_year) "
                "VALUES (%s,%s,%s,%s,%s)",
                (full_name, email, pw_hash, department, academic_year),
                lastrowid=True
            )
            session["student_id"] = student_id
            session["student_name"] = full_name
            flash(f"Welcome, {full_name}! Your account has been created.", "success")
            return redirect(url_for("dashboard"))
        except Exception as ex:
            flash("Registration failed. Please try again.", "danger")
            app.logger.error("Register error: %s", ex)

    return render_template("register.html", form_data={})


@app.route("/login", methods=["GET", "POST"])
def login():
    if "student_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Email and password are required.", "danger")
            return render_template("login.html")

        student = DB.query_one("SELECT * FROM students WHERE email=%s", (email,))
        if student and bcrypt.checkpw(password.encode(), student["password"].encode()):
            session["student_id"]   = student["id"]
            session["student_name"] = student["full_name"]
            flash(f"Welcome back, {student['full_name']}!", "success")
            nxt = request.args.get("next")
            return redirect(nxt or url_for("dashboard"))
        else:
            flash("Invalid email or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


# ═══════════════════════════════════════════════════════════════════════════════
#  DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
@app.route("/dashboard")
@login_required
def dashboard():
    sid = session["student_id"]

    skills_count = DB.query_one(
        "SELECT COUNT(*) AS c FROM skills WHERE student_id=%s", (sid,))["c"]

    pending_requests = DB.query_one(
        "SELECT COUNT(*) AS c FROM learning_requests "
        "WHERE provider_id=%s AND status='Pending'", (sid,))["c"]

    upcoming_sessions = DB.query_one(
        "SELECT COUNT(*) AS c FROM sessions "
        "WHERE (learner_id=%s OR provider_id=%s) AND status='Scheduled'",
        (sid, sid))["c"]

    avg_rating_row = DB.query_one(
        "SELECT ROUND(AVG(f.rating),1) AS avg_r FROM feedback f WHERE f.provider_id=%s", (sid,))
    avg_rating = avg_rating_row["avg_r"] if avg_rating_row["avg_r"] else 0

    recent_skills = DB.query_all(
        "SELECT * FROM skills WHERE student_id=%s ORDER BY created_at DESC LIMIT 4", (sid,))

    recent_requests = DB.query_all("""
        SELECT lr.*, sk.skill_name,
               learner.full_name AS learner_name,
               provider.full_name AS provider_name
        FROM learning_requests lr
        JOIN skills sk ON lr.skill_id = sk.id
        JOIN students learner  ON lr.learner_id  = learner.id
        JOIN students provider ON lr.provider_id = provider.id
        WHERE lr.learner_id=%s OR lr.provider_id=%s
        ORDER BY lr.updated_at DESC LIMIT 5
    """, (sid, sid))

    return render_template("dashboard.html",
                           skills_count=skills_count,
                           pending_requests=pending_requests,
                           upcoming_sessions=upcoming_sessions,
                           avg_rating=avg_rating,
                           recent_skills=recent_skills,
                           recent_requests=recent_requests)


# ═══════════════════════════════════════════════════════════════════════════════
#  PROFILE
# ═══════════════════════════════════════════════════════════════════════════════
@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    sid = session["student_id"]
    student = DB.query_one("SELECT * FROM students WHERE id=%s", (sid,))

    if request.method == "POST":
        full_name     = request.form.get("full_name", "").strip()
        department    = request.form.get("department", "").strip()
        academic_year = request.form.get("academic_year", "").strip()
        bio           = request.form.get("bio", "").strip()

        if not full_name or not department or not academic_year:
            flash("Name, department and academic year are required.", "danger")
        else:
            DB.execute(
                "UPDATE students SET full_name=%s, department=%s, academic_year=%s, bio=%s "
                "WHERE id=%s",
                (full_name, department, academic_year, bio, sid)
            )
            session["student_name"] = full_name
            flash("Profile updated successfully.", "success")
            return redirect(url_for("profile"))

    skills = DB.query_all(
        "SELECT * FROM skills WHERE student_id=%s ORDER BY skill_name", (sid,))
    avg_row = DB.query_one(
        "SELECT ROUND(AVG(rating),1) AS avg_r, COUNT(*) AS cnt "
        "FROM feedback WHERE provider_id=%s", (sid,))
    feedback_list = DB.query_all("""
        SELECT f.*, s2.full_name AS learner_name, se.session_date, sk.skill_name
        FROM feedback f
        JOIN students s2 ON f.learner_id = s2.id
        JOIN sessions se ON f.session_id = se.id
        JOIN learning_requests lr ON se.request_id = lr.id
        JOIN skills sk ON lr.skill_id = sk.id
        WHERE f.provider_id=%s
        ORDER BY f.created_at DESC LIMIT 10
    """, (sid,))

    return render_template("profile.html", student=student, skills=skills,
                           avg_rating=avg_row["avg_r"] or 0,
                           review_count=avg_row["cnt"],
                           feedback_list=feedback_list)


@app.route("/profile/<int:uid>")
@login_required
def public_profile(uid):
    student = DB.query_one("SELECT * FROM students WHERE id=%s", (uid,))
    if not student:
        abort(404)
    skills = DB.query_all(
        "SELECT * FROM skills WHERE student_id=%s ORDER BY skill_name", (uid,))
    avg_row = DB.query_one(
        "SELECT ROUND(AVG(rating),1) AS avg_r, COUNT(*) AS cnt "
        "FROM feedback WHERE provider_id=%s", (uid,))
    feedback_list = DB.query_all("""
        SELECT f.*, s2.full_name AS learner_name, se.session_date, sk.skill_name
        FROM feedback f
        JOIN students s2 ON f.learner_id = s2.id
        JOIN sessions se ON f.session_id = se.id
        JOIN learning_requests lr ON se.request_id = lr.id
        JOIN skills sk ON lr.skill_id = sk.id
        WHERE f.provider_id=%s
        ORDER BY f.created_at DESC
    """, (uid,))
    return render_template("public_profile.html", student=student,
                           skills=skills,
                           avg_rating=avg_row["avg_r"] or 0,
                           review_count=avg_row["cnt"],
                           feedback_list=feedback_list)


# ═══════════════════════════════════════════════════════════════════════════════
#  SKILL MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════
CATEGORIES = ['Programming','Database','Web Development','AI/ML','Design','Communication','Other']
LEVELS      = ['Beginner','Intermediate','Advanced']

@app.route("/skills")
@login_required
def skills():
    sid = session["student_id"]
    my_skills = DB.query_all(
        "SELECT * FROM skills WHERE student_id=%s ORDER BY category, skill_name", (sid,))
    return render_template("skills.html", skills=my_skills,
                           categories=CATEGORIES, levels=LEVELS)


@app.route("/skills/add", methods=["POST"])
@login_required
def add_skill():
    sid        = session["student_id"]
    skill_name = request.form.get("skill_name","").strip()
    category   = request.form.get("category","").strip()
    level      = request.form.get("proficiency_level","").strip()
    desc       = request.form.get("description","").strip()

    if not skill_name or category not in CATEGORIES or level not in LEVELS:
        flash("Please fill all required skill fields correctly.", "danger")
        return redirect(url_for("skills"))

    existing = DB.query_one(
        "SELECT id FROM skills WHERE student_id=%s AND LOWER(skill_name)=LOWER(%s)",
        (sid, skill_name))
    if existing:
        flash(f"You already have a skill named '{skill_name}'.", "warning")
        return redirect(url_for("skills"))

    DB.execute(
        "INSERT INTO skills (student_id, skill_name, category, proficiency_level, description) "
        "VALUES (%s,%s,%s,%s,%s)",
        (sid, skill_name, category, level, desc)
    )
    flash(f"Skill '{skill_name}' added.", "success")
    return redirect(url_for("skills"))


@app.route("/skills/edit/<int:skill_id>", methods=["POST"])
@login_required
def edit_skill(skill_id):
    sid   = session["student_id"]
    skill = DB.query_one("SELECT * FROM skills WHERE id=%s AND student_id=%s", (skill_id, sid))
    if not skill:
        abort(403)

    skill_name = request.form.get("skill_name","").strip()
    category   = request.form.get("category","").strip()
    level      = request.form.get("proficiency_level","").strip()
    desc       = request.form.get("description","").strip()

    if not skill_name or category not in CATEGORIES or level not in LEVELS:
        flash("Please fill all required fields.", "danger")
        return redirect(url_for("skills"))

    # Check duplicate (excluding self)
    dup = DB.query_one(
        "SELECT id FROM skills WHERE student_id=%s AND LOWER(skill_name)=LOWER(%s) AND id!=%s",
        (sid, skill_name, skill_id))
    if dup:
        flash(f"You already have a skill named '{skill_name}'.", "warning")
        return redirect(url_for("skills"))

    DB.execute(
        "UPDATE skills SET skill_name=%s, category=%s, proficiency_level=%s, description=%s "
        "WHERE id=%s AND student_id=%s",
        (skill_name, category, level, desc, skill_id, sid)
    )
    flash("Skill updated.", "success")
    return redirect(url_for("skills"))


@app.route("/skills/delete/<int:skill_id>", methods=["POST"])
@login_required
def delete_skill(skill_id):
    sid = session["student_id"]
    skill = DB.query_one("SELECT * FROM skills WHERE id=%s AND student_id=%s", (skill_id, sid))
    if not skill:
        abort(403)
    DB.execute("DELETE FROM skills WHERE id=%s AND student_id=%s", (skill_id, sid))
    flash("Skill deleted.", "success")
    return redirect(url_for("skills"))


# ═══════════════════════════════════════════════════════════════════════════════
#  EXPLORE SKILLS
# ═══════════════════════════════════════════════════════════════════════════════
@app.route("/explore")
@login_required
def explore():
    sid      = session["student_id"]
    q        = request.args.get("q","").strip()
    cat      = request.args.get("category","").strip()
    level    = request.args.get("level","").strip()

    sql = """
        SELECT sk.id AS skill_id, sk.skill_name, sk.category, sk.proficiency_level,
               sk.description, st.id AS provider_id, st.full_name, st.department,
               COALESCE(ROUND(AVG(f.rating),1),0) AS avg_rating,
               COUNT(f.id) AS review_count
        FROM skills sk
        JOIN students st ON sk.student_id = st.id
        LEFT JOIN feedback f ON f.provider_id = st.id
        WHERE sk.student_id != %s
    """
    params = [sid]

    if q:
        sql += " AND (sk.skill_name LIKE %s OR sk.description LIKE %s)"
        params += [f"%{q}%", f"%{q}%"]
    if cat and cat in CATEGORIES:
        sql += " AND sk.category = %s"
        params.append(cat)
    if level and level in LEVELS:
        sql += " AND sk.proficiency_level = %s"
        params.append(level)

    sql += " GROUP BY sk.id ORDER BY avg_rating DESC, sk.skill_name"

    results = DB.query_all(sql, params)
    return render_template("explore.html", results=results,
                           categories=CATEGORIES, levels=LEVELS,
                           q=q, selected_cat=cat, selected_level=level)


# ═══════════════════════════════════════════════════════════════════════════════
#  LEARNING REQUESTS
# ═══════════════════════════════════════════════════════════════════════════════
@app.route("/requests")
@login_required
def requests_page():
    sid = session["student_id"]

    incoming = DB.query_all("""
        SELECT lr.*, sk.skill_name, st.full_name AS learner_name, st.department
        FROM learning_requests lr
        JOIN skills sk ON lr.skill_id = sk.id
        JOIN students st ON lr.learner_id = st.id
        WHERE lr.provider_id=%s
        ORDER BY lr.updated_at DESC
    """, (sid,))

    sent = DB.query_all("""
        SELECT lr.*, sk.skill_name, st.full_name AS provider_name, st.department
        FROM learning_requests lr
        JOIN skills sk ON lr.skill_id = sk.id
        JOIN students st ON lr.provider_id = st.id
        WHERE lr.learner_id=%s
        ORDER BY lr.updated_at DESC
    """, (sid,))

    return render_template("requests.html", incoming=incoming, sent=sent)


@app.route("/requests/send", methods=["POST"])
@login_required
def send_request():
    sid         = session["student_id"]
    provider_id = request.form.get("provider_id", type=int)
    skill_id    = request.form.get("skill_id",    type=int)
    message     = request.form.get("message","").strip()
    pref_time   = request.form.get("preferred_time","").strip()

    if not provider_id or not skill_id:
        flash("Invalid request parameters.", "danger")
        return redirect(url_for("explore"))

    # Verify skill belongs to provider
    skill = DB.query_one(
        "SELECT * FROM skills WHERE id=%s AND student_id=%s", (skill_id, provider_id))
    if not skill:
        flash("Skill not found.", "danger")
        return redirect(url_for("explore"))

    # Prevent self-request
    if provider_id == sid:
        flash("You cannot send a request to yourself.", "warning")
        return redirect(url_for("explore"))

    # Prevent duplicate active request
    active = DB.query_one("""
        SELECT id FROM learning_requests
        WHERE learner_id=%s AND provider_id=%s AND skill_id=%s
          AND status IN ('Pending','Accepted')
    """, (sid, provider_id, skill_id))
    if active:
        flash("You already have an active request for this skill.", "warning")
        return redirect(url_for("explore"))

    DB.execute(
        "INSERT INTO learning_requests (learner_id, provider_id, skill_id, message, preferred_time) "
        "VALUES (%s,%s,%s,%s,%s)",
        (sid, provider_id, skill_id, message, pref_time)
    )
    flash("Learning request sent!", "success")
    return redirect(url_for("requests_page"))


@app.route("/requests/<int:req_id>/status", methods=["POST"])
@login_required
def update_request_status(req_id):
    sid    = session["student_id"]
    new_st = request.form.get("status","")
    req    = DB.query_one("SELECT * FROM learning_requests WHERE id=%s", (req_id,))

    if not req:
        abort(404)

    # Authorization rules
    if new_st in ("Accepted","Rejected") and req["provider_id"] != sid:
        abort(403)
    if new_st == "Cancelled" and req["learner_id"] != sid:
        abort(403)
    if new_st not in ("Accepted","Rejected","Cancelled"):
        flash("Invalid action.", "danger")
        return redirect(url_for("requests_page"))
    if req["status"] != "Pending":
        flash("Only pending requests can be updated.", "warning")
        return redirect(url_for("requests_page"))

    DB.execute(
        "UPDATE learning_requests SET status=%s WHERE id=%s",
        (new_st, req_id)
    )
    flash(f"Request {new_st.lower()}.", "success")
    return redirect(url_for("requests_page"))


# ═══════════════════════════════════════════════════════════════════════════════
#  SESSIONS
# ═══════════════════════════════════════════════════════════════════════════════
@app.route("/sessions")
@login_required
def sessions_page():
    sid = session["student_id"]

    all_sessions = DB.query_all("""
        SELECT se.*, lr.skill_id,
               learner.full_name  AS learner_name,
               provider.full_name AS provider_name,
               sk.skill_name,
               (SELECT COUNT(*) FROM feedback f WHERE f.session_id=se.id) AS has_feedback
        FROM sessions se
        JOIN learning_requests lr ON se.request_id = lr.id
        JOIN students learner  ON se.learner_id  = learner.id
        JOIN students provider ON se.provider_id = provider.id
        JOIN skills sk ON lr.skill_id = sk.id
        WHERE se.learner_id=%s OR se.provider_id=%s
        ORDER BY se.session_date DESC, se.start_time DESC
    """, (sid, sid))

    today = date.today().isoformat()
    return render_template("sessions.html", all_sessions=all_sessions,
                           today=today, student_id=sid)


@app.route("/sessions/schedule", methods=["POST"])
@login_required
def schedule_session():
    sid        = session["student_id"]
    req_id     = request.form.get("request_id", type=int)
    sess_date  = request.form.get("session_date","").strip()
    start_time = request.form.get("start_time","").strip()
    duration   = request.form.get("duration_minutes", 60, type=int)
    meeting    = request.form.get("meeting_details","").strip()

    req = DB.query_one("SELECT * FROM learning_requests WHERE id=%s", (req_id,))
    if not req or req["provider_id"] != sid:
        abort(403)
    if req["status"] != "Accepted":
        flash("Only accepted requests can be scheduled.", "warning")
        return redirect(url_for("requests_page"))

    existing_session = DB.query_one(
        "SELECT id FROM sessions WHERE request_id=%s", (req_id,))
    if existing_session:
        flash("A session already exists for this request.", "warning")
        return redirect(url_for("sessions_page"))

    if not sess_date or not start_time:
        flash("Date and start time are required.", "danger")
        return redirect(url_for("requests_page"))

    try:
        datetime.strptime(sess_date, "%Y-%m-%d")
        datetime.strptime(start_time, "%H:%M")
    except ValueError:
        flash("Invalid date or time format.", "danger")
        return redirect(url_for("requests_page"))

    DB.execute(
        "INSERT INTO sessions (request_id, learner_id, provider_id, session_date, "
        "start_time, duration_minutes, meeting_details) VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (req_id, req["learner_id"], sid, sess_date, start_time, duration, meeting)
    )
    flash("Session scheduled!", "success")
    return redirect(url_for("sessions_page"))


@app.route("/sessions/<int:session_id>/complete", methods=["POST"])
@login_required
def complete_session(session_id):
    sid  = session["student_id"]
    sess = DB.query_one("SELECT * FROM sessions WHERE id=%s", (session_id,))
    if not sess:
        abort(404)
    if sess["provider_id"] != sid and sess["learner_id"] != sid:
        abort(403)
    if sess["status"] != "Scheduled":
        flash("Session is not in Scheduled state.", "warning")
        return redirect(url_for("sessions_page"))

    DB.execute_many([
        ("UPDATE sessions SET status='Completed' WHERE id=%s", (session_id,)),
        ("UPDATE learning_requests SET status='Completed' WHERE id=%s", (sess["request_id"],))
    ])
    flash("Session marked as completed.", "success")
    return redirect(url_for("sessions_page"))


@app.route("/sessions/<int:session_id>/cancel", methods=["POST"])
@login_required
def cancel_session(session_id):
    sid  = session["student_id"]
    sess = DB.query_one("SELECT * FROM sessions WHERE id=%s", (session_id,))
    if not sess:
        abort(404)
    if sess["provider_id"] != sid and sess["learner_id"] != sid:
        abort(403)
    if sess["status"] != "Scheduled":
        flash("Only scheduled sessions can be cancelled.", "warning")
        return redirect(url_for("sessions_page"))

    DB.execute("UPDATE sessions SET status='Cancelled' WHERE id=%s", (session_id,))
    flash("Session cancelled.", "info")
    return redirect(url_for("sessions_page"))


@app.route("/sessions/<int:session_id>/update", methods=["POST"])
@login_required
def update_session(session_id):
    sid  = session["student_id"]
    sess = DB.query_one("SELECT * FROM sessions WHERE id=%s", (session_id,))
    if not sess or sess["provider_id"] != sid:
        abort(403)
    if sess["status"] != "Scheduled":
        flash("Cannot edit a non-scheduled session.", "warning")
        return redirect(url_for("sessions_page"))

    sess_date  = request.form.get("session_date","").strip()
    start_time = request.form.get("start_time","").strip()
    duration   = request.form.get("duration_minutes", 60, type=int)
    meeting    = request.form.get("meeting_details","").strip()

    DB.execute(
        "UPDATE sessions SET session_date=%s, start_time=%s, duration_minutes=%s, "
        "meeting_details=%s WHERE id=%s",
        (sess_date, start_time, duration, meeting, session_id)
    )
    flash("Session details updated.", "success")
    return redirect(url_for("sessions_page"))


# ═══════════════════════════════════════════════════════════════════════════════
#  FEEDBACK
# ═══════════════════════════════════════════════════════════════════════════════
@app.route("/feedback/<int:session_id>", methods=["GET","POST"])
@login_required
def submit_feedback(session_id):
    sid  = session["student_id"]
    sess = DB.query_one("""
        SELECT se.*, sk.skill_name, provider.full_name AS provider_name
        FROM sessions se
        JOIN learning_requests lr ON se.request_id = lr.id
        JOIN skills sk ON lr.skill_id = sk.id
        JOIN students provider ON se.provider_id = provider.id
        WHERE se.id=%s
    """, (session_id,))

    if not sess:
        abort(404)
    if sess["learner_id"] != sid:
        abort(403)
    if sess["status"] != "Completed":
        flash("Feedback can only be submitted for completed sessions.", "warning")
        return redirect(url_for("sessions_page"))

    existing = DB.query_one(
        "SELECT id FROM feedback WHERE session_id=%s", (session_id,))
    if existing:
        flash("You have already submitted feedback for this session.", "warning")
        return redirect(url_for("sessions_page"))

    if request.method == "POST":
        rating  = request.form.get("rating", type=int)
        comment = request.form.get("comment","").strip()

        if not rating or rating < 1 or rating > 5:
            flash("Please select a rating between 1 and 5.", "danger")
            return render_template("feedback.html", sess=sess)

        DB.execute(
            "INSERT INTO feedback (session_id, learner_id, provider_id, rating, comment) "
            "VALUES (%s,%s,%s,%s,%s)",
            (session_id, sid, sess["provider_id"], rating, comment)
        )
        flash("Thank you for your feedback!", "success")
        return redirect(url_for("sessions_page"))

    return render_template("feedback.html", sess=sess)


# ═══════════════════════════════════════════════════════════════════════════════
#  API ENDPOINTS (JSON)
# ═══════════════════════════════════════════════════════════════════════════════
@app.route("/api/skills/<int:skill_id>")
@login_required
def api_skill(skill_id):
    sid   = session["student_id"]
    skill = DB.query_one(
        "SELECT * FROM skills WHERE id=%s AND student_id=%s", (skill_id, sid))
    if not skill:
        return jsonify({"error": "Not found"}), 404
    # convert datetimes for JSON
    skill["created_at"] = str(skill["created_at"])
    skill["updated_at"] = str(skill["updated_at"])
    return jsonify(skill)


@app.route("/api/request_modal_data")
@login_required
def api_request_modal():
    """Return provider info + skill info for the request modal."""
    skill_id    = request.args.get("skill_id",    type=int)
    provider_id = request.args.get("provider_id", type=int)
    skill = DB.query_one("""
        SELECT sk.*, st.full_name, st.department
        FROM skills sk JOIN students st ON sk.student_id=st.id
        WHERE sk.id=%s AND sk.student_id=%s
    """, (skill_id, provider_id))
    if not skill:
        return jsonify({"error": "Not found"}), 404
    return jsonify({
        "skill_name":       skill["skill_name"],
        "provider_name":    skill["full_name"],
        "department":       skill["department"],
        "proficiency_level":skill["proficiency_level"],
    })


# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
