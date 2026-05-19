# ================================
# BLUE TECH TESTING - SINGLE FILE VERSION
# ================================



# ===== DATABASE =====

import sqlite3
import hashlib
import os

DB_PATH = "blue_tech.db"

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = get_conn()
    c = conn.cursor()

    # Users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            full_name TEXT,
            class TEXT,
            domain TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Questions table
    c.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class TEXT NOT NULL,
            domain TEXT NOT NULL,
            subject TEXT NOT NULL,
            question TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            correct_answer TEXT NOT NULL,
            added_by TEXT DEFAULT 'admin',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tests table
    c.execute("""
        CREATE TABLE IF NOT EXISTS tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            class TEXT NOT NULL,
            domain TEXT NOT NULL,
            subject TEXT NOT NULL,
            questions TEXT NOT NULL,
            created_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Results table
    c.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            student_name TEXT,
            test_id INTEGER,
            test_title TEXT,
            subject TEXT,
            class TEXT,
            score INTEGER,
            total INTEGER,
            percentage REAL,
            answers TEXT,
            taken_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Default admin account
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, role, full_name) VALUES (?,?,?,?)",
                  ('admin', hash_password('admin123'), 'admin', 'Administrator'))

    conn.commit()
    conn.close()

def get_all_users():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, username, role, full_name, class, domain, created_at FROM users WHERE role != 'admin'")
    rows = c.fetchall()
    conn.close()
    return rows

def add_user(username, password, role, full_name, cls=None, domain=None):
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, role, full_name, class, domain) VALUES (?,?,?,?,?,?)",
                  (username, hash_password(password), role, full_name, cls, domain))
        conn.commit()
        conn.close()
        return True, "User added successfully!"
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Username already exists!"

def delete_user(user_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

def verify_login(username, password):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, username, role, full_name, class, domain FROM users WHERE username=? AND password=?",
              (username, hash_password(password)))
    user = c.fetchone()
    conn.close()
    return user

def add_question(cls, domain, subject, question, a, b, c_opt, d, correct, added_by='admin'):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""INSERT INTO questions (class, domain, subject, question, option_a, option_b, option_c, option_d, correct_answer, added_by)
                 VALUES (?,?,?,?,?,?,?,?,?,?)""",
              (cls, domain, subject, question, a, b, c_opt, d, correct, added_by))
    conn.commit()
    conn.close()

def get_questions(cls, domain, subject, limit=None):
    conn = get_conn()
    c = conn.cursor()
    if limit:
        c.execute("SELECT * FROM questions WHERE class=? AND domain=? AND subject=? ORDER BY RANDOM() LIMIT ?",
                  (cls, domain, subject, limit))
    else:
        c.execute("SELECT * FROM questions WHERE class=? AND domain=? AND subject=?",
                  (cls, domain, subject))
    rows = c.fetchall()
    conn.close()
    return rows

def delete_question(q_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM questions WHERE id=?", (q_id,))
    conn.commit()
    conn.close()

def save_test(title, cls, domain, subject, questions_json, created_by):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO tests (title, class, domain, subject, questions, created_by) VALUES (?,?,?,?,?,?)",
              (title, cls, domain, subject, questions_json, created_by))
    conn.commit()
    test_id = c.lastrowid
    conn.close()
    return test_id

