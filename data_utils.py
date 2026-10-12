import importlib
import json
from pathlib import Path

import pandas as pd

# Try import scraper, if not installed will fallback to CSV.
# Use importlib to avoid static-analysis "missing import" warnings when the
# optional dependency is not installed in the current environment.
try:
    google_play_scraper = importlib.import_module("google_play_scraper")
    reviews = google_play_scraper.reviews
    Sort = google_play_scraper.Sort
    # The scraper's exceptions submodule may not be available to static
    # analyzers; catch scraper failures through the general exception handler.
    GooglePlayScraperException = Exception
    RequestException = importlib.import_module("requests.exceptions").RequestException
    SCRAPER_AVAILABLE = True
except ImportError:
    reviews = None
    Sort = None
    GooglePlayScraperException = Exception
    RequestException = Exception
    SCRAPER_AVAILABLE = False

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "moniepoint_reviews.csv"
METRICS_FILE = BASE_DIR / "results" / "evaluation_metrics.json"
CONFUSION_FILE = BASE_DIR / "results" / "gemini_sentiment_confusion_matrix.csv"
ERRORS_FILE = BASE_DIR / "results" / "gemini_sentiment_errors.csv"

ALT_PATHS = [
    BASE_DIR / "data" / "moniepoint_reviews.csv",
    BASE_DIR / "src" / "data" / "moniepoint_reviews.csv",
    BASE_DIR / "data" / "moniepoint_review.csv",
    BASE_DIR / "moniepoint_reviews.csv",
]

REQUIRED_COLUMNS = ["review_id", "review_text", "rating", "review_date", "sentiment", "category"]

def find_data_file():
    for p in ALT_PATHS:
        if p.exists() and p.stat().st_size > 0:
            return p
    return DATA_FILE

def fetch_live_reviews():
    """Fetch live from Play Store Jan 1 2025 to Today"""
    if not SCRAPER_AVAILABLE:
        return None

    print("Fetching live reviews from Play Store...")
    APP_ID = 'com.teamapt.moneypoint'
    START_DATE = pd.to_datetime("2025-01-01").date()

    all_reviews = []

    try:
        result, token = reviews(
            APP_ID,
            lang='en',
            country='ng',
            sort=Sort.NEWEST,
            count=5000
        )
        all_reviews.extend(result)

        # Fetch more until we go below Jan 1 2025
        while token and len(all_reviews) < 25000:
            result, token = reviews(
                APP_ID,
                lang='en',
                country='ng',
                sort=Sort.NEWEST,
                count=5000,
                continuation_token=token
            )
            all_reviews.extend(result)
            # Stop if oldest review is before 2025
            if result:
                oldest = min([r['at'] for r in result]).date()
                if oldest < START_DATE:
                    break

        if not all_reviews:
            return None

        df = pd.DataFrame(all_reviews)

        # Build our required columns
        df_new = pd.DataFrame()
        df_new['review_id'] = df['reviewId'] if 'reviewId' in df.columns else range(1, len(df)+1)
        df_new['review_text'] = df['content'].astype(str)
        df_new['rating'] = pd.to_numeric(df['score'], errors='coerce').fillna(3)
        df_new['review_date'] = pd.to_datetime(df['at'], errors='coerce')

        # Filter Jan 1 2025 to Today
        df_new = df_new[df_new['review_date'] >= pd.to_datetime("2025-01-01")].copy()

        print(f"Live fetched: {len(df_new)} reviews from Jan 1 2025 to Today")

        # Save as cache for offline use
        try:
            DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
            df_new.to_csv(DATA_FILE, index=False)
        except OSError:
            pass

        return df_new

    except (GooglePlayScraperException, RequestException, OSError, ValueError, KeyError) as e:
        print(f"Live fetch failed: {e}")
        return None

