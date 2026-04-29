# ScoreCard AI: Academic Performance Analytics

**Course:** TP INF 232 - Statistics and Data Analysis  
**Project Objective:** Implementing descriptive statistics and comparative analytics using Python to evaluate student performance.

---

## 📌 Project Overview

**ScoreCard AI** is a data-driven dashboard designed to provide students with immediate, actionable insights into their academic results. Instead of looking at raw numbers, the app uses statistical measurements to show a student’s standing relative to the entire cohort.

## 🛠 Features & Statistical Application

The app focuses on three core pillars of data analysis:

1. **Central Tendency & Dispersion:**
   - Calculates **Mean**, **Median**, and **Standard Deviation** for each subject.
   - Uses **Z-Scores** to measure how many standard deviations a score is from the class average.
2. **Positional Analytics:**
   - Computes **Percentile Ranks** to show the percentage of students performing below the user.
   - Identifies the student's "bracket" within the distribution.
3. **Visual Analytics:**
   - **Frequency Histograms:** Visualizes the distribution of scores with a dynamic marker for the user’s position.
   - **Comparative Bar Charts:** Side-by-side comparison of individual scores against class averages.

## 🚀 Technical Stack

- **Language:** Python
- **Frontend/UI:** Streamlit
- **Data Processing:** Pandas & NumPy
- **Visualization:** Plotly (Interactive charts)
- **Mathematical Engine:** SciPy (Statistical distributions)

## 📂 Project Structure

- `app.py`: The main application logic and UI code.
- `cleaned_results.csv`: The dataset containing academic records.
- `requirements.txt`: List of dependencies for deployment.

## ⚙️ How to Run Locally

1. **Install dependencies:**

   ```bash
   pip install streamlit pandas plotly scipy

   ```

2. **Run app:**
   ```bash
   streamlit run app.py
   ```
