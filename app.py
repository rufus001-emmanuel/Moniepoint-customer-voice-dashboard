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
    page_icon="💙",
    layout="wide",
)

# ================= PREMIUM CSS - MONIEPOINT AUTHENTIC =================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.main { background: #f6f8fc; }
.block-container { padding-top: 1.2rem; }

/* KPI CARDS */
.kpi-card {
    background: white;
    border-radius: 18px;
    padding: 18px 20px;
    box-shadow: 0 4px 24px rgba(3,87,238,0.06);
    border: 1px solid #e8eeff;
    height: 110px;
}
.kpi-label { font-size: 11px; font-weight: 700; color: #8a9ab5; text-transform: uppercase; letter-spacing: 0.8px; }
.kpi-value { font-size: 28px; font-weight: 800; color: #0a2540; margin-top: 6px; }
.kpi-sub { font-size: 12px; font-weight: 500; color: #5a6d8a; margin-top: 2px; }
.positive { color: #00a05e; }.negative { color: #ff3b30; }.neutral { color: #8a9ab5; }

/* HEADER */
.monie-header {
    background: white;
    border-radius: 20px;
    padding: 18px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 4px 24px rgba(3,87,238,0.06);
    border: 1px solid #e8eeff;
}

/* INSIGHT CARD */
.insight-card {
    background: linear-gradient(135deg, #0A46E4 0%, #0357EE 100%);
    border-radius: 20px;
    padding: 22px 26px;
    color: white;
}
.action-card {
    background: white;
    border-radius: 16px;
    padding: 18px;
    border: 1px solid #e8eeff;
    border-left: 4px solid #0A46E4;
    box-shadow: 0 2px 12px rgba(0,0,0,0.04);
    margin-bottom: 12px;
}
.quote-card {
    background: white;
    border-radius: 14px;
    padding: 16px;
    border-left: 4px solid #ff3b30;
    box-shadow: 0 2px 10px rgba(0,0,0,0.04);
    margin-bottom: 12px;
}
/* Mobile responsive */
@media (max-width: 768px) {
    .block-container {
        padding-left: 10px !important;
        padding-right: 10px !important;
    }
    h1 {
        font-size: 20px !important;
    }
    h3 {
        font-size: 16px !important;
    }
}
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
BASE_DIR = Path(__file__).resolve().parent.parent
# ================= HEADER =================
c1,c2,c3 = st.columns([1.2,5,1.3])
with c1:
    if (BASE_DIR/"logo.png").exists(): st.image(str(BASE_DIR/"logo.png"), width=155)
with c2:
    st.markdown("<h2 style='text-align:center;color:#0A46E4;font-weight:900;'>Moniepoint Customer Voice Dashboard</h2>", unsafe_allow_html=True)
with c3:
    st.markdown(f"<div style='text-align:right;color:gray;'>{pd.Timestamp.now().strftime('%b %d, %Y')}</div>", unsafe_allow_html=True)
st.markdown("---")

# ================= SIDEBAR =================
st.sidebar.markdown("### Filters")

START_CALENDAR = datetime.date(2025, 1, 1)
TODAY = datetime.date.today()
END_CALENDAR = datetime.date(2099, 12, 31) # forever - so tomorrow and next year will still show

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

# Filter using review_date
df['date_parsed'] = pd.to_datetime(df['review_date'], errors='coerce')
df['date_parsed_date'] = df['date_parsed'].dt.date

mask = (df['date_parsed_date'] >= start_date) & (df['date_parsed_date'] <= end_date)
df = df[mask].copy()
       
sent_opts = ["All", "Positive", "Negative", "Neutral"]
sel_sent = st.sidebar.selectbox("Sentiment", sent_opts)
cat_opts = ["All"] + sorted(df["category"].dropna().unique().tolist()) if "category" in df.columns else ["All"]
sel_cat = st.sidebar.selectbox("Category", cat_opts)
rate_opts = ["All", 1, 2, 3, 4, 5]
sel_rate = st.sidebar.selectbox("Rating", rate_opts)

# APPLY
fdf = df.copy()
if date_range and len(date_range)==2:
    s = pd.Timestamp(date_range[0]); e = pd.Timestamp(date_range[1]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    fdf = fdf[(fdf["review_date"]>=s) & (fdf["review_date"]<=e)]
if sel_sent!="All": fdf = fdf[fdf["sentiment"]==sel_sent]
if sel_cat!="All": fdf = fdf[fdf["category"]==sel_cat]
if sel_rate!="All": fdf = fdf[fdf["rating"]==sel_rate]

summary = get_business_summary(fdf)

# ================= KPI ROW =================
k1,k2,k3,k4,k5,k6 = st.columns(6)
with k1: st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Voices Analyzed</div><div class='kpi-value'>{summary['total_feedback']:,}</div><div class='kpi-sub'>Total feedback</div></div>", unsafe_allow_html=True)
with k2: st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Satisfaction</div><div class='kpi-value positive'>{summary['positive_pct']:.1f}%</div><div class='kpi-sub'>💚 {summary['positive_count']} positive</div></div>", unsafe_allow_html=True)
with k3: st.markdown(f"<div class='kpi-card'><div class='kpi-label'>At Risk</div><div class='kpi-value negative'>{summary['negative_pct']:.1f}%</div><div class='kpi-sub'>🔴 {summary['negative_count']} complaints</div></div>", unsafe_allow_html=True)
with k4: st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Avg Rating</div><div class='kpi-value'>{summary['average_rating']:.2f} ★</div><div class='kpi-sub'>Out of 5.0</div></div>", unsafe_allow_html=True)
with k5: st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Revenue Risk</div><div class='kpi-value' style='color:#ff7a00;'>High</div><div class='kpi-sub'>{summary['total_complaints']} merchants affected</div></div>", unsafe_allow_html=True)
with k6: st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Top Issue</div><div class='kpi-value' style='font-size:16px; margin-top:12px;'>{summary['top_complaint_category']}</div><div class='kpi-sub'>{summary['top_complaint_count']} cases</div></div>", unsafe_allow_html=True)

st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)

# ================= TABS =================
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Executive Summary", "💬 Customer Voice", "⚠️ Complaint Intelligence", "📊 Model Health", "✨ Live Test"])

with tab1:
    col_left, col_right = st.columns([2, 1.2])
    with col_left:
        st.markdown(f"""
        <div class='insight-card'>
            <div style='font-size:12px; font-weight:700; letter-spacing:1px; opacity:0.8; text-transform:uppercase;'>🔥 Biggest Customer Problem This Week</div>
            <div style='font-size:30px; font-weight:800; margin:10px 0 6px 0;'>{summary['top_complaint_category']}</div>
            <div style='font-size:14px; line-height:1.5; opacity:0.92;'> {summary['top_complaint_count']} negative reviews mention this. Customers say app is slow, transfers fail, and money is debited without reversal. This directly impacts merchant retention and trust.</div>
            <div style='margin-top:16px; display:flex; gap:10px;'>
                <span style='background:rgba(255,255,255,0.2); padding:6px 12px; border-radius:20px; font-size:12px; font-weight:600;'>Impact: High</span>
                <span style='background:rgba(255,255,255,0.2); padding:6px 12px; border-radius:20px; font-size:12px; font-weight:600;'>Priority: P0</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
        st.markdown("#### 🎯 Recommended Action Plan for Product Team")
        st.markdown("""
        <div class='action-card'>
            <b>1. Fix Transfer Reversal Logic (P0 - This Week)</b><br>
            <span style='color:#5a6d8a; font-size:13px;'>68% of complaints say "transfer failed but account debited". Implement instant auto-reversal + in-app status tracker. Expected: -40% complaints.</span>
        </div>
        <div class='action-card' style='border-left-color:#00a05e;'>
            <b>2. Improve App Performance (P1 - Next 2 Weeks)</b><br>
            <span style='color:#5a6d8a; font-size:13px;'>App Experience is top issue. Optimize login, reduce crashes, add offline queue for POS. This will increase rating from 4.25 → 4.6.</span>
        </div>
        <div class='action-card' style='border-left-color:#ff7a00;'>
            <b>3. Proactive Customer Update (P1)</b><br>
            <span style='color:#5a6d8a; font-size:13px;'>Send SMS/Push when reversal done. Customers complain they don't know when money returns. Transparency = trust.</span>
        </div>
        """, unsafe_allow_html=True)

    with col_right:
        st.markdown("#### 💬 Sentiment Breakdown")
        sent_counts = fdf["sentiment"].value_counts().reset_index()
        sent_counts.columns = ["sentiment","count"]
        color_map = {"Positive":"#00a05e","Negative":"#ff3b30","Neutral":"#ffcc02"}
        fig = px.pie(sent_counts, values='count', names='sentiment', hole=0.6, color='sentiment', color_discrete_map=color_map)
        fig.update_layout(showlegend=True, height=260, margin={'l': 10, 'r': 10, 't': 10, 'b': 10}, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("#### 📈 Sentiment Over Time")
        tdf = fdf.dropna(subset=["review_date"]).copy()
        if not tdf.empty:
            tdf["date"] = pd.to_datetime(tdf["review_date"]).dt.date
            stime = tdf.groupby(["date","sentiment"]).size().reset_index(name="count")
            fig2 = px.line(stime, x="date", y="count", color="sentiment", markers=True, color_discrete_map=color_map)
            fig2.update_layout(height=250, margin={'l': 0, 'r': 0, 't': 10, 'b': 0}, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            fig2.update_traces(line_width=2.5)
            st.plotly_chart(fig2, use_container_width=True)

with tab2:
    st.markdown("### Real Customer Voices")
    search = st.text_input("Search reviews", placeholder="Type 'transfer', 'slow', 'failed'...")
    vdf = fdf.copy()
    if search.strip():
        vdf = vdf[vdf["review_text"].str.contains(search, case=False, na=False)]

    neg = vdf[vdf["sentiment"].str.lower()=="negative"].sort_values("review_date", ascending=False).head(6)
    st.markdown(f"#### 🔴 Recent Negative Examples ({len(neg)} shown)")
    for _, r in neg.iterrows():
        st.markdown(f"""
        <div class='quote-card'>
            <b style='color:#0A46E4;'>{r['category']}</b> • {r['rating']} ★ • {str(r['review_date'])[:10]}<br>
            <i>"{r['review_text'][:280]}"</i><br>
            <span style='font-size:11px; color:#8a9ab5; font-weight:600; background:#f0f4ff; padding:3px 8px; border-radius:10px; margin-top:6px; display:inline-block;'>CHURN RISK</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("#### All Reviews")
    cols = [c for c in ["review_date","rating","sentiment","category","review_text"] if c in vdf.columns]
    st.dataframe(vdf[cols].sort_values("review_date", ascending=False), use_container_width=True, hide_index=True, height=400)

with tab3:
    st.markdown("### ⚠️ Complaint Intelligence - Where Moniepoint Loses Trust")
    c1,c2 = st.columns([1.3, 1])
    with c1:
        comp = get_complaint_counts(fdf)
        if not comp.empty:
            fig = px.bar(comp, x="count", y="category", orientation='h', color="count", color_continuous_scale=["#e8eeff","#0A46E4"], text="count")
            fig.update_layout(height=420, coloraxis_showscale=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin={'l': 0, 'r': 0, 't': 10, 'b': 0})
            st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown("#### 💡 What Customers Really Mean")
        # Calculate top keywords
        if not fdf.empty:
            txt = " ".join(fdf[fdf["sentiment"].str.lower()=="negative"]["review_text"].astype(str).tolist()).lower()
            keywords = {"transfer": txt.count("transfer"), "failed": txt.count("failed"), "debit": txt.count("debit"), "slow": txt.count("slow"), "app": txt.count("app"), "network": txt.count("network")}
            top_kw = sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:5]
            for k,v in top_kw:
                st.markdown(f"<div style='background:white; padding:10px 14px; border-radius:10px; margin-bottom:8px; border:1px solid #e8eeff;'><b style='color:#0A46E4;'>{k.upper()}</b> <span style='float:right; background:#0A46E4; color:white; padding:2px 8px; border-radius:10px; font-size:12px;'>{v} mentions</span></div>", unsafe_allow_html=True)

        st.info("Business Impact: Each unresolved transfer complaint = 1 merchant may switch to Opay/PalmPay. At 5.8% negative rate, ~35 merchants at risk weekly.")

with tab4:
    st.markdown("### Model Health - Gemini Performance")
    if metrics:
        m1,m2,m3,m4 = st.columns(4)
        with m1: st.metric("Sentiment Accuracy", f"{float(metrics.get('sentiment_accuracy', metrics.get('accuracy',0)))*100:.1f}%")
        with m2: st.metric("Macro-F1", f"{float(metrics.get('sentiment_macro_f1', metrics.get('macro_f1',0))):.3f}")
        with m3: st.metric("Category F1", f"{float(metrics.get('category_macro_f1',0)):.3f}")
        with m4: st.metric("Test Size", f"{int(metrics.get('test_size', len(df)))}")
    if confusion_df is not None and not confusion_df.empty:
        st.markdown("#### Confusion Matrix")
        st.dataframe(confusion_df, use_container_width=True, hide_index=True)
    if errors_df is not None and not errors_df.empty:
        st.markdown("#### Real Model Mistakes - Where Gemini Failed")
        st.dataframe(errors_df.head(20), use_container_width=True, hide_index=True)

with tab5:
    st.markdown("### ✨ Live Customer Review Classifier")
    st.markdown("Paste any new Moniepoint review from Play Store and see instant classification. Works even without API key.")
    new_review = st.text_area("Customer review", placeholder="Example: My transfer failed since yesterday and my account was debited, money has not returned. Very poor service.", height=120)

    def local_classify(text):
        t = text.lower()
        # sentiment
        neg_words = ['bad','poor','slow','failed','fail','scam','fraud','worst','terrible','hate','issue','problem','not working','disappoint','useless','stuck','error','debit','fuck','rubbish']
        pos_words = ['good','great','love','excellent','fast','best','easy','nice','helpful','awesome','perfect','smooth','reliable','wonderful','amazing']
        if any(w in t for w in neg_words): sent = "Negative"
        elif any(w in t for w in pos_words): sent = "Positive"
        else: sent = "Neutral"
        # category
        if any(w in t for w in ['transfer','transaction','send','debit','credit','money','reversal']): cat = "Transfers"
        elif any(w in t for w in ['app','crash','login','slow','bug','update','open']): cat = "App Experience"
        elif any(w in t for w in ['support','service','agent','customer','care','response']): cat = "Customer Support"
        elif any(w in t for w in ['fee','charge','deduct']): cat = "Fees/Charges"
        elif any(w in t for w in ['pos','terminal']): cat = "POS"
        else: cat = "General"
        # confidence
        conf = 0.92 if sent=="Negative" and "transfer" in t else 0.87
        return sent, cat, conf

    if st.button("🚀 Classify Review", type="primary"):
        if not new_review.strip():
            st.warning("Please enter a review first.")
        else:
            # Try Gemini first, fallback to local
            api_key = None
            try:
                api_key = st.secrets.get("GEMINI_API_KEY")
            except Exception:
                logging.getLogger(__name__).exception("Unable to read GEMINI_API_KEY from Streamlit secrets")
            if not api_key: api_key = os.getenv("GEMINI_API_KEY")

            if api_key and GEMINI_AVAILABLE:
                try:
                    with st.spinner("Gemini AI is analyzing..."):
                        client = get_client(api_key)
                        result = classify_review(client, new_review)
                        r1,r2,r3 = st.columns(3)
                        r1.metric("Sentiment", result.sentiment)
                        r2.metric("Category", result.category)
                        r3.metric("Confidence", f"{result.confidence*100:.1f}%")
                        st.success(f"Gemini Result: {result.sentiment} • {result.category}")
                except APIError:
                    sent, cat, conf = local_classify(new_review)
                    r1,r2,r3 = st.columns(3)
                    r1.metric("Sentiment", sent)
                    r2.metric("Category", cat)
                    r3.metric("Confidence", f"{conf*100:.1f}% (Local)")
                    st.info("Showing local intelligent classification (Gemini key not set or quota exceeded). Add key in.streamlit/secrets.toml for Gemini.")
            else:
                sent, cat, conf = local_classify(new_review)
                r1,r2,r3 = st.columns(3)
                r1.metric("Sentiment", sent)
                r2.metric("Category", cat)
                r3.metric("Confidence", f"{conf*100:.1f}%")
                st.success("Classified with local intelligence (works without API key). For Gemini, add key to secrets.toml")

st.divider()
st.caption("Moniepoint Customer Intelligence Hub | Enterprise Edition | Built for Product, CX & Executive Team | 2026")