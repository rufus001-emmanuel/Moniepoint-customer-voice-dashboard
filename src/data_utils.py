"""Small, tolerant CSV normalization utilities for the quick-start dashboard."""
import pandas as pd

ALIASES = {
    "review_text": "review_text_original", "content": "review_text_original",
    "text": "review_text_original", "score": "rating", "at": "review_date",
    "username": "userName", "user_name": "userName", "user": "userName",
    "translated_text": "review_text_english", "topic": "complaint_category",
}
COLUMNS = ["review_id", "review_text_original", "review_text_english", "rating", "review_date", "userName", "country", "language", "sentiment", "complaint_category", "is_complaint", "short_summary", "classification_status"]

def normalize_reviews(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    # Case-insensitive aliases; preserve the user's original columns as well.
    lower_to_actual = {str(c).strip().lower(): c for c in out.columns}
    for alias, target in ALIASES.items():
        if alias in lower_to_actual and target not in out.columns:
            out[target] = out[lower_to_actual[alias]]
    if "review_id" not in out.columns:
        out["review_id"] = ""
    if "review_text_original" not in out.columns:
        out["review_text_original"] = ""
    if "review_text_english" not in out.columns:
        out["review_text_english"] = ""
    for col in COLUMNS:
        if col not in out.columns: out[col] = ""
    out["review_id"] = out["review_id"].fillna("").astype(str).str.strip()
    out["review_text_original"] = out["review_text_original"].fillna("").astype(str)
    out["review_text_english"] = out["review_text_english"].fillna("").astype(str)
    out["rating"] = pd.to_numeric(out["rating"], errors="coerce")
    out["review_date"] = pd.to_datetime(out["review_date"], errors="coerce")
    with_id = out[out["review_id"].ne("")].drop_duplicates("review_id", keep="last")
    without_id = out[out["review_id"].eq("")]
    out = pd.concat([with_id, without_id], ignore_index=True)
    return out
