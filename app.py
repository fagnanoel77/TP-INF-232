import streamlit as st
import pandas as pd
import plotly.express as px
from scipy import stats
import numpy as np
import os
import re
import time

# --- 1. CONFIG & RESPONSIVE STYLING ---
st.set_page_config(page_title="ScoreCard AI", page_icon="🎓", layout="wide")

# Custom CSS for Mobile Optimization and Centralized GPA Box
st.markdown("""
    <style>
    /* Centralized GPA Box */
    .gpa-card {
        background-color: rgba(128, 128, 128, 0.05);
        border: 2px solid rgba(128, 128, 128, 0.2);
        border-radius: 20px;
        padding: 30px 10px;
        text-align: center;
        margin: 0 auto 30px auto;
        max-width: 500px; /* Limits width on desktop, full width on mobile */
    }
    
    .gpa-label { 
        font-size: 1rem; 
        font-weight: 500;
        text-transform: lowercase;
        opacity: 0.7;
        display: block;
        margin-bottom: 5px;
    }
    
    .gpa-value { 
        font-size: 5.5rem; 
        font-weight: 900; 
        color: #1A1A1A; /* Deep Dark Tone */
        line-height: 1;
        display: block;
        margin: 10px 0;
    }
    
    .gpa-avg { 
        font-size: 1.2rem; 
        font-weight: 500;
        text-transform: lowercase;
        opacity: 0.6;
        display: block;
    }

    /* Dark Mode Text Colors */
    @media (prefers-color-scheme: dark) {
        .gpa-value { color: #FFFFFF; }
        .gpa-label, .gpa-avg { color: #BBBBBB; }
    }

    /* Mobile-Specific Tweaks (Smaller screens) */
    @media only screen and (max-width: 600px) {
        .gpa-value { font-size: 4rem; }
        .gpa-card { padding: 20px 5px; }
    }

    /* Metric Boxes UI Fix for both themes */
    div[data-testid="stMetric"] {
        padding: 15px;
        border-radius: 12px;
        border: 1px solid rgba(128, 128, 128, 0.2);
        background-color: rgba(128, 128, 128, 0.03);
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. GPA CALCULATION (CAMEROON UNIVERSITY SCALE) ---
def calculate_cameroon_gpa(scores):
    """Maps scores to the 4.0 grading system used in Cameroon."""
    if not scores: return 0.0
    
    pts = []
    for s in scores:
        if s >= 80: pts.append(4.0)
        elif s >= 75: pts.append(3.7)
        elif s >= 70: pts.append(3.3)
        elif s >= 65: pts.append(3.0)
        elif s >= 60: pts.append(2.7)
        elif s >= 55: pts.append(2.3)
        elif s >= 50: pts.append(2.0)
        elif s >= 45: pts.append(1.7)
        elif s >= 40: pts.append(1.3)
        else: pts.append(1.0)
    return sum(pts) / len(pts)

# --- 3. DATA PERSISTENCE ---
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

# --- 4. SIDEBAR LOGIC ---
with st.sidebar:
    st.title("🎓 ScoreCard AI")
    mode = st.radio("Step 1: Choose Entry Mode", ["Matricule Number", "Manual Entry"])
    
    user_scores = {}
    current_gpa = 0.0
    
    if mode == "Matricule Number":
        search_id = st.selectbox("Search/Select Matricule", df['matricule'].unique())
        student_row = df[df['matricule'] == search_id].iloc[0]
        st.success(f"Student: {student_row['name']}")
        current_gpa = student_row.get('mgp', 0.0)
        for sub in subjects:
            user_scores[sub] = student_row[sub]
            
    else:
        st.subheader("Manual Score Entry")
        selected_manual_subs = st.multiselect("Select 8 to 10 subjects:", subjects)
        
        for sub in selected_manual_subs:
             user_scores[sub] = st.number_input(f"Score for {sub}", 0.0, 100.0, 50.0)

        if user_scores:
            current_gpa = calculate_cameroon_gpa(list(user_scores.values()))
            st.metric("Estimated GPA", f"{current_gpa:.2f}")

        st.divider()
        num_selected = len(selected_manual_subs)
        if 8 <= num_selected <= 10:
            reg_name = st.text_input("Full Name")
            reg_mat = st.text_input("Matricule (e.g. 24F1234)").upper().strip() 
            
            if st.button("💾 Save & Record Results"):
                mat_pattern = re.compile(r"^[0-9]{2}[A-Z]{1}[0-9]{4}$")
                if not reg_name or not reg_mat:
                    st.error("Please fill all fields.")
                elif not mat_pattern.match(reg_mat):
                    st.error("Invalid Matricule! Use format 00X0000.")
                elif reg_mat in df['matricule'].astype(str).values:
                    st.error("Matricule already exists in database.")
                else:
                    new_row = {col: np.nan for col in df.columns}
                    new_row['name'], new_row['matricule'], new_row['mgp'] = reg_name, reg_mat, current_gpa
                    for sub, score in user_scores.items(): new_row[sub] = score
                    pd.DataFrame([new_row]).to_csv(SAVED_FILE, mode='a', header=False, index=False)
                    
                    msg_slot = st.empty()
                    msg_slot.success(f"✅ Record saved! Refreshing in 5 seconds...")
                    st.balloons()
                    time.sleep(5)
                    st.cache_data.clear()
                    st.rerun()
        else:
            st.warning("Please select 8-10 subjects.")

# --- 5. MAIN CONTENT ---
st.title("📊 Performance Analysis")

if user_scores:
    # --- GPA CENTRALIZED BOX ---
    avg_gpa = df['mgp'].mean()
    st.markdown(f"""
        <div class="gpa-card">
            <span class="gpa-label">your gpa</span>
            <span class="gpa-value">{current_gpa:.2f}</span>
            <span class="gpa-avg">average class gpa: {avg_gpa:.2f}</span>
        </div>
    """, unsafe_allow_html=True)

    # --- SUBJECT DEEP-DIVE ---
    valid_keys = [s for s, v in user_scores.items() if not pd.isna(v)]
    if valid_keys:
        selected_sub = st.selectbox("Select subject to analyze:", valid_keys)
        class_data = df[selected_sub].dropna()
        u_score = user_scores.get(selected_sub, 0)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Your Score", f"{u_score:.1f}")
        c2.metric("Class Average", f"{class_data.mean():.1f}")
        c3.metric("Percentile", f"{stats.percentileofscore(class_data, u_score):.1f}%")

        # Visual Chart
        fig = px.histogram(class_data, x=selected_sub, title=f"Distribution of {selected_sub}", 
                           color_discrete_sequence=['#3366CC'], height=350)
        fig.add_vline(x=u_score, line_color="#FF4B4B", line_width=4, annotation_text="YOU")
        st.plotly_chart(fig, use_container_width=True)

    # --- COMPARISON ---
    if len(valid_keys) > 1:
        st.divider()
        st.subheader("⚔️ Subject Comparison")
        comp_df = []
        for s in valid_keys:
            comp_df.append({"Subject": s, "Score": user_scores[s], "Type": "You"})
            comp_df.append({"Subject": s, "Score": df[s].mean(), "Type": "Class"})
        
        fig_bar = px.bar(pd.DataFrame(comp_df), x="Subject", y="Score", color="Type", 
                         barmode="group", height=400, color_discrete_map={"You": "#FF4B4B", "Class": "#1F77B4"})
        st.plotly_chart(fig_bar, use_container_width=True)
else:
    st.info("👈 Use the sidebar to enter scores and see your ranking.")


# À mettre tout en bas de ton app.py
import streamlit.components.v1 as components

components.html(
    """
    <script>
        window.parent.document.addEventListener('DOMContentLoaded', function() {
            var script = document.createElement('script');
            script.dataset.goatcounter = 'https://scorecard.goatcounter.com/count';
            script.async = true;
            script.src = '//gc.zgo.at/count.js';
            window.parent.document.head.appendChild(script);
        });
    </script>
    """,
    height=0,
)

