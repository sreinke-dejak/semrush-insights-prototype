import streamlit as st
import pandas as pd
from utils import run_gap_analysis, generate_insight_no_llm

st.set_page_config(page_title="SEMrush Insights Prototype", layout="wide")

st.title("SEMrush → Insights Prototype")
st.write("Upload SEMrush CSV exports and generate content gap insights (no OpenAI key needed).")

# Sidebar (optional key for future)
st.sidebar.header("Optional (for future LLM upgrade)")
_ = st.sidebar.text_input("OpenAI API Key (not required right now)", type="password")

# Upload CSV
st.header("1️⃣ Upload SEMrush CSV")
uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success("File uploaded successfully.")
    st.dataframe(df.head())

    st.header("2️⃣ Ask Your Question")
    question = st.text_input(
        "Example: What prompts are we missing out on and what content should we create?",
        value="What prompts are we missing out on and what content recs can you make so we can better capitalize in that space?"
    )

    # Simple controls for demo
    col1, col2, col3 = st.columns(3)
    with col1:
        min_volume = st.number_input("Min Volume", min_value=0, value=100, step=50)
    with col2:
        gap_position_threshold = st.number_input("Treat as 'gap' if position >", min_value=1, value=20, step=1)
    with col3:
        top_n = st.number_input("Top N gaps", min_value=5, value=25, step=5)

    if st.button("Generate Insights (no API key)"):
        gaps = run_gap_analysis(df, min_volume=min_volume, gap_position_threshold=gap_position_threshold, top_n=top_n)

        st.header("📌 Evidence (Top Gaps)")
        st.dataframe(pd.DataFrame(gaps))

        insight = generate_insight_no_llm(question, gaps)

        st.header("📊 Insight Output (Structured JSON)")
        st.json(insight)



