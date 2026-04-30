import streamlit as st
import pandas as pd
import plotly.express as px
from scipy import stats
import numpy as np
import os
import re
import time

# --- 1. CONFIG & THEME-AWARE STYLING ---
st.set_page_config(page_title="ScoreCard AI", page_icon="🎓", layout="wide")

# Custom CSS for the specific GPA layout and theme compatibility
st.markdown("""
    <style>
    /* GPA Layout Fix */
    .gpa-container {
        margin-top: -20px;
        margin-bottom: 30px;
        display: flex;
        flex-direction: column;
        align-items: flex-start;
    }
    .gpa-label { 
        font-size: 1rem; 
        font-weight: 400;
        margin-bottom: -10px; 
        text-transform: lowercase;
        opacity: 0.8;
    }
    .gpa-value { 
        font-size: 5rem; 
        font-weight: 900; 
        color: #1E1E1E; /* Deep Dark Tone */
        line-height: 1;
        margin: 5px 0;
    }
    .gpa-avg { 
        font-size: 1.5rem; 
        font-weight: 500;
        text-transform: lowercase;
        opacity: 0.7;
    }
    
    /* Support for Streamlit Dark Theme */
    @media (prefers-color-scheme: dark) {
        .gpa-value { color: #E0E0E0; }
    }

    /* Metric Box Fix for Dark Mode */
    div[data-testid="stMetric"] {
        padding: 20px;
        border-radius: 12px;
        border: 1px solid rgba(128, 128, 128, 0.3);
        background-color: rgba(128, 128, 128, 0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. GPA CALCULATION LOGIC (CAMEROON SCALE) ---
def calculate_cameroon_gpa(scores_list):
    """Calculates GPA based on the 4.0 scale common in Cameroon."""
    if not scores_list:
        return 0.0
    
    grade_points = []
    for score in scores_list:
        if score >= 80: gp = 4.0
        elif score >= 75: gp = 3.7
        elif score >= 70: gp = 3.3
        elif score >= 65: gp = 3.0
        elif score >= 60: gp = 2.7
        elif score >= 55: gp = 2.3
        elif score >= 50: gp = 2.0
        elif score >= 45: gp = 1.7
        elif score >= 40: gp = 1.3
        else: gp = 1.0
        grade_points.append(gp)
    
    return sum(grade_points) / len(grade_points)

# --- 3. DATA MANAGEMENT ---
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
    mode = st.radio("Entry Mode", ["Matricule Number", "Manual Entry"])
    
    user_scores = {}
    current_gpa = 0.0
    
    if mode == "Matricule Number":
        search_id = st.selectbox("Select Matricule", df['matricule'].unique())
        student_row = df[df['matricule'] == search_id].iloc[0]
        st.success(f"Viewing: {student_row['name']}")
        # Pull original GPA or recalculate
        current_gpa = student_row.get('mgp', 0.0)
        for sub in subjects:
            user_scores[sub] = student_row[sub]
            
    else:
        st.subheader("Manual Entry")
        selected_manual_subs = st.multiselect("Select 8-10 subjects:", subjects)
        
        for sub in selected_manual_subs:
             user_scores[sub] = st.number_input(f"Score for {sub}", 0.0, 100.0, 50.0)

        # Real-time GPA update in Sidebar
        if user_scores:
            scores_only = [v for v in user_scores.values()]
            current_gpa = calculate_cameroon_gpa(scores_only)
            st.metric("Estimated GPA", f"{current_gpa:.2f}")

        st.divider()
        
        # --- SAVE ACTION ---
        num_selected = len(selected_manual_subs)
        if 8 <= num_selected <= 10:
            reg_name = st.text_input("Full Name")
            reg_mat = st.text_input("Matricule (00X0000)").upper().strip() 
            
            if st.button("💾 Record Results"):
                mat_pattern = re.compile(r"^[0-9]{2}[A-Z]{1}[0-9]{4}$")
                
                if not reg_name or not reg_mat:
                    st.error("Fields required!")
                elif not mat_pattern.match(reg_mat):
                    st.error("Invalid Format! Example: 24F1234")
                elif reg_mat in df['matricule'].astype(str).values:
                    st.error("Matricule already taken!")
                else:
                    new_row = {col: np.nan for col in df.columns}
                    new_row['name'], new_row['matricule'], new_row['mgp'] = reg_name, reg_mat, current_gpa
                    for sub, score in user_scores.items(): new_row[sub] = score
                    
                    pd.DataFrame([new_row]).to_csv(SAVED_FILE, mode='a', header=False, index=False)
                    
                    msg_slot = st.empty()
                    msg_slot.success(f"✅ Record for {reg_name} saved! Refreshing...")
                    st.balloons()
                    time.sleep(5)
                    st.cache_data.clear()
                    st.rerun()
        else:
            st.warning("Select 8-10 subjects to save.")

# --- 5. MAIN DASHBOARD ---
st.title("📊 Personal Performance Analysis")

if user_scores:
    # --- GPA SECTION (Visual Fix) ---
    avg_gpa = df['mgp'].mean()
    st.markdown(f"""
        <div class="gpa-container">
            <span class="gpa-label">your GPA</span>
            <span class="gpa-value">{current_gpa:.2f}</span>
            <span class="gpa-avg">average gpa: {avg_gpa:.2f}</span>
        </div>
    """, unsafe_allow_html=True)

    # --- SUBJECT ANALYSIS ---
    valid_keys = [s for s, v in user_scores.items() if not pd.isna(v)]
    if valid_keys:
        selected_sub = st.selectbox("Detailed Analysis:", valid_keys)
        class_data = df[selected_sub].dropna()
        u_score = user_scores.get(selected_sub, 0)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Your Score", f"{u_score:.1f}")
        c2.metric("Class Average", f"{class_data.mean():.1f}")
        c3.metric("Percentile", f"{stats.percentileofscore(class_data, u_score):.1f}%")

        fig = px.histogram(class_data, x=selected_sub, title=f"Distribution: {selected_sub}", color_discrete_sequence=['#3366CC'])
        fig.add_vline(x=u_score, line_color="#FF4B4B", line_width=4, annotation_text="YOU")
        st.plotly_chart(fig, use_container_width=True)

    # --- COMPARISON ---
    st.divider()
    if len(valid_keys) > 1:
        st.subheader("⚔️ Subject Comparison")
        comp_list = []
        for s in valid_keys:
            comp_list.append({"Subject": s, "Score": user_scores[s], "Type": "You"})
            comp_list.append({"Subject": s, "Score": df[s].mean(), "Type": "Class"})
        
        fig_bar = px.bar(pd.DataFrame(comp_list), x="Subject", y="Score", color="Type", barmode="group")
        st.plotly_chart(fig_bar, use_container_width=True)
else:
    st.info("👈 Enter your scores in the sidebar to view your analytics.")
