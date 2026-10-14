from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

try:
    from data_utils import normalize_reviews  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - graceful fallback for local execution
    def normalize_reviews(df):
        out = df.copy()
        for col in ["review_id", "review_text", "rating", "review_date", "userName"]:
            if col not in out:
                out[col] = ""
        out["review_text_original"] = out.get("review_text", "").fillna("")
        out["review_text_english"] = out.get("review_text", "").fillna("")
        out["sentiment"] = ""
        out["complaint_category"] = ""
        return out

st.set_page_config(page_title="Moniepoint Customer Voice Dashboard", page_icon="M", layout="wide", initial_sidebar_state="expanded")
BLUE="#0755E9"; NAVY="#0A1D55"; GREEN="#078F72"; YELLOW="#F3BD20"; RED="#EF4056"; MUTED="#637493"
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] {{font-family:Inter,Arial,sans-serif;}}
.stApp {{background:#F5F8FD; color:{NAVY};}}
.block-container {{padding-top:1rem;padding-bottom:2rem;max-width:1600px;}}
[data-testid="stSidebar"] {{background:linear-gradient(180deg,#064DE0 0%,#0739B4 100%);}}
[data-testid="stSidebar"] * {{color:white !important;}}
[data-testid="stSidebar"] [data-testid="stFileUploader"] {{background:#ffffff18;border:1px solid #ffffff55;border-radius:10px;padding:8px;}}
[data-testid="stMetric"] {{background:white;border:1px solid #DFE7F3;border-radius:13px;padding:15px 16px;min-height:112px;box-shadow:0 2px 8px #183c6a08;}}
[data-testid="stMetricLabel"] p {{font-size:12px;color:#526483 !important;}}
[data-testid="stMetricValue"] {{color:{NAVY};font-weight:800;}}
h1,h2,h3 {{color:{NAVY};}}
div[data-testid="stTabs"] button {{font-weight:600;}}
.panel {{background:white;border:1px solid #DFE7F3;border-radius:14px;padding:16px 18px;margin-bottom:12px;}}
.subtle {{color:{MUTED};font-size:12px;}}
.kicker {{font-size:12px;color:{MUTED};font-weight:600;letter-spacing:.04em;text-transform:uppercase;}}
</style>
""", unsafe_allow_html=True)

# Sidebar / file loading
st.sidebar.markdown("<div style='font-size:25px;font-weight:800;line-height:1.2'>▣ Moniepoint</div><div style='font-size:10px;letter-spacing:2px;margin-top:5px;opacity:.85'>CUSTOMER VOICE</div>", unsafe_allow_html=True)
st.sidebar.markdown("---")
page=st.sidebar.radio("NAVIGATION",["Dashboard","Customer Feedback","Complaints by Topic","Model Health","Test & Review"],label_visibility="visible")
st.sidebar.markdown("---")
st.sidebar.markdown("### ▽ Filters")
up=st.sidebar.file_uploader("Upload your current CSV",type=["csv"],help="Expected columns: review_id, review_text, rating, review_date, userName")
if up is not None:
    try:
        raw=pd.read_csv(up)
        source=f"Uploaded file: {up.name}"
        st.session_state["last_uploaded_csv_name"]=up.name
    except (pd.errors.EmptyDataError, pd.errors.ParserError, ValueError, TypeError, OSError) as e:
        st.error(f"Could not read CSV: {e}"); st.stop()
else:
    default_path=Path("data/moniepoint_reviews.csv")
    if default_path.exists() and default_path.stat().st_size>10:
        raw=pd.read_csv(default_path); source=str(default_path)
    else:
        raw=pd.DataFrame(); source="No file loaded"

if raw.empty:
    st.title("Moniepoint Customer Voice")
    st.markdown("### Understand your customers. Identify problems. Improve their experience.")
    st.info("Upload your existing CSV in the blue sidebar to populate the dashboard. The data you pasted in chat appears to stop partway through a row, so this project does not pretend that partial text is your complete dataset.")
    st.markdown("#### Quick setup")
    st.write("1. Click **Browse files** in the left sidebar.  2. Select your complete CSV.  3. The charts and figures will calculate from those rows automatically.")
    st.stop()

# Normalize and derive useful fields from the real uploaded data
df=normalize_reviews(raw)
df["rating"]=pd.to_numeric(df["rating"],errors="coerce")
df["review_date"]=pd.to_datetime(df["review_date"],errors="coerce")
for c in ["review_text_original","review_text_english","sentiment","complaint_category","userName"]:
    if c not in df: df[c]=""
    df[c]=df[c].fillna("").astype(str)
df["display_text"]=df["review_text_english"].where(df["review_text_english"].str.strip().ne(""),df["review_text_original"])
# Transparent baseline sentiment: use an existing valid label first; otherwise use rating bands.
def sentiment(row):
    s=str(row.get("sentiment","")).strip().title()
    if s in {"Positive","Neutral","Negative"}: return s
    r=row.get("rating")
    if pd.isna(r): return "Unclassified"
    return "Positive" if r>=4 else ("Neutral" if r==3 else "Negative")
df["sentiment_display"]=df.apply(sentiment,axis=1)
# Keyword topic fallback, clearly identified as preliminary, used only where topic absent.
TOPICS=[
 ("Failed Transfer",["transfer","transaction","withdraw","not going through","send money","declining"]),
 ("Account Issues",["account","lien","debited","negative balance","balance","money is showing","can't use my money","cant use my money"]),
 ("Login / Access",["access my account","can't access","cant access","login","log in","pin","biometric"]),
 ("KYC / Verification",["verify","verification","upgrade my account","upgrade me","kyc"]),
 ("App Experience",["slow","download","update my app","app is","network","not working","keeps saying update"]),
 ("Customer Support",["customer service","customer support","support are","support didn't","support did not"]),
 ("Fees / Charges",["charge","charges","stamp duty","fee","fees"]),
 ("Card / Payments",["card","airtime","data","cashback","loan"]),
 ("Security / Fraud",["fraud","scam","security","secure"]),
]
def topic(text):
    t=str(text).lower()
    for label, words in TOPICS:
        if any(w in t for w in words): return label
    return "Other"
existing=df["complaint_category"].str.strip().ne("")
df.loc[~existing,"complaint_category"]=df.loc[~existing,"display_text"].map(topic)
# Define potential complaint using existing flag if available; otherwise negative sentiment or topic-specific issue wording.
if "is_complaint" not in df: df["is_complaint"]=""
def complaint(row):
    x=str(row.get("is_complaint","")).strip().lower()
    if x in {"true","1","yes","y"}: return True
    if x in {"false","0","no","n"}: return False
    return row["sentiment_display"]=="Negative" or (row["complaint_category"]!="Other" and row["rating"]<=3 if pd.notna(row["rating"]) else False)
df["potential_complaint"]=df.apply(complaint,axis=1)

# Real filters
filtered=df.copy()
valid_dates=df["review_date"].dropna()
if len(valid_dates):
    min_d,max_d=valid_dates.min().date(),valid_dates.max().date()
    date_range=st.sidebar.date_input("Date range",value=(min_d,max_d),min_value=min_d,max_value=max_d)
    if isinstance(date_range,(tuple,list)) and len(date_range)==2:
        filtered=filtered[filtered["review_date"].dt.date.between(date_range[0],date_range[1])]
segment=st.sidebar.selectbox("Customer segment",["All","Positive","Neutral","Negative"])
if segment!="All": filtered=filtered[filtered["sentiment_display"]==segment]
feedback_type=st.sidebar.selectbox("Feedback type",["All","Potential complaints","Non-complaints"])
if feedback_type=="Potential complaints": filtered=filtered[filtered["potential_complaint"]]
elif feedback_type=="Non-complaints": filtered=filtered[~filtered["potential_complaint"]]
rating_options=sorted([int(x) for x in filtered["rating"].dropna().unique() if 1<=x<=5])
selected_ratings=st.sidebar.multiselect("Star rating",rating_options,default=rating_options)
if selected_ratings: filtered=filtered[filtered["rating"].isin(selected_ratings)]
elif rating_options: filtered=filtered.iloc[0:0]
st.sidebar.markdown("---")
st.sidebar.caption(f"Data source: {source}")
st.sidebar.caption(f"{len(df):,} unique rows loaded")

# Header
header_left,header_right=st.columns([3,1])
with header_left:
    st.markdown("<div class='kicker'>MONIEPOINT · CUSTOMER EXPERIENCE ANALYTICS</div>",unsafe_allow_html=True)
    st.title("Customer Voice Dashboard")
    st.caption("Understand your customers. Identify problems. Improve their experience.")
with header_right:
    st.markdown(f"<div style='text-align:right;padding-top:14px;color:{MUTED};font-size:12px'>CSV ANALYSIS MODE<br><b style='color:{NAVY}'>Not connected to live reviews</b></div>",unsafe_allow_html=True)
st.markdown("<div class='panel'><b>How to use this dashboard</b><br><span class='subtle'>Start with the numbers at the top. Use the tabs to explore customer feedback, complaint topics, and data quality. Filters on the left update the figures and charts.</span></div>",unsafe_allow_html=True)

# KPIs computed from filtered rows; no invented previous-period percentages
n=len(filtered); pos=int((filtered.sentiment_display=="Positive").sum()); neu=int((filtered.sentiment_display=="Neutral").sum()); neg=int((filtered.sentiment_display=="Negative").sum()); complaints=int(filtered.potential_complaint.sum())
avg=filtered.rating.mean() if filtered.rating.notna().any() else None
neg_topics=filtered.loc[filtered.potential_complaint,"complaint_category"].value_counts()
top_topic=neg_topics.index[0] if len(neg_topics) else "Not identified"
cols=st.columns(6)
cols[0].metric("Total Feedback",f"{n:,}",help="Number of rows matching the current filters")
cols[1].metric("Happy Customers",f"{(pos/n):.1%}" if n else "—",f"{pos:,} positive reviews")
cols[2].metric("Unhappy Customers",f"{(neg/n):.1%}" if n else "—",f"{neg:,} negative reviews")
cols[3].metric("Average Rating",f"{avg:.2f} / 5" if avg is not None else "—")
cols[4].metric("Potential Complaints",f"{complaints:,}",help="Rule-based estimate unless is_complaint was supplied in the data")
cols[5].metric("Biggest Complaint",top_topic,help="Most frequent topic among potential complaints")

if page=="Dashboard":
    st.markdown("#### Overview")
    left,right=st.columns([1.45,1])
    with left:
        st.markdown("<div class='panel'>",unsafe_allow_html=True); st.subheader("Customer Feedback Trend")
        trend=filtered.dropna(subset=["review_date"]).copy()
        if not trend.empty:
            span=(trend.review_date.max()-trend.review_date.min()).days
            trend["Period"]=trend.review_date.dt.strftime("%Y-%m-%d") if span<=14 else trend.review_date.dt.to_period("M").astype(str)
            tg=trend.groupby(["Period","sentiment_display"]).size().reset_index(name="Reviews")
            fig=px.line(tg,x="Period",y="Reviews",color="sentiment_display",markers=True,color_discrete_map={"Positive":GREEN,"Neutral":YELLOW,"Negative":RED,"Unclassified":"#9AA7BA"})
            fig.update_layout(height=300,margin={"l": 5, "r": 5, "t": 5, "b": 5},paper_bgcolor="white",plot_bgcolor="white",legend_title_text="",xaxis_title="",yaxis_title="Reviews",font_color=NAVY)
            st.plotly_chart(fig,use_container_width=True)
        else: st.info("No usable dates in the current selection.")
        st.markdown("</div>",unsafe_allow_html=True)
    with right:
        st.markdown("<div class='panel'>",unsafe_allow_html=True); st.subheader("Customer Sentiment")
        sc=filtered["sentiment_display"].value_counts().reindex(["Positive","Neutral","Negative","Unclassified"],fill_value=0).reset_index(); sc.columns=["Sentiment","Reviews"]; sc=sc[sc.Reviews>0]
        if not sc.empty:
            fig=px.pie(sc,names="Sentiment",values="Reviews",hole=.63,color="Sentiment",color_discrete_map={"Positive":GREEN,"Neutral":YELLOW,"Negative":RED,"Unclassified":"#9AA7BA"})
            fig.update_layout(height=300,margin={"l": 0, "r": 0, "t": 5, "b": 5},paper_bgcolor="white",legend_title_text="")
            st.plotly_chart(fig,use_container_width=True)
        else: st.info("No reviews match the filters.")
        st.markdown("</div>",unsafe_allow_html=True)
    a,b=st.columns([1,1.45])
    with a:
        st.markdown("<div class='panel'>",unsafe_allow_html=True); st.subheader("Top Complaint Categories")
        cat=filtered.loc[filtered.potential_complaint,"complaint_category"].value_counts().head(7).rename_axis("Category").reset_index(name="Reviews")
        if cat.empty: st.info("No potential complaints match the current filters.")
        else:
            fig=px.bar(cat,x="Reviews",y="Category",orientation="h",text="Reviews",color_discrete_sequence=[BLUE]); fig.update_layout(height=285,margin={"l": 0, "r": 0, "t": 0, "b": 0},yaxis={"categoryorder":"total ascending"},paper_bgcolor="white",plot_bgcolor="white",xaxis_title="Reviews",yaxis_title="")
            st.plotly_chart(fig,use_container_width=True)
        st.markdown("</div>",unsafe_allow_html=True)
    with b:
        st.markdown("<div class='panel'>",unsafe_allow_html=True); st.subheader("Recent Customer Feedback")
        recent=filtered.sort_values("review_date",ascending=False,na_position="last").head(6)
        if recent.empty: st.info("No reviews match the current filters.")
        else:
            show=recent[[c for c in ["review_date","rating","sentiment_display","complaint_category","display_text"] if c in recent.columns]].copy()
            show["review_date"]=show["review_date"].dt.strftime("%b %d, %Y").fillna("")
            st.dataframe(show,use_container_width=True,hide_index=True,height=285)
        st.markdown("</div>",unsafe_allow_html=True)
    st.markdown("<div class='panel'><b>Quick Insights</b>",unsafe_allow_html=True)
    if n:
        st.write(f"• Positive: **{pos:,} ({pos/n:.1%})** · Neutral: **{neu:,} ({neu/n:.1%})** · Negative: **{neg:,} ({neg/n:.1%})**")
        st.write(f"• **{complaints:,}** reviews are currently flagged as potential complaints.")
        st.write(f"• Most frequent potential-complaint topic: **{top_topic}**.")
    else: st.write("No data matches the selected filters.")
    st.caption("No previous-period comparison is shown because this quick version does not invent comparison figures. All visible metrics are recalculated from the loaded CSV and active filters.")
    st.markdown("</div>",unsafe_allow_html=True)
elif page=="Customer Feedback":
    st.title("What Customers Are Saying")
    q=st.text_input("Search review text or customer name",placeholder="Try: transfer, account, slow, customer support…")
    view=filtered.copy()
    if q.strip():
        mask=view["display_text"].str.contains(q.strip(),case=False,na=False,regex=False) | view["userName"].str.contains(q.strip(),case=False,na=False,regex=False)
        view=view[mask]
    st.caption(f"Showing {len(view):,} reviews")
    show=view[[c for c in ["review_id","review_date","userName","rating","sentiment_display","complaint_category","display_text"] if c in view.columns]].sort_values("review_date",ascending=False,na_position="last")
    st.dataframe(show,use_container_width=True,hide_index=True)
    st.download_button("Download filtered feedback CSV",view.to_csv(index=False).encode("utf-8-sig"),"moniepoint_filtered_feedback.csv","text/csv")
elif page=="Complaints by Topic":
    st.title("Complaints by Topic")
    st.caption("Complaint flags and topics are rule-based estimates unless supplied by an earlier classifier. Review them before treating them as verified findings.")
    view=filtered[filtered.potential_complaint].copy()
    topics=view["complaint_category"].value_counts().rename_axis("Topic").reset_index(name="Count")
    l,r=st.columns([1,1.4])
    with l: st.subheader("Topic distribution"); st.dataframe(topics,use_container_width=True,hide_index=True)
    with r: st.subheader("Complaint review details"); st.dataframe(view[[c for c in ["review_date","rating","userName","complaint_category","display_text"] if c in view.columns]].sort_values("review_date",ascending=False,na_position="last"),use_container_width=True,hide_index=True)
    st.download_button("Download potential complaints CSV",view.to_csv(index=False).encode("utf-8-sig"),"moniepoint_potential_complaints.csv","text/csv")
elif page=="Model Health":
    st.title("Model Health & Data Quality")
    total=len(df)
    checks=[("Rows loaded",total),("Unique review IDs",df.loc[df.review_id.astype(str).str.strip().ne(""),"review_id"].nunique()),("Rows with review text",int(df.display_text.str.strip().ne("").sum())),("Rows with valid dates",int(df.review_date.notna().sum())),("Rows with valid 1–5 ratings",int(df.rating.between(1,5).sum())),("Existing sentiment labels",int(df.sentiment.isin(["Positive","Neutral","Negative"]).sum())),("Existing topic labels",int(df.complaint_category.str.strip().ne("").sum()))]
    st.dataframe(pd.DataFrame(checks,columns=["Check","Result"]),use_container_width=True,hide_index=True)
    st.info("This quick-start uses rating-based sentiment when no valid sentiment label exists and keyword-based complaint topics when no topic is provided. Gemini is not called automatically in this presentation version.")
    st.download_button("Download normalized data",df.to_csv(index=False).encode("utf-8-sig"),"moniepoint_normalized_reviews.csv","text/csv")
elif page=="Test & Review":
    st.title("Test & Review")
    st.write("Run basic checks on the dataset loaded into the dashboard.")
    if st.button("Run data validation",type="primary"):
        checks={"Dataset is loaded":len(df)>0,"Review text column is available":"display_text" in df.columns,"Ratings are within 1–5":bool(df.rating.dropna().between(1,5).all()),"Dates parsed":bool(df.review_date.notna().any()),"Review IDs have no duplicates":bool(df.loc[df.review_id.astype(str).str.strip().ne(""),"review_id"].duplicated().sum()==0)}
        for label,passed in checks.items(): st.success(f"PASS — {label}") if passed else st.warning(f"CHECK — {label}")
        st.caption("These are local data validation tests, not live API or live Play Store connection tests.")
    st.markdown("#### Preview")
    st.dataframe(df.head(20)[[c for c in ["review_id","review_date","rating","sentiment_display","complaint_category","display_text"] if c in df.columns]],use_container_width=True,hide_index=True)

st.markdown("<div style='text-align:center;color:#8190A9;font-size:11px;padding:20px 0 0'>MONIEPOINT CUSTOMER VOICE · PRESENTATION BUILD · CSV-BASED ANALYSIS</div>",unsafe_allow_html=True)
