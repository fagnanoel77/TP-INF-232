import streamlit as st
import pandas as pd
import plotly.express as px
from scipy import stats
import numpy as np
import os
import re
import time

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="ScoreCard AI", page_icon="🎓", layout="wide")

# Theme-aware styling with Darker Red and Charcoal Tones
st.markdown("""
    <style>
    .gpa-container {
        margin-top: 10px;
        margin-bottom: 30px;
        padding: 10px;
        line-height: 1.1;
    }
    .gpa-label { 
        font-size: 1rem; 
        font-weight: 500;
        color: #2c3e50; /* Darker charcoal */
        margin: 0;
    }
    .gpa-value { 
        font-size: 5rem; 
        font-weight: 900; 
        color: #B22222; /* Deep Firebrick Red */
        margin: 5px 0;
    }
    .gpa-avg { 
        font-size: 1.4rem; 
        font-weight: 400;
        color: #34495e; /* Medium Dark Tone */
        margin: 0;
    }
    /* Metric boxes fix for Dark/Light mode */
    div[data-testid="stMetric"] {
        padding: 15px;
        border-radius: 10px;
        border: 1px solid rgba(128, 128, 128, 0.2);
        background-color: rgba(128, 128, 128, 0.05);
    }
    /* Ensure text visibility in dark mode */
    [data-theme="dark"] .gpa-label, [data-theme="dark"] .gpa-avg {
        color: #ecf0f1 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. GPA LOGIC (CAMEROON SCALE) ---
def get_grade_points(score):
    """Converts a 0-100 score to Cameroon GPA points (4.0 Scale)."""
    if score >= 80: return 4.0
    elif score >= 75: return 3.7
    elif score >= 70: return 3.3
    elif score >= 65: return 3.0
    elif score >= 60: return 2.7
    elif score >= 55: return 2.3
    elif score >= 50: return 2.0
    elif score >= 45: return 1.7
    elif score >= 40: return 1.3
    elif score >= 35: return 1.0
    else: return 0.0

def calculate_average_gpa(user_scores_dict):
    """Calculates the mean GPA points from a dictionary of scores."""
    valid_scores = [v for v in user_scores_dict.values() if v is not None and not np.isnan(v)]
    if not valid_scores: return 0.0
    points = [get_grade_points(s) for s in valid_scores]
    return sum(points) / len(points)

# --- 3. DATA & FILE MANAGEMENT ---
ORIGINAL_FILE = 'cleaned_results.csv'
SAVED_FILE = 'user_submissions.csv'

def initialize_files():
    if not os.path.exists(SAVED_FILE):
        try:
            df_orig = pd.read_csv(ORIGINAL_FILE)
            empty_df = pd.DataFrame(columns=df_orig.columns)
            empty_df.to_csv(SAVED_FILE, index=False)
        except: pass

@st.cache_data
def load_all_data():
    df_orig = pd.read_csv(ORIGINAL_FILE)
    if os.path.exists(SAVED_FILE):
        df_user = pd.read_csv(SAVED_FILE)
        df_combined = pd.concat([df_orig, df_user], ignore_index=True)
    else:
        df_combined = df_orig
    df_combined = df_combined.dropna(subset=['matricule'])
    
    subject_cols = ['FBLI11', 'INF111', 'INF112', 'INF121', 'INF122', 'INF131', 
                    'INF132', 'INF141', 'INF142', 'INF151', 'INF152', 'MAT112', 
                    'MAT131', 'PHY161', 'PPE111']
    return df_combined, subject_cols

initialize_files()
df, subjects = load_all_data()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("🎓 ScoreCard AI")
    mode = st.radio("Step 1: Choose Entry Mode", ["Matricule Number", "Manual Entry"])
    
    user_scores = {}
    
    if mode == "Matricule Number":
        search_id = st.selectbox("Select your Matricule", df['matricule'].unique())
        student_row = df[df['matricule'] == search_id].iloc[0]
        st.success(f"Viewing: {student_row['name']}")
        for sub in subjects:
            user_scores[sub] = student_row[sub]
        # For existing records, we use the mgp provided or calculate it
        current_gpa = student_row.get('mgp', calculate_average_gpa(user_scores))
            
    else:
        st.subheader("Manual Score Entry")
        selected_manual_subs = st.multiselect("Select 8 to 10 subjects:", subjects)
        for sub in selected_manual_subs:
             user_scores[sub] = st.number_input(f"Score for {sub}", 0.0, 100.0, 50.0)

        current_gpa = calculate_average_gpa(user_scores)
        if user_scores:
            st.metric("Estimated GPA", f"{current_gpa:.2f}")

        st.divider()
        num_selected = len(selected_manual_subs)
        if 8 <= num_selected <= 10:
            reg_name = st.text_input("Full Name")
            reg_mat = st.text_input("Matricule (e.g. 24F1234)").upper().strip() 
            
            if st.button("💾 Save & Record Results"):
                mat_pattern = re.compile(r"^[0-9]{2}[A-Z]{1}[0-9]{4}$")
                if not reg_name or not reg_mat:
                    st.error("Missing name or matricule!")
                elif not mat_pattern.match(reg_mat):
                    st.error("Format Error! Use 00X0000 (e.g. 24F1234).")
                elif reg_mat in df['matricule'].astype(str).values:
                    st.error("Matricule already exists!")
                else:
                    new_row = {col: np.nan for col in df.columns}
                    new_row['name'], new_row['matricule'], new_row['mgp'] = reg_name, reg_mat, current_gpa
                    for sub, score in user_scores.items(): new_row[sub] = score
                    pd.DataFrame([new_row]).to_csv(SAVED_FILE, mode='a', header=False, index=False)
                    
                    msg_slot = st.empty()
                    msg_slot.success(f"✅ Record for {reg_name} saved! Refreshing in 5s...")
                    st.balloons()
                    time.sleep(5)
                    st.cache_data.clear()
                    st.rerun()
        else:
            st.warning("Select 8-10 subjects to enable saving.")

# --- 5. MAIN DASHBOARD ---
st.title("📊 Performance Analysis")

if user_scores and any(v > 0 for v in user_scores.values()):
    # GPA SECTION
    avg_class_gpa = df['mgp'].mean()
    st.markdown(f"""
        <div class="gpa-container">
            <p class="gpa-label">your GPA</p>
            <p class="gpa-value">{current_gpa:.2f}</p>
            <p class="gpa-avg">average gpa: {avg_class_gpa:.2f}</p>
        </div>
    """, unsafe_allow_html=True)

    # SUBJECT DEEP DIVE
    valid_keys = [s for s, v in user_scores.items() if not pd.isna(v)]
    if valid_keys:
        selected_sub = st.selectbox("Deep-Dive Subject:", valid_keys)
        class_data = df[selected_sub].dropna()
        u_score = user_scores.get(selected_sub, 0)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Your Score", f"{u_score:.1f}")
        c2.metric("Class Average", f"{class_data.mean():.1f}")
        c3.metric("Z-Score", f"{(u_score - class_data.mean())/class_data.std():.2f}" if class_data.std() > 0 else "0")

        fig = px.histogram(class_data, x=selected_sub, title=f"Distribution: {selected_sub}", color_discrete_sequence=['#3366CC'])
        fig.add_vline(x=u_score, line_color="#FF4B4B", line_width=4, annotation_text="YOU")
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("👈 Please enter your scores in the sidebar to visualize your performance.")