def load_reviews():
    """
    Load reviews - LIVE version (Option B)
    Tries live fetch first, fallback to CSV if offline
    """
    df = fetch_live_reviews()

    if df is None or df.empty:
        # Fallback to CSV
        print("Using saved CSV file...")
        actual_file = find_data_file()
        if not actual_file.exists():
            raise FileNotFoundError("No data file found. Please check internet connection.")
        df = pd.read_csv(actual_file)
        df.columns = [c.lower().strip() for c in df.columns]
        col_map = {'review':'review_text','text':'review_text','comment':'review_text','content':'review_text','date':'review_date'}
        df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

    df.columns = [c.lower().strip() for c in df.columns]
    if 'review_id' not in df.columns:
        df['review_id'] = range(1, len(df) + 1)
    if 'review_text' not in df.columns:
        df['review_text'] = df.iloc[:, 0].astype(str)
    if 'rating' not in df.columns:
        df['rating'] = 3
    if 'review_date' not in df.columns:
        df['review_date'] = pd.Timestamp.now()

    if 'sentiment' not in df.columns:
        def get_sentiment(t):
            t = str(t).lower()
            neg = ['bad','poor','slow','failed','scam','fraud','worst','terrible','hate','issue','problem','not working','disappoint','useless','stuck','error','cannot','unable']
            pos = ['good','great','love','excellent','fast','best','easy','nice','helpful','awesome','perfect','smooth','reliable','wonderful']
            if any(w in t for w in neg):
                return 'Negative'
            if any(w in t for w in pos):
                return 'Positive'
            return 'Neutral'
        df['sentiment'] = df['review_text'].apply(get_sentiment)

    if 'category' not in df.columns:
        def get_category(t):
            t = str(t).lower()
            if any(w in t for w in ['transfer','transaction','send','debit','credit','money']):
                return 'Transfers'
            if any(w in t for w in ['app','crash','login','slow','bug','update','open','usability']):
                return 'App Experience'
            if any(w in t for w in ['support','service','agent','customer','care','response']):
                return 'Customer Support'
            if any(w in t for w in ['fee','charge','deduct']):
                return 'Fees/Charges'
            if any(w in t for w in ['pos','terminal']):
                return 'POS'
            return 'General'
        df['category'] = df['review_text'].apply(get_category)

    df["review_date"] = pd.to_datetime(df["review_date"], errors="coerce")
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce").fillna(3)
    df["sentiment"] = df["sentiment"].astype(str).str.strip().str.title()
    df["category"] = df["category"].astype(str).str.strip()
    df["review_text"] = df["review_text"].astype(str).str.strip()

    # Final filter Jan 1 2025 to Today for safety
    df = df[df["review_date"] >= pd.to_datetime("2025-01-01")].copy()

    return df

def load_evaluation_metrics():
    if not METRICS_FILE.exists():
        return {}
    with open(METRICS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def load_confusion_matrix():
    if not CONFUSION_FILE.exists():
        return pd.DataFrame()
    return pd.read_csv(CONFUSION_FILE)

def load_errors():
    if not ERRORS_FILE.exists():
        return pd.DataFrame()
    return pd.read_csv(ERRORS_FILE)

def get_complaint_counts(df):
    negative_reviews = df[df["sentiment"].str.lower() == "negative"].copy()
    if negative_reviews.empty:
        return pd.DataFrame(columns=["category", "count"])
    counts = negative_reviews["category"].value_counts().reset_index()
    counts.columns = ["category", "count"]
    return counts

def get_business_summary(df):
    total_feedback = len(df)
    positive_count = (df["sentiment"].str.lower() == "positive").sum()
    negative_count = (df["sentiment"].str.lower() == "negative").sum()
    neutral_count = (df["sentiment"].str.lower() == "neutral").sum()
    if total_feedback > 0:
        positive_pct = positive_count / total_feedback * 100
        negative_pct = negative_count / total_feedback * 100
        neutral_pct = neutral_count / total_feedback * 100
    else:
        positive_pct = negative_pct = neutral_pct = 0
    average_rating = df["rating"].mean()
    complaint_counts = get_complaint_counts(df)
    if not complaint_counts.empty:
        top_category = complaint_counts.iloc[0]["category"]
        top_count = int(complaint_counts.iloc[0]["count"])
    else:
        top_category = "No complaints"
        top_count = 0
    return {
        "total_feedback": int(total_feedback),
        "positive_count": int(positive_count),
        "negative_count": int(negative_count),
        "neutral_count": int(neutral_count),
        "positive_pct": float(positive_pct),
        "negative_pct": float(negative_pct),
        "neutral_pct": float(neutral_pct),
        "average_rating": float(average_rating) if pd.notna(average_rating) else 0,
        "total_complaints": int(negative_count),
        "top_complaint_category": top_category,
        "top_complaint_count": top_count,
    }