def get_tests(cls=None, domain=None):
    conn = get_conn()
    c = conn.cursor()
    if cls and domain:
        c.execute("SELECT * FROM tests WHERE class=? AND domain=? ORDER BY created_at DESC", (cls, domain))
    else:
        c.execute("SELECT * FROM tests ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def save_result(student_id, student_name, test_id, test_title, subject, cls, score, total, answers_json):
    percentage = round((score / total) * 100, 1) if total > 0 else 0
    conn = get_conn()
    c = conn.cursor()
    c.execute("""INSERT INTO results (student_id, student_name, test_id, test_title, subject, class, score, total, percentage, answers)
                 VALUES (?,?,?,?,?,?,?,?,?,?)""",
              (student_id, student_name, test_id, test_title, subject, cls, score, total, percentage, answers_json))
    conn.commit()
    conn.close()

def get_student_results(student_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM results WHERE student_id=? ORDER BY taken_at DESC", (student_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_all_results():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM results ORDER BY taken_at DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def get_question_count(cls, domain, subject):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM questions WHERE class=? AND domain=? AND subject=?", (cls, domain, subject))
    count = c.fetchone()[0]
    conn.close()
    return count


# ===== AUTH =====

import streamlit as st

def check_login():
    return st.session_state.get("logged_in", False)

def logout():
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = None
    st.session_state.user_id = None
    st.session_state.full_name = None
    st.rerun()


# ===== SUBJECTS =====

# Subject configuration for Blue Tech Testing System

SUBJECTS = {
    "9": {
        "Medical": ["Biology", "Chemistry", "Physics", "Mathematics", "English", "Urdu", "Islamiat", "Tarjuma tul Quran"],
        "Non-Medical": ["Computer Science", "Chemistry", "Physics", "Mathematics", "English", "Urdu", "Islamiat", "Tarjuma tul Quran"]
    },
    "10": {
        "Medical": ["Biology", "Chemistry", "Physics", "Mathematics", "English", "Urdu", "Pak Studies", "Tarjuma tul Quran"],
        "Non-Medical": ["Computer Science", "Chemistry", "Physics", "Mathematics", "English", "Urdu", "Pak Studies", "Tarjuma tul Quran"]
    }
}

CLASSES = ["9", "10"]
DOMAINS = ["Medical", "Non-Medical"]


# ===== AI_GENERATOR =====

import requests
import json
import streamlit as st

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def get_groq_key():
    # Try from secrets first, then session state
    try:
        return st.secrets["GROQ_API_KEY"]
    except:
        return st.session_state.get("groq_api_key", "")

def generate_questions_ai(cls, domain, subject, num_questions=10):
    api_key = get_groq_key()
    if not api_key:
        return None, "Groq API key not set!"

    prompt = f"""Generate {num_questions} multiple choice questions (MCQs) for:
- Class: {cls}th Grade (Pakistan curriculum)
- Domain: {domain}
- Subject: {subject}

Return ONLY a valid JSON array. No extra text. Format:
[
  {{
    "question": "Question text here?",
    "option_a": "Option A",
    "option_b": "Option B",
    "option_c": "Option C",
    "option_d": "Option D",
    "correct_answer": "A"
  }}
]

Rules:
- Questions must be from Pakistan's 9th/10th grade curriculum
- correct_answer must be only A, B, C, or D
- Make questions educational and appropriate
- Return ONLY the JSON array, nothing else"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system", "content": "You are an expert Pakistani education curriculum MCQ generator. Return only valid JSON arrays."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 3000
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"].strip()
            # Clean up response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            questions = json.loads(content)
            return questions, None
        else:
            return None, f"API Error: {response.status_code} - {response.text}"
    except json.JSONDecodeError as e:
        return None, f"JSON parse error: {str(e)}"
    except Exception as e:
        return None, f"Error: {str(e)}"


# ===== LOGIN =====

import streamlit as st

def show_login():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="background:white; padding:35px; border-radius:16px; 
                    box-shadow:0 4px 24px rgba(0,0,0,0.10); margin-top:20px;">
            <h2 style="text-align:center; color:#1a3a6b; margin-bottom:5px;">🔵 Login</h2>
            <p style="text-align:center; color:#888; margin-bottom:25px;">Blue Tech Testing System</p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("👤 Username", placeholder="Enter username")
            password = st.text_input("🔒 Password", type="password", placeholder="Enter password")
            submitted = st.form_submit_button("🚀 Login", use_container_width=True)

            if submitted:
                if username and password:
                    user = verify_login(username, password)
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.user_id = user[0]
                        st.session_state.username = user[1]
                        st.session_state.role = user[2]
                        st.session_state.full_name = user[3]
                        st.session_state.user_class = user[4]
                        st.session_state.user_domain = user[5]
                        st.success(f"Welcome, {user[3]}!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password!")
                else:
                    st.warning("⚠️ Please enter username and password!")

        st.markdown("""
        <div style="text-align:center; margin-top:15px; padding:10px; 
                    background:#f0f4ff; border-radius:8px;">
            <small style="color:#666;">
                🔑 Default Admin: <b>admin</b> / <b>admin123</b><br>
                Contact admin for student/teacher accounts
            </small>
        </div>
        """, unsafe_allow_html=True)


# ===== ADMIN =====

import streamlit as st
import pandas as pd
import json

def show_admin():
    # Sidebar
    with st.sidebar:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#1a3a6b,#0d6efd);padding:15px;border-radius:10px;color:white;text-align:center;">
            <h3 style="margin:0;">👤 Admin Panel</h3>
            <p style="margin:5px 0 0;opacity:0.85;">Welcome, {st.session_state.full_name}</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")
        menu = st.radio("📋 Menu", [
            "🏠 Dashboard",
            "👥 Manage Users",
            "❓ Question Bank",
            "🤖 AI Generator",
            "📝 Create Test",
            "📊 Student Performance",
            "⚙️ Settings"
        ])
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            logout()

    if menu == "🏠 Dashboard":
        show_dashboard()
    elif menu == "👥 Manage Users":
        show_users()
    elif menu == "❓ Question Bank":
        show_question_bank()
    elif menu == "🤖 AI Generator":
        show_ai_generator()
    elif menu == "📝 Create Test":
        show_create_test()
    elif menu == "📊 Student Performance":
        show_performance()
    elif menu == "⚙️ Settings":
        show_settings()


def show_dashboard():
    st.markdown("### 🏠 Admin Dashboard")
    users = get_all_users()
    results = get_all_results()
    teachers = [u for u in users if u[2] == 'teacher']
    students = [u for u in users if u[2] == 'student']
    tests = get_tests()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="stat-card"><h2>{len(teachers)}</h2><p>👨‍🏫 Teachers</p></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="stat-card"><h2>{len(students)}</h2><p>👨‍🎓 Students</p></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="stat-card"><h2>{len(tests)}</h2><p>📝 Tests</p></div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="stat-card"><h2>{len(results)}</h2><p>📊 Results</p></div>""", unsafe_allow_html=True)

    if results:
        st.markdown("### 📈 Recent Results")
        df = pd.DataFrame(results, columns=["ID","Student ID","Student","Test ID","Test","Subject","Class","Score","Total","Percentage","Answers","Date"])
        df = df[["Student","Test","Subject","Class","Score","Total","Percentage","Date"]].head(10)
        st.dataframe(df, use_container_width=True)


