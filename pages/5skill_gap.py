import streamlit as st
from menu import menu_with_redirect

# Page configuration
st.set_page_config(page_title="FinPRO-JOB - Dashboard", layout="wide")

# Load menu
menu_with_redirect()

## Loading CSS
def load_css():
    with open("styles.css", "r") as f:
        css = f.read()
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
load_css()

## ---------- FRONTEND STARTS HERE
st.markdown("""
<div class="career-header">
  <div class="emoji-bg">🛤️</div>
  <h1>Skill Gap</h1>
  <p class="sub">Gap skill + link sertifikasi spesifik</p>
  <div class="badge-row">
    <span>Gap analysis (FR-5.02)</span>
    <span>Link belajar (FR-5.04)</span>
  </div>
</div>
""", unsafe_allow_html=True)

## Peta Jalur Karir (FR-5.01)
st.write("PETA JALUR KARIR (FR-5.01)")

# Ganti waktu udh ada n8n
career_data = {
    "current": {
        "title": "KAMU",
        "jobs": ["Data Analyst", "Data Engineer", "Analyst Intern"],
        "count": 12,
        "gap": ["sql", "python"]
    },
    "mid": {
        "title": "MID LEVEL",
        "jobs": ["Analyst Officer", "CRM Specialist"],
        "count": 19,
        "gap": ["tableau", "statistics"]
    },
    "senior": {
        "title": "SENIOR",
        "jobs": ["Senior Scientist", "Lead Analyst"],
        "count": 16,
        "gap": ["analytics"]
    }
}

cols = st.columns(3)

for i, key in enumerate(career_data):
    item = career_data[key]
    
    jobs_html = ""
    for job in item["jobs"]:
        jobs_html += f"""
        <div class="skill-jobs">{job}</div>"""

    gap_html = ""
    for skill in item["gap"]:
        gap_html += f"""
        <span class="skill-pill">{skill.upper()}</span>"""
    
    with cols[i]:
        st.markdown(f"""
        <div class="skill-card">
            <div class="skill-badge">{item["title"]}</div>
            <div class="skill-count">{item["count"]} Lowongan</div>
            <div>{jobs_html}</div>
            <div class="skill-gap-title">GAP (FR-5.02)</div>
            <div>{gap_html} </div>
        </div>""", unsafe_allow_html=True)

## 📚 LINK BELAJAR & SERTIFIKASI (FR-5.04)
# Nanti dihapus
LearnEntry = tuple[str, str, str, bool]
LEARNING_LINKS: dict[str, list[LearnEntry]] = {
    "sql": [
        ("Dicoding — Belajar Dasar SQL",
         "https://www.dicoding.com/academies/191",    "Dicoding 🇮🇩", True),
        ("Coursera — SQL for Data Science",
         "https://www.coursera.org/learn/sql-for-data-science", "Coursera", True),
        ("W3Schools SQL Tutorial",
         "https://www.w3schools.com/sql/",            "W3Schools",    True),
        ("HackerRank SQL Practice",
         "https://www.hackerrank.com/domains/sql",    "HackerRank",   True),
    ],
    "python": [
        ("Dicoding — Memulai Python",
         "https://www.dicoding.com/academies/86",     "Dicoding 🇮🇩", True),
        ("Coursera — Python for Everybody",
         "https://www.coursera.org/specializations/python", "Coursera", True),
        ("Kaggle — Python (interaktif)",
         "https://www.kaggle.com/learn/python",       "Kaggle",       True),
    ],
    "excel": [
        ("Microsoft Learn — Excel",
         "https://support.microsoft.com/en-us/excel", "Microsoft",    True),
        ("Coursera — Excel Skills for Business",
         "https://www.coursera.org/specializations/excel", "Coursera", True),
        ("GCFGlobal — Excel Tutorial",
         "https://edu.gcfglobal.org/en/excel2016/",   "GCFGlobal",    True),
    ],
    "tableau": [
        ("Tableau eLearning (official)",
         "https://www.tableau.com/learn/training/elearning", "Tableau", True),
        ("Kaggle — Data Visualization",
         "https://www.kaggle.com/learn/data-visualization", "Kaggle", True),
    ],
    "power bi": [
        ("Microsoft Learn — Power BI",
         "https://learn.microsoft.com/en-us/power-bi/", "Microsoft",  True),
        ("Coursera — Power BI Data Analyst",
         "https://www.coursera.org/professional-certificates/"
         "microsoft-power-bi-data-analyst",           "Coursera",     False),
    ],
    "marketing": [
        ("Google Digital Marketing",
         "https://grow.google/intl/id_id/",           "Google 🇮🇩",   True),
        ("Meta Blueprint",
         "https://www.facebook.com/business/learn",   "Meta",         True),
    ],
    "analytics": [
        ("Google Analytics — Skillshop",
         "https://skillshop.withgoogle.com/",         "Google",       True),
        ("Coursera — Google Data Analytics",
         "https://www.coursera.org/professional-certificates/"
         "google-data-analytics",                     "Coursera",     False),
        ("Kaggle — Pandas",
         "https://www.kaggle.com/learn/pandas",       "Kaggle",       True),
    ],
    "communication": [
        ("Coursera — Business Communication",
         "https://www.coursera.org/specializations/business-communication",
         "Coursera", True),
    ],
    "adobe": [
        ("Adobe Learn — Tutorial Resmi",
         "https://helpx.adobe.com/id/learn-and-support.html", "Adobe", True),
    ],
    "design": [
        ("Dicoding — Belajar Dasar UI/UX",
         "https://www.dicoding.com/academies/428",    "Dicoding 🇮🇩", True),
        ("Coursera — Google UX Design",
         "https://www.coursera.org/professional-certificates/google-ux-design",
         "Coursera", False),
        ("Figma Learn",
         "https://help.figma.com/hc/en-us/categories/360002051613", "Figma", True),
    ],
    "statistics": [
        ("Coursera — Statistics with Python",
         "https://www.coursera.org/specializations/statistics-with-python",
         "Coursera", True),
        ("Khan Academy — Statistics",
         "https://www.khanacademy.org/math/statistics-probability",
         "Khan Academy", True),
    ],
}

st.write("LINK BELAJAR & SERTIFIKASI (FR-5.04)")
current_stage = career_data["mid"] ## ini gimana taunya dia harus ambil yang mid?

for skill in current_stage["gap"]:
    skill_key = skill.lower()
    if skill_key not in LEARNING_LINKS:
        continue

    links = LEARNING_LINKS[skill_key]
    links_html = ""

    for title, url, provider, free in links:
        badge = "🆓" if free else "💰"
        links_html += f"""<a href="{url}" target="_blank" class="learn-pill">{badge} {provider}</a>"""

    st.markdown(f"""
    <div class="learning-card">
        <div class="learning-header">
            <h4>{skill.upper()}</h4>
            <div class="priority-pill">Skill Gap</div>
        </div>
        <div class="learning-links">{links_html}</div>
    </div>
    """, unsafe_allow_html=True)