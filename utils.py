import pandas as pd
from typing import List, Dict, Any

def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]

    # Common SEMrush-ish column names
    # We support: keyword, volume, position, url, domain
    if "keyword" not in df.columns:
        # fallback: first column becomes keyword
        df.rename(columns={df.columns[0]: "keyword"}, inplace=True)

    # Volume
    if "volume" not in df.columns:
        # try common alternatives
        for alt in ["vol", "search_volume", "search volume", "monthly_volume"]:
            if alt in df.columns:
                df.rename(columns={alt: "volume"}, inplace=True)
                break
    if "volume" not in df.columns:
        df["volume"] = 0

    # Position
    if "position" not in df.columns:
        for alt in ["pos", "rank"]:
            if alt in df.columns:
                df.rename(columns={alt: "position"}, inplace=True)
                break
    if "position" not in df.columns:
        df["position"] = 999

    # Optional
    if "url" not in df.columns:
        df["url"] = ""
    if "domain" not in df.columns:
        df["domain"] = ""

    # Types
    df["keyword"] = df["keyword"].astype(str)
    df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0).astype(int)
    df["position"] = pd.to_numeric(df["position"], errors="coerce").fillna(999).astype(int)

    return df


def run_gap_analysis(
    df: pd.DataFrame,
    min_volume: int = 100,
    gap_position_threshold: int = 20,
    top_n: int = 25
) -> List[Dict[str, Any]]:
    """
    Simple gap logic for demo:
    - Keep keywords with volume >= min_volume
    - Consider "gap" if position > threshold or missing (>= 999)
    - Return top N by volume
    """
    df = _normalize_columns(df)

    gaps = df[(df["volume"] >= min_volume) & (df["position"] > gap_position_threshold)].copy()
    gaps = gaps.sort_values(by=["volume", "position"], ascending=[False, True]).head(top_n)

    return gaps[["keyword", "volume", "position", "url", "domain"]].to_dict(orient="records")


def generate_insight_no_llm(question: str, gap_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Rule-based narrative generator that produces structured JSON similar to the LLM output.
    No API calls required. Good for stakeholder demos and prototyping.
    """

    if not gap_data:
        return {
            "question": question,
            "summary": "No gaps found based on current filters.",
            "top_opportunities": [],
            "recommended_actions": [
                "Lower the Min Volume filter, or raise the gap threshold to broaden results.",
                "Upload a SEMrush export with more keywords (Keyword Gap / Organic Research / Position Tracking)."
            ],
            "estimated_impact": "low (insufficient evidence rows)",
        }

    df = pd.DataFrame(gap_data)

    # Quick heuristics to categorize intent-ish themes from keywords
    keywords = df["keyword"].astype(str).tolist()
    themes = {
        "cost_coverage": ["cost", "price", "coverage", "insurance", "benefits"],
        "comparisons": ["vs", "versus", "compare", "best"],
        "how_to": ["how", "timeline", "steps", "process"],
        "local": ["near me", "clinic", "doctor", "center"],
        "eligibility": ["qualify", "requirements", "eligible", "who can"],
        "success_rates": ["success", "rate", "chances", "age"]
    }

    theme_hits = {k: 0 for k in themes.keys()}
    for kw in keywords:
        low = kw.lower()
        for theme, tokens in themes.items():
            if any(t in low for t in tokens):
                theme_hits[theme] += 1

    # Top themes
    top_themes = sorted(theme_hits.items(), key=lambda x: x[1], reverse=True)
    top_themes = [t for t, c in top_themes if c > 0][:3]

    # Opportunities: top 8 by volume
    top_opps = df.sort_values("volume", ascending=False).head(8).to_dict(orient="records")

    # Build recommended actions (demo-ready)
    recs = []
    recs.append("Create 1–2 pillar pages for the highest-volume missed themes, then add supporting FAQ sections targeting long-tail variants.")
    if "cost_coverage" in top_themes:
        recs.append("Build/refresh a 'Cost & Coverage' hub: IVF cost, egg freezing cost, what insurance covers, state-by-state considerations, and employer benefit explainers.")
    if "how_to" in top_themes:
        recs.append("Publish a 'How it works / Timeline' guide with step-by-step sections, eligibility, and what to expect—optimize for 'how/timeline' queries.")
    if "comparisons" in top_themes:
        recs.append("Create comparison pages (e.g., IVF vs surrogacy) with decision frameworks, pros/cons, and FAQ—these often win high-intent searches.")
    if "success_rates" in top_themes:
        recs.append("Add medically-reviewed success rate content with age bands, definitions, and citations—optimize headings for 'success rate' questions.")
    if "local" in top_themes:
        recs.append("If appropriate, create a location/clinic-finder support page and SEO FAQs for 'near me' intent (often requires local SEO strategy).")

    # Add tactical SEO recs
    recs.extend([
        "For each new/updated page: add a concise definition near the top, a table of contents, and 6–10 FAQ items matching question-style keywords.",
        "Add internal links from your highest-traffic pages to the new hubs using descriptive anchor text.",
        "Track success: top 10 rankings for the cluster, organic entrances to the new pages, and downstream conversion proxy (CTA clicks / lead starts)."
    ])

    # Simple impact estimate
    total_volume = int(df["volume"].sum())
    # Super rough: assume 5% CTR capture of total volume as “potential clicks”
    est_clicks = int(total_volume * 0.05)

    return {
        "question": question,
        "summary": f"Found {len(df)} high-opportunity keywords where current ranking is weaker than the configured threshold. Top themes: {', '.join(top_themes) if top_themes else 'general gaps'}.",
        "top_opportunities": [
            {
                "keyword": r.get("keyword"),
                "volume": int(r.get("volume", 0)),
                "current_position": int(r.get("position", 999)),
                "suggested_asset": _suggest_asset_type(str(r.get("keyword", ""))),
                "notes": "Prioritize by volume + intent; treat this as a content brief starter."
            }
            for r in top_opps
        ],
        "recommended_actions": recs,
        "estimated_impact": {
            "method": "Sum(volume) * 0.05 (rough CTR capture proxy for demo)",
            "total_volume_in_gaps": total_volume,
            "estimated_additional_clicks_per_month": est_clicks,
            "confidence": "low (rule-based prototype estimate)"
        }
    }


def _suggest_asset_type(keyword: str) -> str:
    k = keyword.lower()
    if any(x in k for x in ["cost", "price", "coverage", "insurance"]):
        return "Cost/Coverage hub page + FAQ"
    if any(x in k for x in ["vs", "versus", "compare", "best"]):
        return "Comparison page"
    if any(x in k for x in ["how", "timeline", "steps", "process"]):
        return "How-to / Timeline guide"
    if any(x in k for x in ["success", "rate", "chances", "age"]):
        return "Success rates explainer (medically reviewed)"
    if any(x in k for x in ["near me", "clinic", "doctor", "center"]):
        return "Local intent support page + FAQs"
    return "Educational pillar page + supporting FAQs"