def show_users():
    st.markdown("### 👥 Manage Users")
    tab1, tab2 = st.tabs(["➕ Add User", "📋 All Users"])

    with tab1:
        with st.form("add_user_form"):
            col1, col2 = st.columns(2)
            with col1:
                full_name = st.text_input("Full Name")
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
            with col2:
                role = st.selectbox("Role", ["teacher", "student"])
                cls = st.selectbox("Class", ["", "9", "10"])
                domain = st.selectbox("Domain", ["", "Medical", "Non-Medical"])

            if st.form_submit_button("➕ Add User", use_container_width=True):
                if full_name and username and password:
                    success, msg = add_user(username, password, role, full_name,
                                           cls if cls else None,
                                           domain if domain else None)
                    if success:
                        st.success(f"✅ {msg}")
                    else:
                        st.error(f"❌ {msg}")
                else:
                    st.warning("Please fill all required fields!")

    with tab2:
        users = get_all_users()
        if users:
            for u in users:
                col1, col2 = st.columns([5, 1])
                with col1:
                    role_icon = "👨‍🏫" if u[2] == "teacher" else "👨‍🎓"
                    st.markdown(f"""
                    <div style="background:#f8f9ff;padding:10px;border-radius:8px;margin:4px 0;border-left:4px solid #0d6efd;">
                        {role_icon} <b>{u[3]}</b> (@{u[1]}) — {u[2].title()} | Class: {u[4] or '-'} | Domain: {u[5] or '-'}
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    if st.button("🗑️", key=f"del_{u[0]}"):
                        delete_user(u[0])
                        st.rerun()
        else:
            st.info("No users yet. Add some above!")


def show_question_bank():
    st.markdown("### ❓ Question Bank")
    tab1, tab2 = st.tabs(["➕ Add Question", "📋 View Questions"])

    with tab1:
        with st.form("add_q_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                cls = st.selectbox("Class", CLASSES)
            with col2:
                domain = st.selectbox("Domain", DOMAINS)
            with col3:
                subject = st.selectbox("Subject", SUBJECTS[cls][domain])

            question = st.text_area("Question")
            col1, col2 = st.columns(2)
            with col1:
                opt_a = st.text_input("Option A")
                opt_b = st.text_input("Option B")
            with col2:
                opt_c = st.text_input("Option C")
                opt_d = st.text_input("Option D")
            correct = st.selectbox("Correct Answer", ["A", "B", "C", "D"])

            if st.form_submit_button("➕ Add Question", use_container_width=True):
                if question and opt_a and opt_b and opt_c and opt_d:
                    add_question(cls, domain, subject, question, opt_a, opt_b, opt_c, opt_d, correct)
                    st.success("✅ Question added!")
                else:
                    st.warning("Fill all fields!")

    with tab2:
        col1, col2, col3 = st.columns(3)
        with col1:
            f_cls = st.selectbox("Filter Class", CLASSES, key="fq_cls")
        with col2:
            f_dom = st.selectbox("Filter Domain", DOMAINS, key="fq_dom")
        with col3:
            f_sub = st.selectbox("Filter Subject", SUBJECTS[f_cls][f_dom], key="fq_sub")

        questions = get_questions(f_cls, f_dom, f_sub)
        st.markdown(f"**Total: {len(questions)} questions**")

        for q in questions:
            with st.expander(f"Q{q[0]}: {q[4][:60]}..."):
                st.write(f"**A)** {q[5]}  **B)** {q[6]}  **C)** {q[7]}  **D)** {q[8]}")
                st.success(f"✅ Correct: {q[9]}")
                if st.button("🗑️ Delete", key=f"dq_{q[0]}"):
                    delete_question(q[0])
                    st.rerun()


def show_ai_generator():
    st.markdown("### 🤖 AI Question Generator")
    st.info("💡 Generate questions automatically using Groq AI and save to Question Bank!")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        cls = st.selectbox("Class", CLASSES, key="ai_cls")
    with col2:
        domain = st.selectbox("Domain", DOMAINS, key="ai_dom")
    with col3:
        subject = st.selectbox("Subject", SUBJECTS[cls][domain], key="ai_sub")
    with col4:
        num = st.number_input("How many?", min_value=5, max_value=30, value=10)

    if st.button("🤖 Generate with AI", use_container_width=True):
        with st.spinner("🤖 AI is generating questions... Please wait!"):
            questions, error = generate_questions_ai(cls, domain, subject, num)
            if error:
                st.error(f"❌ {error}")
                if "API key" in error:
                    st.warning("⚠️ Please set your Groq API key in Settings!")
            else:
                st.session_state.ai_questions = questions
                st.session_state.ai_meta = (cls, domain, subject)
                st.success(f"✅ {len(questions)} questions generated!")

    if "ai_questions" in st.session_state and st.session_state.ai_questions:
        questions = st.session_state.ai_questions
        meta = st.session_state.ai_meta

        st.markdown(f"**Preview — {len(questions)} questions for Class {meta[0]} | {meta[1]} | {meta[2]}:**")
        for i, q in enumerate(questions[:3]):
            with st.expander(f"Preview Q{i+1}: {q.get('question','')[:60]}..."):
                st.write(f"**A)** {q.get('option_a','')}  **B)** {q.get('option_b','')}  **C)** {q.get('option_c','')}  **D)** {q.get('option_d','')}")
                st.success(f"✅ Correct: {q.get('correct_answer','')}")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save All to Question Bank", use_container_width=True):
                saved = 0
                for q in questions:
                    try:
                        add_question(meta[0], meta[1], meta[2],
                                     q['question'], q['option_a'], q['option_b'],
                                     q['option_c'], q['option_d'], q['correct_answer'], 'AI')
                        saved += 1
                    except:
                        pass
                st.success(f"✅ {saved} questions saved to bank!")
                del st.session_state.ai_questions
        with col2:
            if st.button("🗑️ Discard", use_container_width=True):
                del st.session_state.ai_questions
                st.rerun()


def show_create_test():
    st.markdown("### 📝 Create Test")

    with st.form("create_test_form"):
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("Test Title", placeholder="e.g., Biology Chapter 1 Test")
            cls = st.selectbox("Class", CLASSES)
            domain = st.selectbox("Domain", DOMAINS)
        with col2:
            subject = st.selectbox("Subject", SUBJECTS[cls][domain])
            num_q = st.number_input("Number of Questions", min_value=5, max_value=50, value=10)

        if st.form_submit_button("📝 Create Test", use_container_width=True):
            available = get_question_count(cls, domain, subject)
            if available < num_q:
                st.error(f"❌ Only {available} questions available for this subject! Please add more or use AI Generator.")
            elif not title:
                st.warning("Please enter a test title!")
            else:
                questions = get_questions(cls, domain, subject, num_q)
                q_list = []
                for q in questions:
                    q_list.append({
                        "id": q[0], "question": q[4],
                        "option_a": q[5], "option_b": q[6],
                        "option_c": q[7], "option_d": q[8],
                        "correct_answer": q[9]
                    })
                test_id = save_test(title, cls, domain, subject, json.dumps(q_list), st.session_state.username)
                st.success(f"✅ Test created! ID: {test_id}")

    # Show existing tests
    st.markdown("### 📋 Existing Tests")
    tests = get_tests()
    if tests:
        for t in tests:
            qs = json.loads(t[5])
            st.markdown(f"""
            <div style="background:#f8f9ff;padding:12px;border-radius:8px;margin:4px 0;border-left:4px solid #0d6efd;">
                📝 <b>{t[1]}</b> — Class {t[2]} | {t[3]} | {t[4]} | <b>{len(qs)} questions</b> | {t[7][:10]}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No tests created yet!")


def show_performance():
    st.markdown("### 📊 Student Performance Analytics")
    results = get_all_results()

    if not results:
        st.info("No results yet! Students need to take tests first.")
        return

    df = pd.DataFrame(results, columns=["ID","Student ID","Student","Test ID","Test","Subject","Class","Score","Total","Percentage","Answers","Date"])

    # Summary stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""<div class="stat-card"><h2>{len(df)}</h2><p>Total Tests Taken</p></div>""", unsafe_allow_html=True)
    with col2:
        avg = round(df['Percentage'].mean(), 1)
        st.markdown(f"""<div class="stat-card"><h2>{avg}%</h2><p>Average Score</p></div>""", unsafe_allow_html=True)
    with col3:
        top = df.loc[df['Percentage'].idxmax(), 'Student']
        st.markdown(f"""<div class="stat-card"><h2 style="font-size:1.2rem">{top}</h2><p>🏆 Top Student</p></div>""", unsafe_allow_html=True)
    with col4:
        passed = len(df[df['Percentage'] >= 50])
        st.markdown(f"""<div class="stat-card"><h2>{passed}</h2><p>✅ Passed (≥50%)</p></div>""", unsafe_allow_html=True)

    st.markdown("---")

    # Per student performance
    st.markdown("### 👨‍🎓 Individual Student Progress")
    students = df['Student'].unique()
    selected_student = st.selectbox("Select Student", ["All Students"] + list(students))

    if selected_student != "All Students":
        student_df = df[df['Student'] == selected_student]
    else:
        student_df = df

    # Progress indicator
    for _, row in student_df.iterrows():
        pct = row['Percentage']
        color = "#28a745" if pct >= 70 else "#ffc107" if pct >= 50 else "#dc3545"
        bar_width = int(pct)
        st.markdown(f"""
        <div style="background:#f8f9ff;padding:12px;border-radius:8px;margin:5px 0;border-left:4px solid {color};">
            <div style="display:flex;justify-content:space-between;margin-bottom:5px;">
                <span><b>{row['Student']}</b> — {row['Test']} ({row['Subject']}) | Class {row['Class']}</span>
                <span style="color:{color};font-weight:700;">{row['Score']}/{row['Total']} ({pct}%)</span>
            </div>
            <div style="background:#e9ecef;border-radius:4px;height:8px;">
                <div style="background:{color};width:{bar_width}%;height:8px;border-radius:4px;"></div>
            </div>
            <small style="color:#888;">{row['Date'][:16]}</small>
        </div>
        """, unsafe_allow_html=True)

    # Subject-wise analysis
    st.markdown("### 📚 Subject-wise Performance")
    subject_avg = df.groupby('Subject')['Percentage'].mean().round(1).reset_index()
    subject_avg.columns = ['Subject', 'Average %']
    st.bar_chart(subject_avg.set_index('Subject'))


def show_settings():
    st.markdown("### ⚙️ Settings")
    st.markdown("#### 🔑 Groq API Key")
    st.info("Enter your Groq API key to enable AI question generation. Get it free from console.groq.com")

    current_key = st.session_state.get("groq_api_key", "")
    new_key = st.text_input("Groq API Key", value=current_key, type="password", placeholder="gsk_...")

    if st.button("💾 Save API Key", use_container_width=True):
        st.session_state.groq_api_key = new_key
        st.success("✅ API Key saved for this session!")

    st.markdown("---")
    st.markdown("#### ℹ️ System Info")
    st.markdown("""
    - **Platform:** Blue Tech Testing System
    - **Classes:** 9th & 10th Grade
    - **Domains:** Medical, Non-Medical
    - **AI Model:** Groq Llama3
    - **Version:** 1.0
    """)


# ===== TEACHER =====

import streamlit as st
import pandas as pd
import json

def show_teacher():
    with st.sidebar:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#1a3a6b,#0d6efd);padding:15px;border-radius:10px;color:white;text-align:center;">
            <h3 style="margin:0;">👨‍🏫 Teacher Panel</h3>
            <p style="margin:5px 0 0;opacity:0.85;">{st.session_state.full_name}</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")
        menu = st.radio("📋 Menu", [
            "🏠 Dashboard",
            "❓ Question Bank",
            "🤖 AI Generator",
            "📝 Create Test",
            "📊 Student Performance"
        ])
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            logout()

    if menu == "🏠 Dashboard":
        st.markdown("### 🏠 Teacher Dashboard")
        tests = get_tests()
        results = get_all_results()
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""<div class="stat-card"><h2>{len(tests)}</h2><p>📝 Total Tests</p></div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class="stat-card"><h2>{len(results)}</h2><p>📊 Results</p></div>""", unsafe_allow_html=True)
        with c3:
            students = get_all_users()
            s_count = len([u for u in students if u[2] == 'student'])
            st.markdown(f"""<div class="stat-card"><h2>{s_count}</h2><p>👨‍🎓 Students</p></div>""", unsafe_allow_html=True)

        if results:
            st.markdown("### 📈 Recent Results")
            df = pd.DataFrame(results, columns=["ID","SID","Student","TID","Test","Subject","Class","Score","Total","Percentage","Answers","Date"])
            st.dataframe(df[["Student","Test","Subject","Class","Score","Total","Percentage","Date"]].head(10), use_container_width=True)

    elif menu == "❓ Question Bank":
        st.markdown("### ❓ Question Bank")
        tab1, tab2 = st.tabs(["➕ Add Question", "📋 View"])
        with tab1:
            with st.form("t_add_q"):
                col1, col2, col3 = st.columns(3)
                with col1: cls = st.selectbox("Class", CLASSES)
                with col2: domain = st.selectbox("Domain", DOMAINS)
                with col3: subject = st.selectbox("Subject", SUBJECTS[cls][domain])
                question = st.text_area("Question")
                c1, c2 = st.columns(2)
                with c1:
                    a = st.text_input("Option A")
                    b = st.text_input("Option B")
                with c2:
                    c = st.text_input("Option C")
                    d = st.text_input("Option D")
                correct = st.selectbox("Correct", ["A","B","C","D"])
                if st.form_submit_button("➕ Add", use_container_width=True):
                    if question and a and b and c and d:
                        add_question(cls, domain, subject, question, a, b, c, d, correct, st.session_state.username)
                        st.success("✅ Added!")
                    else:
                        st.warning("Fill all fields!")
        with tab2:
            c1, c2, c3 = st.columns(3)
            with c1: fc = st.selectbox("Class", CLASSES, key="tv_cls")
            with c2: fd = st.selectbox("Domain", DOMAINS, key="tv_dom")
            with c3: fs = st.selectbox("Subject", SUBJECTS[fc][fd], key="tv_sub")
            qs = get_questions(fc, fd, fs)
            st.markdown(f"**{len(qs)} questions**")
            for q in qs:
                with st.expander(f"{q[4][:60]}..."):
                    st.write(f"**A)** {q[5]} | **B)** {q[6]} | **C)** {q[7]} | **D)** {q[8]}")
                    st.success(f"✅ Correct: {q[9]}")

    elif menu == "🤖 AI Generator":
        st.markdown("### 🤖 AI Question Generator")
        c1, c2, c3, c4 = st.columns(4)
        with c1: cls = st.selectbox("Class", CLASSES, key="tai_cls")
        with c2: domain = st.selectbox("Domain", DOMAINS, key="tai_dom")
        with c3: subject = st.selectbox("Subject", SUBJECTS[cls][domain], key="tai_sub")
        with c4: num = st.number_input("Count", 5, 30, 10)
        if st.button("🤖 Generate", use_container_width=True):
            with st.spinner("Generating..."):
                qs, err = generate_questions_ai(cls, domain, subject, num)
                if err:
                    st.error(f"❌ {err}")
                else:
                    st.session_state.t_ai_qs = qs
                    st.session_state.t_ai_meta = (cls, domain, subject)
                    st.success(f"✅ {len(qs)} generated!")
        if "t_ai_qs" in st.session_state:
            qs = st.session_state.t_ai_qs
            meta = st.session_state.t_ai_meta
            for i, q in enumerate(qs[:3]):
                with st.expander(f"Q{i+1}: {q['question'][:50]}..."):
                    st.write(f"A) {q['option_a']} | B) {q['option_b']} | C) {q['option_c']} | D) {q['option_d']}")
                    st.success(f"Correct: {q['correct_answer']}")
            if st.button("💾 Save All to Bank", use_container_width=True):
                for q in qs:
                    add_question(meta[0], meta[1], meta[2], q['question'], q['option_a'], q['option_b'], q['option_c'], q['option_d'], q['correct_answer'], 'AI')
                st.success("✅ Saved!")
                del st.session_state.t_ai_qs

    elif menu == "📝 Create Test":
        st.markdown("### 📝 Create Test")
        with st.form("t_create_test"):
            c1, c2 = st.columns(2)
            with c1:
                title = st.text_input("Test Title")
                cls = st.selectbox("Class", CLASSES)
                domain = st.selectbox("Domain", DOMAINS)
            with c2:
                subject = st.selectbox("Subject", SUBJECTS[cls][domain])
                num_q = st.number_input("Questions", 5, 50, 10)
            if st.form_submit_button("📝 Create", use_container_width=True):
                available = get_question_count(cls, domain, subject)
                if available < num_q:
                    st.error(f"❌ Only {available} questions available!")
                else:
                    questions = get_questions(cls, domain, subject, num_q)
                    q_list = [{"id":q[0],"question":q[4],"option_a":q[5],"option_b":q[6],"option_c":q[7],"option_d":q[8],"correct_answer":q[9]} for q in questions]
                    tid = save_test(title, cls, domain, subject, json.dumps(q_list), st.session_state.username)
                    st.success(f"✅ Test created! ID: {tid}")
        st.markdown("### 📋 My Tests")
        for t in get_tests():
            qs = json.loads(t[5])
            st.markdown(f"""<div style="background:#f8f9ff;padding:10px;border-radius:8px;margin:4px 0;border-left:4px solid #0d6efd;">📝 <b>{t[1]}</b> — Class {t[2]} | {t[3]} | {t[4]} | {len(qs)} Qs</div>""", unsafe_allow_html=True)

    elif menu == "📊 Student Performance":
        st.markdown("### 📊 Student Performance")
        results = get_all_results()
        if not results:
            st.info("No results yet!")
            return
        df = pd.DataFrame(results, columns=["ID","SID","Student","TID","Test","Subject","Class","Score","Total","Percentage","Answers","Date"])
        students = df['Student'].unique()
        sel = st.selectbox("Select Student", ["All"] + list(students))
        if sel != "All":
            df = df[df['Student'] == sel]
        for _, row in df.iterrows():
            pct = row['Percentage']
            color = "#28a745" if pct >= 70 else "#ffc107" if pct >= 50 else "#dc3545"
            st.markdown(f"""
            <div style="background:#f8f9ff;padding:12px;border-radius:8px;margin:5px 0;border-left:4px solid {color};">
                <b>{row['Student']}</b> — {row['Test']} | {row['Subject']} | Class {row['Class']}
                <span style="float:right;color:{color};font-weight:700;">{row['Score']}/{row['Total']} ({pct}%)</span>
                <div style="background:#e9ecef;border-radius:4px;height:8px;margin-top:6px;">
                    <div style="background:{color};width:{int(pct)}%;height:8px;border-radius:4px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)


# ===== STUDENT =====

import streamlit as st
import pandas as pd
import json

def show_student():
    with st.sidebar:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#1a3a6b,#0d6efd);padding:15px;border-radius:10px;color:white;text-align:center;">
            <h3 style="margin:0;">👨‍🎓 Student Panel</h3>
            <p style="margin:5px 0 0;opacity:0.85;">{st.session_state.full_name}</p>
            <small style="opacity:0.75;">Class {st.session_state.user_class or '-'} | {st.session_state.user_domain or '-'}</small>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")
        menu = st.radio("📋 Menu", [
            "🏠 Dashboard",
            "📝 Take Test",
            "📊 My Results",
            "📈 My Progress"
        ])
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            logout()

    if menu == "🏠 Dashboard":
        show_student_home()
    elif menu == "📝 Take Test":
        show_take_test()
    elif menu == "📊 My Results":
        show_my_results()
    elif menu == "📈 My Progress":
        show_my_progress()


def show_student_home():
    st.markdown(f"### 🏠 Welcome, {st.session_state.full_name}!")
    cls = st.session_state.user_class
    domain = st.session_state.user_domain

    results = get_student_results(st.session_state.user_id)
    tests = get_tests(cls, domain) if cls and domain else get_tests()

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""<div class="stat-card"><h2>{len(tests)}</h2><p>📝 Available Tests</p></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="stat-card"><h2>{len(results)}</h2><p>✅ Tests Taken</p></div>""", unsafe_allow_html=True)
    with c3:
        if results:
            df = pd.DataFrame(results, columns=["ID","SID","Student","TID","Test","Subject","Class","Score","Total","Percentage","Answers","Date"])
            avg = round(df['Percentage'].mean(), 1)
        else:
            avg = 0
        st.markdown(f"""<div class="stat-card"><h2>{avg}%</h2><p>📊 Avg Score</p></div>""", unsafe_allow_html=True)

    if results:
        st.markdown("### 📋 Recent Tests")
        df = pd.DataFrame(results, columns=["ID","SID","Student","TID","Test","Subject","Class","Score","Total","Percentage","Answers","Date"])
        for _, row in df.head(5).iterrows():
            pct = row['Percentage']
            color = "#28a745" if pct >= 70 else "#ffc107" if pct >= 50 else "#dc3545"
            st.markdown(f"""
            <div style="background:#f8f9ff;padding:10px;border-radius:8px;margin:4px 0;border-left:4px solid {color};">
                📝 <b>{row['Test']}</b> — {row['Subject']}
                <span style="float:right;color:{color};font-weight:700;">{row['Score']}/{row['Total']} ({pct}%)</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("👆 Go to 'Take Test' to start your first test!")


def show_take_test():
    st.markdown("### 📝 Take Test")

    cls = st.session_state.user_class
    domain = st.session_state.user_domain

    if "active_test" not in st.session_state:
        # Show available tests
        tests = get_tests(cls, domain) if cls and domain else get_tests()

        if not tests:
            st.info("No tests available yet. Please ask your teacher!")
            return

        st.markdown("#### 📋 Available Tests:")
        for t in tests:
            qs = json.loads(t[5])
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"""
                <div style="background:#f8f9ff;padding:12px;border-radius:8px;border-left:4px solid #0d6efd;">
                    📝 <b>{t[1]}</b><br>
                    <small>Class {t[2]} | {t[3]} | {t[4]} | {len(qs)} Questions</small>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("▶️ Start", key=f"start_{t[0]}"):
                    st.session_state.active_test = {
                        "id": t[0],
                        "title": t[1],
                        "class": t[2],
                        "subject": t[4],
                        "questions": json.loads(t[5]),
                        "answers": {},
                        "submitted": False
                    }
                    st.rerun()
    else:
        test = st.session_state.active_test

        if test.get("submitted"):
            show_result_screen(test)
            return

        st.markdown(f"#### 📝 {test['title']} — {test['subject']}")
        st.progress(len(test['answers']) / len(test['questions']))
        st.markdown(f"**Answered: {len(test['answers'])}/{len(test['questions'])}**")
        st.markdown("---")

        questions = test['questions']
        for i, q in enumerate(questions):
            st.markdown(f"**Q{i+1}. {q['question']}**")
            options = {
                "A": q['option_a'],
                "B": q['option_b'],
                "C": q['option_c'],
                "D": q['option_d']
            }
            choices = [f"{k}) {v}" for k, v in options.items()]
            current = test['answers'].get(str(i))
            default_idx = 0
            if current:
                for idx, ch in enumerate(choices):
                    if ch.startswith(current):
                        default_idx = idx
                        break

            selected = st.radio(f"q_{i}", choices, index=default_idx, key=f"q_{i}_{test['id']}", label_visibility="collapsed")
            if selected:
                test['answers'][str(i)] = selected[0]  # Get A/B/C/D
            st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Submit Test", use_container_width=True, type="primary"):
                if len(test['answers']) < len(questions):
                    st.warning(f"⚠️ Please answer all questions! ({len(test['answers'])}/{len(questions)} answered)")
                else:
                    # Calculate score
                    score = 0
                    for i, q in enumerate(questions):
                        if test['answers'].get(str(i)) == q['correct_answer']:
                            score += 1
                    test['score'] = score
                    test['total'] = len(questions)
                    test['submitted'] = True

                    # Save result
                    save_result(
                        st.session_state.user_id,
                        st.session_state.full_name,
                        test['id'],
                        test['title'],
                        test['subject'],
                        test['class'],
                        score,
                        len(questions),
                        json.dumps(test['answers'])
                    )
                    st.rerun()
        with col2:
            if st.button("❌ Cancel", use_container_width=True):
                del st.session_state.active_test
                st.rerun()


def show_result_screen(test):
    score = test['score']
    total = test['total']
    pct = round((score / total) * 100, 1)
    color = "#28a745" if pct >= 70 else "#ffc107" if pct >= 50 else "#dc3545"
    grade = "A+" if pct >= 90 else "A" if pct >= 80 else "B" if pct >= 70 else "C" if pct >= 60 else "D" if pct >= 50 else "F"
    msg = "Excellent! 🎉" if pct >= 70 else "Good effort! 👍" if pct >= 50 else "Keep practicing! 📚"

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,{color}22,{color}11);border:2px solid {color};
                padding:30px;border-radius:16px;text-align:center;margin:20px 0;">
        <h1 style="color:{color};font-size:3rem;margin:0;">{score}/{total}</h1>
        <h2 style="color:{color};">{pct}% — Grade {grade}</h2>
        <p style="font-size:1.2rem;color:#333;">{msg}</p>
        <p style="color:#666;">Test: {test['title']} | Subject: {test['subject']}</p>
    </div>
    """, unsafe_allow_html=True)

    # Show answers review
    with st.expander("📋 Review Answers"):
        for i, q in enumerate(test['questions']):
            student_ans = test['answers'].get(str(i), '-')
            correct = q['correct_answer']
            is_correct = student_ans == correct
            icon = "✅" if is_correct else "❌"
            bg = "#d4edda" if is_correct else "#f8d7da"
            st.markdown(f"""
            <div style="background:{bg};padding:10px;border-radius:8px;margin:5px 0;">
                {icon} <b>Q{i+1}:</b> {q['question']}<br>
                <small>Your answer: <b>{student_ans}</b> | Correct: <b>{correct}</b></small>
            </div>
            """, unsafe_allow_html=True)

    if st.button("🏠 Back to Tests", use_container_width=True):
        del st.session_state.active_test
        st.rerun()


