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

# Theme-aware styling
st.markdown("""
    <style>
    .gpa-label { font-size: 0.9rem; opacity: 0.8; margin-bottom: -15px; text-transform: lowercase; }
    .gpa-value { font-size: 4rem; font-weight: bold; color: #FF4B4B; line-height: 1.2; }
    .gpa-avg { font-size: 1.3rem; opacity: 0.9; text-transform: lowercase; }
    
    /* Responsive metric boxes for Dark/Light mode */
    div[data-testid="stMetric"] {
        padding: 15px;
        border-radius: 10px;
        border: 1px solid rgba(128, 128, 128, 0.2);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA & FILE MANAGEMENT ---
ORIGINAL_FILE = 'cleaned_results.csv'
SAVED_FILE = 'user_submissions.csv'

def initialize_files():
    """Ensure the user submission file exists with the right columns."""
    if not os.path.exists(SAVED_FILE):
        try:
            df_orig = pd.read_csv(ORIGINAL_FILE)
            empty_df = pd.DataFrame(columns=df_orig.columns)
            empty_df.to_csv(SAVED_FILE, index=False)
        except Exception:
            pass

@st.cache_data
def load_all_data():
    """Load and combine original data with user submissions."""
    df_orig = pd.read_csv(ORIGINAL_FILE)
    if os.path.exists(SAVED_FILE):
        df_user = pd.read_csv(SAVED_FILE)
        df_combined = pd.concat([df_orig, df_user], ignore_index=True)
    else:
        df_combined = df_orig
        
    df_combined = df_combined.dropna(subset=['matricule'])
    
    # Define subject columns
    subject_cols = ['FBLI11', 'INF111', 'INF112', 'INF121', 'INF122', 'INF131', 
                    'INF132', 'INF141', 'INF142', 'INF151', 'INF152', 'MAT112', 
                    'MAT131', 'PHY161', 'PPE111']
    return df_combined, subject_cols

initialize_files()
df, subjects = load_all_data()

# --- 3. SIDEBAR NAVIGATION & ENTRY ---
with st.sidebar:
    st.title("🎓 ScoreCard AI")
    mode = st.radio("Step 1: Choose Entry Mode", ["Matricule Number", "Manual Entry"])
    
    user_scores = {}
    current_gpa = 0.0
    
    if mode == "Matricule Number":
        search_id = st.selectbox("Select/Type your Matricule", df['matricule'].unique())
        student_row = df[df['matricule'] == search_id].iloc[0]
        st.success(f"Viewing: {student_row['name']}")
        
        current_gpa = student_row.get('mgp', 0.0)
        for sub in subjects:
            user_scores[sub] = student_row[sub]
            
    else:
        st.subheader("Manual Score Entry")
        selected_manual_subs = st.multiselect(
            "Select 8 to 10 subjects:", 
            subjects,
            help="You must select between 8 and 10 subjects to save your record."
        )
        
        # Collect scores
        for sub in selected_manual_subs:
             user_scores[sub] = st.number_input(f"Score for {sub}", 0.0, 100.0, 50.0)

        # Real-time GPA Estimation
        if user_scores:
            scores_only = [v for v in user_scores.values() if v > 0]
            if scores_only:
                # Estimate GPA on a 4.0 scale (assuming scores are out of 100)
                current_gpa = (sum(scores_only) / len(scores_only)) / 25
            
            st.metric("Estimated GPA", f"{current_gpa:.2f}")

        st.divider()
        
        # --- SAVE & RECORD LOGIC ---
        num_selected = len(selected_manual_subs)
        if 8 <= num_selected <= 10:
            st.info("💡 Ready to record results.")
            reg_name = st.text_input("Full Name")
            
            # Auto-capitalize and strip spaces
            raw_mat = st.text_input("Matricule (e.g. 24F1234)")
            reg_mat = raw_mat.upper().strip() 
            
            if st.button("💾 Save & Record Results"):
                # Strict Regex Validation: 2 numbers, 1 letter, 4 numbers
                mat_pattern = re.compile(r"^[0-9]{2}[A-Z]{1}[0-9]{4}$")
                
                if not reg_name or not reg_mat:
                    st.error("Please fill in both Name and Matricule.")
                elif not mat_pattern.match(reg_mat):
                    st.error("Format Error! Use 00X0000 (The middle character must be a Letter).")
                elif reg_mat in df['matricule'].astype(str).values:
                    st.error(f"The matricule {reg_mat} is already in the database!")
                else:
                    try:
                        # Prepare the new row
                        new_row = {col: np.nan for col in df.columns}
                        new_row['name'] = reg_name
                        new_row['matricule'] = reg_mat
                        new_row['mgp'] = current_gpa
                        for sub, score in user_scores.items(): 
                            new_row[sub] = score
                        
                        # Append to CSV
                        pd.DataFrame([new_row]).to_csv(SAVED_FILE, mode='a', header=False, index=False)
                        
                        # Success Message & 5-Second Delay
                        msg_slot = st.empty()
                        msg_slot.success(f"✅ Success! Record for {reg_name} ({reg_mat}) saved. Refreshing in 5s...")
                        st.balloons()
                        time.sleep(5)
                        
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Database Error: Could not save file. {e}")
        else:
            st.warning(f"Please select 8-10 subjects to enable saving. (Current: {num_selected})")


# --- 4. MAIN DASHBOARD ---
st.title("📊 Personal Performance Analysis")

if not user_scores or all(pd.isna(v) for v in user_scores.values()):
    st.info("👈 Please select a matricule or enter your scores in the sidebar to begin.")
else:
    # --- GPA SECTION ---
    avg_gpa = df['mgp'].mean()
    st.markdown(f"""
        <div style="margin-bottom: 30px; padding-left: 5px;">
            <p class="gpa-label">your GPA</p>
            <p class="gpa-value">{current_gpa:.2f}</p>
            <p class="gpa-avg">average gpa: {avg_gpa:.2f}</p>
        </div>
    """, unsafe_allow_html=True)

    # --- DEEP DIVE SECTION ---
    valid_keys = [s for s, v in user_scores.items() if not pd.isna(v)]
    
    if valid_keys:
        selected_sub = st.selectbox("Select subject for Deep-Dive:", valid_keys)
        
        class_data = df[selected_sub].dropna()
        u_score = user_scores.get(selected_sub, 0)
        
        mean_val = class_data.mean()
        std_val = class_data.std()
        percentile = stats.percentileofscore(class_data, u_score)
        z_score = (u_score - mean_val) / std_val if std_val > 0 else 0
        
        # Metrics
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Your Score", f"{u_score:.1f}")
        c2.metric("Class Average", f"{mean_val:.1f}")
        c3.metric("Percentile Rank", f"{percentile:.1f}%")
        c4.metric("Performance Index (Z)", f"{z_score:.2f}")

        # Histogram
        fig = px.histogram(class_data, x=selected_sub, nbins=20, 
                           title=f"Distribution of {selected_sub} (All Students)",
                           color_discrete_sequence=['#3366CC'], opacity=0.7)
        fig.add_vline(x=u_score, line_width=5, line_color="#FF4B4B", annotation_text="YOU")
        st.plotly_chart(fig, use_container_width=True)

        # --- COMPARISON SECTION ---
        st.divider()
        st.subheader("⚔️ Subject Comparison")
        
        if len(valid_keys) > 1:
            comparison_data = []
            for sub in valid_keys:
                avg = df[sub].mean()
                comparison_data.append({"Subject": sub, "Score": user_scores[sub], "Type": "You"})
                comparison_data.append({"Subject": sub, "Score": avg, "Type": "Class Avg"})
            
            comp_df = pd.DataFrame(comparison_data)
            fig_bar = px.bar(comp_df, x="Subject", y="Score", color="Type", barmode="group", 
                             color_discrete_map={"You": "#FF4B4B", "Class Avg": "#1F77B4"},
                             height=400)
            st.plotly_chart(fig_bar, use_container_width=True)
