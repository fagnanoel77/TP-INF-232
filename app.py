import streamlit as st
import pandas as pd
import plotly.express as px
from scipy import stats
import numpy as np

# --- CONFIG & STYLING ---
st.set_page_config(page_title="ScoreCard AI", page_icon="🎓", layout="wide")

# Custom CSS for a cleaner look
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- DATA LOADING ---
@st.cache_data
def load_data():
    df = pd.read_csv('cleaned_results.csv')
    df = df.dropna(subset=['matricule'])
    
    # Subject columns are those with numeric scores
    subject_cols = ['FBLI11', 'INF111', 'INF112', 'INF121', 'INF122', 'INF131', 
                    'INF132', 'INF141', 'INF142', 'INF151', 'INF152', 'MAT112', 
                    'MAT131', 'PHY161', 'PPE111']
    return df, subject_cols

df, subjects = load_data()

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("🎓 ScoreCard AI")
    st.info("Quickly analyze your academic standing relative to the class.")
    
    mode = st.radio("Step 1: Choose Entry Mode", ["Matricule Number", "Manual Entry"])
    
    user_scores = {} 
    
    if mode == "Matricule Number":
        search_id = st.selectbox("Select/Type your Matricule", df['matricule'].unique())
        student_row = df[df['matricule'] == search_id].iloc[0]
        st.success(f"Viewing: {student_row['name']}")
        
        # Pre-load all scores for this student
        for sub in subjects:
            user_scores[sub] = student_row[sub]
            
    else:
        st.subheader("Enter your scores")
        # UX Tweak: Pick subjects first to avoid clutter
        selected_manual_subs = st.multiselect("Choose subjects to enter:", subjects, default=[subjects[0]])
        
        # Only show input boxes for the chosen subjects
        for sub in selected_manual_subs:
             val = st.number_input(f"Score for {sub}", 0.0, 100.0, 50.0)
             user_scores[sub] = val

# --- FEATURE 1: DEEP DIVE ---
st.title("📊 Personal Performance Deep-Dive")
selected_sub = st.selectbox("Which subject do you want to analyze?", subjects)

# Stats Logic (Handle NaNs gracefully)
class_data = df[selected_sub].dropna()
user_score = user_scores.get(selected_sub, np.nan)

if np.isnan(user_score):
    st.warning(f"⚠️ No score entered/found for {selected_sub}. Please enter it in the sidebar.")
else:
    mean_val = class_data.mean()
    std_val = class_data.std()
    percentile = stats.percentileofscore(class_data, user_score)
    z_score = (user_score - mean_val) / std_val if std_val > 0 else 0

    # Metric Row
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Your Score", f"{user_score:.1f}")
    c2.metric("Class Average", f"{mean_val:.1f}")
    c3.metric("Percentile Rank", f"{percentile:.1f}%")
    c4.metric("Performance Index (Z)", f"{z_score:.2f}")

    # Visual Distribution
    fig = px.histogram(class_data, x=selected_sub, nbins=25, 
                       title=f"Class Distribution: {selected_sub}",
                       color_discrete_sequence=['#3366CC'], opacity=0.6)
    
    fig.add_vline(x=user_score, line_width=5, line_color="#FF4B4B", 
                  annotation_text="YOU", annotation_position="top left")
    
    st.plotly_chart(fig, use_container_width=True)

# --- FEATURE 2: SUBJECT BATTLE ---
st.divider()
st.title("⚔️ Subject Comparison")
st.write("Compare your results against the class average for specific subjects.")

compare_list = st.multiselect("Pick up to 3 subjects to compare", subjects, default=subjects[:3])

if compare_list:
    comparison_data = []
    for sub in compare_list:
        score = user_scores.get(sub, 0)
        avg = df[sub].dropna().mean()
        comparison_data.append({"Subject": sub, "Score": score, "Type": "Your Score"})
        comparison_data.append({"Subject": sub, "Score": avg, "Type": "Class Average"})
    
    comp_df = pd.DataFrame(comparison_data)
    
    fig_bar = px.bar(comp_df, x="Subject", y="Score", color="Type", barmode="group",
                     color_discrete_map={"Your Score": "#FF4B4B", "Class Average": "#1F77B4"},
                     height=400)
    
    st.plotly_chart(fig_bar, use_container_width=True)

    # Insight Text (Finds strongest subject dynamically)
    valid_subs = [s for s in compare_list if not np.isnan(user_scores.get(s, np.nan))]
    if valid_subs:
        best_sub = max(valid_subs, key=lambda x: user_scores.get(x) - df[x].mean())
        st.info(f"💡 **Insight:** Relative to the average, your strongest subject here is **{best_sub}**.")