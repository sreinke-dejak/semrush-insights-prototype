import streamlit as st
import pandas as pd
import json
from utils import run_gap_analysis, generate_insight

st.set_page_config(page_title="SEMrush Insights Prototype", layout="wide")

st.title("SEMrush → Insights Prototype")

st.write("Upload SEMrush CSV exports and generate content gap insights.")

# Sidebar API Key
st.sidebar.header("API Keys")
openai_key = st.sidebar.text_input("OpenAI API Key", type="password")

# Upload CSV
st.header("1️⃣ Upload SEMrush CSV")
uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success("File uploaded successfully.")
    st.dataframe(df.head())

    st.header("2️⃣ Ask Your Question")
    question = st.text_input(
        "Example: What prompts are we missing out on and what content should we create?"
    )

    if st.button("Generate Insights"):
        if not openai_key:
            st.error("Please enter your OpenAI API key in the sidebar.")
        else:
            gaps = run_gap_analysis(df)
            insight = generate_insight(openai_key, question, gaps)

            st.header("📊 Insight Output")
            st.json(insight)

