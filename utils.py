import pandas as pd
import requests
import json

def run_gap_analysis(df):
    df.columns = [c.lower() for c in df.columns]

    if "volume" not in df.columns:
        df["volume"] = 0

    if "position" not in df.columns:
        df["position"] = 999

    df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0)
    df["position"] = pd.to_numeric(df["position"], errors="coerce").fillna(999)

    gaps = df[df["position"] > 20]
    gaps = gaps.sort_values("volume", ascending=False)

    return gaps.head(50).to_dict(orient="records")


def generate_insight(api_key, question, gap_data):

    system_prompt = """
You are an SEO content strategist.
Only use the provided keyword gap data.
Return JSON with:
- summary
- top_opportunities (list)
- recommended_actions (list)
- estimated_impact
Return only valid JSON.
"""

    user_prompt = f"""
User Question:
{question}

Gap Data:
{json.dumps(gap_data)}
"""

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2
        }
    )

    result = response.json()

    try:
        return json.loads(result["choices"][0]["message"]["content"])
    except:
        return {"error": result}