def show_my_results():
    st.markdown("### 📊 My Results")
    results = get_student_results(st.session_state.user_id)
    if not results:
        st.info("No results yet! Take a test first.")
        return

    for r in results:
        pct = r[9]
        color = "#28a745" if pct >= 70 else "#ffc107" if pct >= 50 else "#dc3545"
        grade = "A+" if pct >= 90 else "A" if pct >= 80 else "B" if pct >= 70 else "C" if pct >= 60 else "D" if pct >= 50 else "F"
        st.markdown(f"""
        <div style="background:#f8f9ff;padding:14px;border-radius:10px;margin:6px 0;border-left:5px solid {color};">
            <div style="display:flex;justify-content:space-between;">
                <span><b>{r[4]}</b> — {r[5]} | Class {r[6]}</span>
                <span style="color:{color};font-weight:700;">{r[7]}/{r[8]} ({pct}%) — Grade {grade}</span>
            </div>
            <div style="background:#e9ecef;border-radius:4px;height:8px;margin-top:8px;">
                <div style="background:{color};width:{int(pct)}%;height:8px;border-radius:4px;"></div>
            </div>
            <small style="color:#888;">{r[11][:16]}</small>
        </div>
        """, unsafe_allow_html=True)


def show_my_progress():
    st.markdown("### 📈 My Progress")
    results = get_student_results(st.session_state.user_id)
    if not results:
        st.info("No results yet! Take some tests first.")
        return

    df = pd.DataFrame(results, columns=["ID","SID","Student","TID","Test","Subject","Class","Score","Total","Percentage","Answers","Date"])

    # Overall stats
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""<div class="stat-card"><h2>{len(df)}</h2><p>Tests Taken</p></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="stat-card"><h2>{round(df['Percentage'].mean(),1)}%</h2><p>Average Score</p></div>""", unsafe_allow_html=True)
    with c3:
        best = round(df['Percentage'].max(), 1)
        st.markdown(f"""<div class="stat-card"><h2>{best}%</h2><p>🏆 Best Score</p></div>""", unsafe_allow_html=True)

    # Subject-wise chart
    st.markdown("### 📚 Performance by Subject")
    sub_avg = df.groupby('Subject')['Percentage'].mean().round(1)
    st.bar_chart(sub_avg)

    # Progress over time
    st.markdown("### 📅 Progress Over Time")
    df['Date'] = pd.to_datetime(df['Date'])
    df_sorted = df.sort_values('Date')
    st.line_chart(df_sorted.set_index('Date')['Percentage'])


# ===== MAIN APP =====

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
st.set_page_config(
    page_title="Blue Tech Testing System",
    page_icon="🔵",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Initialize database
init_db()

# Custom CSS
st.markdown("""
<style>
    /* Main theme */
    .main-header {
        background: linear-gradient(135deg, #1a3a6b, #0d6efd);
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        color: white;
        margin-bottom: 20px;
    }
    .main-header h1 { font-size: 2.2rem; margin: 0; font-weight: 700; }
    .main-header p { font-size: 1rem; margin: 5px 0 0; opacity: 0.85; }

    .login-box {
        background: white;
        padding: 35px;
        border-radius: 16px;
        box-shadow: 0 4px 24px rgba(0,0,0,0.10);
        max-width: 420px;
        margin: 30px auto;
    }
    .role-card {
        background: linear-gradient(135deg, #0d6efd, #1a3a6b);
        color: white;
        padding: 18px;
        border-radius: 12px;
        text-align: center;
        margin: 8px 0;
        cursor: pointer;
    }
    .stat-card {
        background: linear-gradient(135deg, #0d6efd22, #1a3a6b11);
        border: 1px solid #0d6efd44;
        padding: 18px;
        border-radius: 12px;
        text-align: center;
    }
    .stat-card h2 { color: #0d6efd; font-size: 2rem; margin: 0; }
    .stat-card p { color: #333; margin: 4px 0 0; font-size: 0.95rem; }

    div[data-testid="stButton"] button {
        background: linear-gradient(135deg, #0d6efd, #1a3a6b);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 600;
        width: 100%;
    }
    div[data-testid="stButton"] button:hover {
        background: linear-gradient(135deg, #1a3a6b, #0d6efd);
    }
    .footer {
        text-align: center;
        color: #888;
        font-size: 0.8rem;
        margin-top: 40px;
        padding: 10px;
        border-top: 1px solid #eee;
    }
    .stSelectbox label, .stTextInput label, .stRadio label {
        font-weight: 600;
        color: #1a3a6b;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>🔵 Blue Tech Testing System</h1>
    <p>Pakistan's Smart Exam Paper Generator — Class 9 & 10</p>
</div>
""", unsafe_allow_html=True)

# Check login state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = None
    st.session_state.user_id = None

if not st.session_state.logged_in:
    # Show login page
        show_login()
else:
    role = st.session_state.role
    if role == "admin":
                show_admin()
    elif role == "teacher":
                show_teacher()
    elif role == "student":
                show_student()

# Footer
st.markdown("""
<div class="footer">
    🔵 Blue Tech Testing System | Class 9 & 10 | Powered by AI
</div>
""", unsafe_allow_html=True)

