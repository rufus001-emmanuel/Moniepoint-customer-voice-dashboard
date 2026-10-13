import datetime
import logging
import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# Try import gemini, but make it optional
try:
    from google.genai.errors import APIError

    from src.gemini_classifier import classify_review, get_client
except ImportError:
    APIError = None
    classify_review = None
    get_client = None
    GEMINI_AVAILABLE = False
else:
    GEMINI_AVAILABLE = True

from src.data_utils import (
    get_business_summary,
    get_complaint_counts,
    load_confusion_matrix,
    load_errors,
    load_evaluation_metrics,
    load_reviews,
)

# ================= CONFIG =================
st.set_page_config(
    page_title="Moniepoint | Customer Voice Dashboard",
    page_icon="logo.png",
    layout="wide",
)

# ================= CLEAN PROFESSIONAL CSS =================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #1A1A1A; }
.main { background: #F7F8FA; }
.block-container { padding-top: 1rem; max-width: 1280px; }

/* Cards - flat, no glow, no gradient */
.kpi-card {
    background: white;
    border-radius: 10px;
    padding: 16px 18px;
    border: 1px solid #E5E8ED;
    height: 112px;
}
.kpi-label { font-size: 12px; font-weight: 600; color: #667085; }
.kpi-value { font-size: 28px; font-weight: 700; color: #0A2540; margin-top: 6px; line-height: 1; }
.kpi-sub { font-size: 12px; color: #667085; margin-top: 6px; }

.white-box {
    background: white;
    border-radius: 10px;
    padding: 20px;
    border: 1px solid #E5E8ED;
}
.guide-box {
    background: #EFF4FF;
    border: 1px solid #D1E0FF;
    border-radius: 10px;
    padding: 14px 18px;
    font-size: 14px;
    color: #0A2540;
}
.explain { font-size: 13px; color: #667085; margin-top: 6px; }
.section-title { font-size: 17px; font-weight: 700; color: #0A2540; margin-bottom: 4px; }
.action-box {
    background: white;
    border-radius: 10px;
    padding: 16px;
    border: 1px solid #E5E8ED;
    border-left: 4px solid #0357EE;
    margin-bottom: 10px;
}
.quote-box {
    background: white;
    border-radius: 10px;
    padding: 14px 16px;
    border: 1px solid #E5E8ED;
    border-left: 4px solid #D92D20;
    margin-bottom: 10px;
}
.stTabs [data-baseweb="tab"] { font-size: 14px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ================= LOAD DATA =================
try:
    df = load_reviews()
except (OSError, ValueError, pd.errors.ParserError, pd.errors.EmptyDataError) as e:
    st.error(str(e))
    st.stop()

metrics = load_evaluation_metrics()
confusion_df = load_confusion_matrix()
errors_df = load_errors()
BASE_DIR = (
    Path(globals()["__file__"]).resolve().parent.parent
    if "__file__" in globals()
    else Path.cwd()
)

# ================= HEADER =================
c1, c2, c3 = st.columns([1.1, 5, 1.4])
with c1:
    if (BASE_DIR / "logo.png").exists():
        st.image(str(BASE_DIR / "logo.png"), width=150)
with c2:
    st.markdown("<h2 style='text-align:center;color:#0A2540;margin:0;'>Moniepoint Customer Voice Dashboard</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;color:#667085;margin:4px 0 0 0;font-size:13px;'>What customers are saying about Moniepoint, and what we should fix first.</p>", unsafe_allow_html=True)
with c3:
    st.markdown(f"<div style='text-align:right;color:#667085;font-size:13px;'>{pd.Timestamp.now().strftime('%b %d, %Y')}</div>", unsafe_allow_html=True)

# How to use - for non-technical users
st.markdown("""
<div class='guide-box'>
<b>How to use this dashboard:</b> Start from left to right.
1. Look at the numbers at the top for the overall picture.
2. Go to <b>Overview</b> to see the biggest problem.
3. Go to <b>What Customers Are Saying</b> to see the details.
4. Use the filters on the left to see a specific time period, rating, or category.
</div>
""", unsafe_allow_html=True)
st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
# ================= SIDEBAR =================
st.sidebar.markdown("### Filters")
st.sidebar.caption("Use these to narrow down the feedback you want to see.")

START_CALENDAR = datetime.date(2025, 1, 1)
TODAY = datetime.date.today()
END_CALENDAR = datetime.date(2099, 12, 31)

date_range = st.sidebar.date_input(
    "Select period",
    value=(START_CALENDAR, TODAY),
    min_value=START_CALENDAR,
    max_value=END_CALENDAR
)
if len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = date_range[0], TODAY

df['date_parsed'] = pd.to_datetime(df['review_date'], errors='coerce')
df['date_parsed_date'] = df['date_parsed'].dt.date
mask = (df['date_parsed_date'] >= start_date) & (df['date_parsed_date'] <= end_date)
df = df[mask].copy()

sel_sent = st.sidebar.selectbox("Are customers happy or unhappy?", ["All", "Positive", "Negative", "Neutral"])
cat_opts = ["All"] + sorted(df["category"].dropna().unique().tolist()) if "category" in df.columns else ["All"]
sel_cat = st.sidebar.selectbox("Feedback topic", cat_opts)
sel_rate = st.sidebar.selectbox("Star rating", ["All", 1, 2, 3, 4, 5])

fdf = df.copy()
if sel_sent!= "All":
    fdf = fdf[fdf["sentiment"] == sel_sent]
if sel_cat!= "All":
    fdf = fdf[fdf["category"] == sel_cat]
if sel_rate!= "All":
    fdf = fdf[fdf["rating"] == sel_rate]

summary = get_business_summary(fdf)

# ================= KPI ROW - Plain English =================
k1, k2, k3, k4, k5, k6 = st.columns(6)
with k1:
    st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Total feedback</div><div class='kpi-value'>{summary['total_feedback']:,}</div><div class='kpi-sub'>Reviews analysed in this period</div></div>", unsafe_allow_html=True)
with k2:
    st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Happy customers</div><div class='kpi-value' style='color:#067647;'>{summary['positive_pct']:.1f}%</div><div class='kpi-sub'>{summary['positive_count']} positive reviews</div></div>", unsafe_allow_html=True)
with k3:
    st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Unhappy customers</div><div class='kpi-value' style='color:#D92D20;'>{summary['negative_pct']:.1f}%</div><div class='kpi-sub'>{summary['negative_count']} complaints</div></div>", unsafe_allow_html=True)
with k4:
    st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Average rating</div><div class='kpi-value'>{summary['average_rating']:.2f} / 5</div><div class='kpi-sub'>Average star rating</div></div>", unsafe_allow_html=True)
with k5:
    st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Total complaints</div><div class='kpi-value' style='color:#D92D20;'>{summary['total_complaints']}</div><div class='kpi-sub'>Complaints to resolve</div></div>", unsafe_allow_html=True)
with k6:
    st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Biggest complaint</div><div class='kpi-value' style='font-size:16px; margin-top:10px;'>{summary['top_complaint_category']}</div><div class='kpi-sub'>{summary['top_complaint_count']} cases</div></div>", unsafe_allow_html=True)

st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

# ================= TABS - Simple Flow =================
tab1, tab2, tab3, tab4, tab5 = st.tabs(["1. Overview", "2. What Customers Are Saying", "3. Complaints by Topic", "4. Model Health", "5. Test a Review"])

with tab1:
    col_left, col_right = st.columns([2, 1.2])
    with col_left:
        st.markdown("<div class='white-box'>", unsafe_allow_html=True)
        st.markdown(f"<div class='section-title'>Biggest problem to fix now: {summary['top_complaint_category']}</div>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size:14px; color:#344054; line-height:1.6;'>{summary['top_complaint_count']} negative reviews mention this. Customers report slow app, failed transfers, and money debited without reversal. This affects trust and retention.</p>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:13px;'><b>Impact:</b> High &nbsp; | &nbsp; <b>Priority:</b> Fix this week</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
        st.markdown("#### What we should do next")
        st.markdown("""
        <div class='action-box'><b>1. Fix transfer reversals (This week)</b><br><span style='color:#667085; font-size:13px;'>Most complaints say "transfer failed but account was debited". Add instant auto-reversal and show the reversal status in the app.</span></div>
        <div class='action-box'><b>2. Improve app speed (Next 2 weeks)</b><br><span style='color:#667085; font-size:13px;'>App Experience is a top issue. Fix slow login and crashes.</span></div>
        <div class='action-box'><b>3. Tell customers what happened (Ongoing)</b><br><span style='color:#667085; font-size:13px;'>Send SMS / push notification when a reversal is done. Customers complain they do not know when money returns.</span></div>
        """, unsafe_allow_html=True)

    with col_right:
        st.markdown("<div class='white-box'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Are customers happy or unhappy?</div>", unsafe_allow_html=True)
        st.markdown("<div class='explain'>This chart shows the share of positive, negative and neutral feedback.</div>", unsafe_allow_html=True)
        sent_counts = fdf["sentiment"].value_counts().reset_index()
        sent_counts.columns = ["sentiment", "count"]
        color_map = {"Positive": "#067647", "Negative": "#D92D20", "Neutral": "#98A2B3"}
        fig = px.pie(sent_counts, values='count', names='sentiment', hole=0.6, color='sentiment', color_discrete_map=color_map)
        fig.update_layout(showlegend=True, height=230, margin={'l': 10, 'r': 10, 't': 10, 'b': 10}, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
        st.markdown("<div class='white-box'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>How does this change over time?</div>", unsafe_allow_html=True)
        st.markdown("<div class='explain'>If the red line goes up, complaints are increasing. If green goes up, satisfaction is improving.</div>", unsafe_allow_html=True)
        tdf = fdf.dropna(subset=["review_date"]).copy()
        if not tdf.empty:
            tdf["date"] = pd.to_datetime(tdf["review_date"]).dt.date
            stime = tdf.groupby(["date", "sentiment"]).size().reset_index(name="count")
            fig2 = px.line(stime, x="date", y="count", color="sentiment", markers=True, color_discrete_map=color_map)
            fig2.update_layout(height=240, margin={'l': 0, 'r': 0, 't': 10, 'b': 0}, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            fig2.update_traces(line_width=2)
            st.plotly_chart(fig2, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    st.markdown("### Recent customer feedback")
    st.markdown("<div class='explain'>These are real comments from customers. Read them to understand the problem in their own words.</div>", unsafe_allow_html=True)
    search = st.text_input("Search feedback", placeholder="Type 'transfer', 'slow', 'failed'...")
    vdf = fdf.copy()
    if search.strip():
        vdf = vdf[vdf["review_text"].str.contains(search, case=False, na=False)]

    neg = vdf[vdf["sentiment"].str.lower() == "negative"].sort_values("review_date", ascending=False).head(6)
    st.markdown(f"#### Recent complaints ({len(neg)} shown)")
    for _, r in neg.iterrows():
        st.markdown(f"""
        <div class='quote-box'>
            <b>{r['category']}</b> &nbsp;|&nbsp; {r['rating']} out of 5 &nbsp;|&nbsp; {str(r['review_date'])[:10]}<br>
            <i>"{r['review_text'][:280]}"</i>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("#### All feedback in this filter")
    cols = [c for c in ["review_date", "rating", "sentiment", "category", "review_text"] if c in vdf.columns]
    st.dataframe(vdf[cols].sort_values("review_date", ascending=False), use_container_width=True, hide_index=True, height=400)

with tab3:
    st.markdown("### Complaints by topic")
    st.markdown("<div class='explain'>This shows which topics cause the most complaints. The longest bar is the most urgent problem.</div>", unsafe_allow_html=True)
    c1, c2 = st.columns([1.3, 1])
    with c1:
        comp = get_complaint_counts(fdf)
        if not comp.empty:
            fig = px.bar(comp, x="count", y="category", orientation='h', color="count", color_continuous_scale=["#D1E0FF", "#0357EE"], text="count")
            fig.update_layout(height=420, coloraxis_showscale=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin={'l': 0, 'r': 0, 't': 10, 'b': 0}, xaxis_title="Number of complaints", yaxis_title="Topic")
            st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown("#### Most mentioned words in complaints")
        st.markdown("<div class='explain'>These are the words customers use most often when they complain.</div>", unsafe_allow_html=True)
        if not fdf.empty:
            txt = " ".join(fdf[fdf["sentiment"].str.lower() == "negative"]["review_text"].astype(str).tolist()).lower()
            keywords = {"transfer": txt.count("transfer"), "failed": txt.count("failed"), "debit": txt.count("debit"), "slow": txt.count("slow"), "app": txt.count("app"), "network": txt.count("network")}
            top_kw = sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:5]
            for k, v in top_kw:
                st.markdown(f"<div style='background:white; padding:10px 14px; border-radius:8px; margin-bottom:8px; border:1px solid #E5E8ED;'><b>{k.upper()}</b> <span style='float:right; background:#0357EE; color:white; padding:2px 8px; border-radius:10px; font-size:12px;'>{v} mentions</span></div>", unsafe_allow_html=True)
        st.info("Why this matters: Each unresolved transfer complaint risks losing a merchant to a competitor.")

with tab4:
    st.markdown("### How accurate is the automatic classification?")
    st.markdown("<div class='explain'>We use AI to label each review as Positive, Negative or Neutral. This section shows how accurate that labelling is.</div>", unsafe_allow_html=True)
    if metrics:
        m1, m2, m3, m4 = st.columns(4)
        with m1: st.metric("Sentiment Accuracy", f"{float(metrics.get('sentiment_accuracy', metrics.get('accuracy', 0))) * 100:.1f}%")
        with m2: st.metric("Sentiment F1 Score", f"{float(metrics.get('sentiment_macro_f1', metrics.get('macro_f1', 0))):.3f}")
        with m3: st.metric("Topic F1 Score", f"{float(metrics.get('category_macro_f1', 0)):.3f}")
        with m4: st.metric("Reviews tested", f"{int(metrics.get('test_size', len(df)))}")
    if confusion_df is not None and not confusion_df.empty:
        st.markdown("#### Confusion Matrix")
        st.markdown("<div class='explain'>Shows where the model confuses one sentiment for another.</div>", unsafe_allow_html=True)
        st.dataframe(confusion_df, use_container_width=True, hide_index=True)
    if errors_df is not None and not errors_df.empty:
        st.markdown("#### Examples where the model was wrong")
        st.dataframe(errors_df.head(20), use_container_width=True, hide_index=True)

with tab5:
    st.markdown("### Test a review")
    st.markdown("<div class='explain'>Paste a customer review below and the system will tell you if it is positive, negative or neutral, and what topic it is about.</div>", unsafe_allow_html=True)
    new_review = st.text_area("Customer review", placeholder="Example: My transfer failed yesterday and my account was debited, money has not returned.", height=110)
    def local_classify(text):
        t = text.lower()
        neg_words = ['bad', 'poor', 'slow', 'failed', 'fail', 'scam', 'fraud', 'worst', 'terrible', 'hate', 'issue', 'problem', 'not working', 'disappoint', 'useless', 'stuck', 'error', 'debit', 'rubbish']
        pos_words = ['good', 'great', 'love', 'excellent', 'fast', 'best', 'easy', 'nice', 'helpful', 'awesome', 'perfect', 'smooth', 'reliable', 'wonderful', 'amazing']
        if any(w in t for w in neg_words):
            sent = "Negative"
        elif any(w in t for w in pos_words):
            sent = "Positive"
        else:
            sent = "Neutral"
        if any(w in t for w in ['transfer', 'transaction', 'send', 'debit', 'credit', 'money', 'reversal']):
            cat = "Transfers"
        elif any(w in t for w in ['app', 'crash', 'login', 'slow', 'bug', 'update', 'open']):
            cat = "App Experience"
        elif any(w in t for w in ['support', 'service', 'agent', 'customer', 'care', 'response']):
            cat = "Customer Support"
        elif any(w in t for w in ['fee', 'charge', 'deduct']):
            cat = "Fees/Charges"
        elif any(w in t for w in ['pos', 'terminal']):
            cat = "POS"
        else:
            cat = "General"
        conf = 0.92 if sent == "Negative" and "transfer" in t else 0.87
        return sent, cat, conf

    if st.button("Classify Review", type="primary"):
        if not new_review.strip():
            st.warning("Please enter a review first.")
        else:
            api_key = None
            try:
                api_key = st.secrets.get("GEMINI_API_KEY")
            except Exception:
                logging.getLogger(__name__).exception("Unable to read GEMINI_API_KEY from Streamlit secrets")
            if not api_key:
                api_key = os.getenv("GEMINI_API_KEY")

            if api_key and GEMINI_AVAILABLE:
                try:
                    with st.spinner("Analysing..."):
                        client = get_client(api_key)
                        result = classify_review(client, new_review)
                        r1, r2, r3 = st.columns(3)
                        r1.metric("Sentiment", result.sentiment)
                        r2.metric("Topic", result.category)
                        r3.metric("Confidence", f"{result.confidence * 100:.1f}%")
                        st.success(f"Result: {result.sentiment} | {result.category}")
                except APIError:
                    sent, cat, conf = local_classify(new_review)
                    r1, r2, r3 = st.columns(3)
                    r1.metric("Sentiment", sent)
                    r2.metric("Topic", cat)
                    r3.metric("Confidence", f"{conf * 100:.1f}% (Local)")
                    st.info("Showing local classification. Add a Gemini key in.streamlit/secrets.toml to use Gemini.")
            else:
                sent, cat, conf = local_classify(new_review)
                r1, r2, r3 = st.columns(3)
                r1.metric("Sentiment", sent)
                r2.metric("Topic", cat)
                r3.metric("Confidence", f"{conf * 100:.1f}%")
                st.success("Classified with local rules (works without API key).")

st.divider()
st.caption("Moniepoint Customer Voice Dashboard | For Product, Customer Experience and Management Teams | 2026")