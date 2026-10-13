from datetime import date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------
# MoneyPoint | Customer Voice Dashboard
# ---------------------------------------------------------

st.set_page_config(
    page_title="MoneyPoint | Customer Voice",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Theme ----------
BG = "#F5F8F7"
GREEN = "#087F5B"
DARK_GREEN = "#082D26"
MINT = "#E4F5EE"
TEXT = "#152238"
MUTED = "#64748B"
BORDER = "#E2E8F0"
AMBER = "#F59E0B"
RED = "#EF4444"
BLUE = "#6479E8"

st.markdown(
    f"""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
      html, body, [class*="css"] {{ font-family: Inter, sans-serif; }}
     .stApp {{ background: {BG}; color: {TEXT}; }}
      [data-testid="stHeader"] {{ background: rgba(245,248,247,.92); }}
      [data-testid="stSidebar"] {{ background: {DARK_GREEN}; }}
      [data-testid="stSidebar"] * {{ color: #F8FAFC; }}
      [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{ color: #D7E6E1; }}
      [data-testid="stSidebar"] hr {{ border-color: #285047; }}
     .block-container {{ max-width: 1600px; padding-top: 1.25rem; padding-bottom: 2rem; }}
     .brand {{ display:flex; align-items:center; gap:11px; padding: 8px 0 22px 0; }}
     .brand-mark {{ width:42px; height:42px; border-radius:13px; display:flex; align-items:center; justify-content:center; background:#0D8D65; color:white; font-size:23px; font-weight:800; }}
     .brand-name {{ font-size:22px; font-weight:800; letter-spacing:-.6px; color:#fff; line-height:1.1; }}
     .brand-sub {{ color:#7FE0B5; font-size:12px; margin-top:4px; }}
     .side-section {{ color:#91B8AC; text-transform:uppercase; letter-spacing:1.1px; font-size:10px; font-weight:700; margin:18px 0 8px 0; }}
     .page-title {{ font-size:29px; font-weight:800; letter-spacing:-.8px; color:{TEXT}; margin:0; }}
     .page-subtitle {{ font-size:13px; color:{MUTED}; margin-top:5px; }}
     .eyebrow {{ font-size:11px; color:{MUTED}; font-weight:700; letter-spacing:.7px; text-transform:uppercase; }}
     .help-banner {{ background:#E8F6F0; border:1px solid #C8E9DB; border-radius:13px; padding:15px 18px; margin:17px 0 18px 0; display:flex; gap:13px; align-items:center; }}
     .help-icon {{ min-width:42px; height:42px; border-radius:50%; display:flex; align-items:center; justify-content:center; background:{DARK_GREEN}; color:#fff; font-size:20px; }}
     .help-title {{ color:{TEXT}; font-size:14px; font-weight:700; margin-bottom:3px; }}
     .help-copy {{ color:#405B54; font-size:12px; line-height:1.6; }}
     .metric-card {{ background:white; border:1px solid {BORDER}; border-radius:13px; padding:15px 16px 13px 16px; min-height:145px; box-shadow:0 2px 7px rgba(15,23,42,.025); }}
     .metric-head {{ display:flex; align-items:center; gap:8px; color:#475569; font-size:11px; font-weight:600; }}
     .metric-icon {{ width:32px; height:32px; border-radius:11px; display:flex; align-items:center; justify-content:center; font-size:16px; }}
     .metric-value {{ font-size:29px; line-height:1.25; font-weight:800; letter-spacing:-.7px; color:{TEXT}; margin-top:8px; }}
     .metric-note {{ font-size:11px; color:{MUTED}; margin-top:2px; }}
     .metric-change {{ font-size:11px; font-weight:700; margin-top:8px; color:{GREEN}; }}
     .panel {{ background:white; border:1px solid {BORDER}; border-radius:13px; padding:17px 18px; box-shadow:0 2px 7px rgba(15,23,42,.025); }}
     .panel-title {{ font-size:15px; color:{TEXT}; font-weight:750; margin:0 0 2px 0; }}
     .panel-subtitle {{ font-size:11px; color:{MUTED}; margin-bottom:12px; }}
     .complaint-label {{ font-size:11px; color:#334155; }}
[13/10/2026 09:13] Rufus: .complaint-count {{ font-size:11px; color:{TEXT}; font-weight:700; text-align:right; }}
     .feedback-text {{ color:#334155; font-size:11px; line-height:1.5; }}
     .feedback-date {{ color:{MUTED}; font-size:10px; margin-top:4px; }}
     .rating {{ color:{AMBER}; letter-spacing:1px; white-space:nowrap; }}
     .insight {{ display:flex; gap:10px; padding:9px 0; border-bottom:1px solid #EEF2F6; }}
     .insight:last-child {{ border-bottom:0; }}
     .insight-bubble {{ width:31px; height:31px; min-width:31px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:15px; }}
     .insight-title {{ font-size:12px; font-weight:700; color:{TEXT}; }}
     .insight-copy {{ font-size:11px; color:{MUTED}; line-height:1.5; margin-top:3px; }}
      div[data-testid="stSelectbox"] label, div[data-testid="stDateInput"] label {{ font-size:12px; font-weight:600; }}
      div[data-testid="stSelectbox"] > div > div, div[data-testid="stDateInput"] input {{ border-radius:8px; }}
     .small-muted {{ color:{MUTED}; font-size:11px; }}
      @media (max-width: 900px) {{
       .page-title {{ font-size:23px; }}
       .metric-value {{ font-size:24px; }}
      }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Sample dataset ----------
feedback = pd.DataFrame(
    [
        {"date": "2026-10-12", "topic": "App Experience", "sentiment": "Positive", "rating": 5, "customer": "Customer 1048", "comment": "Great experience using the app. Super easy to navigate."},
        {"date": "2026-10-12", "topic": "Account Issues", "sentiment": "Negative", "rating": 2, "customer": "Customer 1021", "comment": "I'm having trouble with the login process. Please help."},
        {"date": "2026-10-11", "topic": "Transaction Delay", "sentiment": "Neutral", "rating": 4, "customer": "Customer 1092", "comment": "Transaction was delayed but customer support resolved it."},
        {"date": "2026-10-11", "topic": "Customer Support", "sentiment": "Positive", "rating": 5, "customer": "Customer 1007", "comment": "Very fast and reliable service. Keep it up!"},
        {"date": "2026-10-10", "topic": "App Experience", "sentiment": "Positive", "rating": 4, "customer": "Customer 1014", "comment": "The new app layout is much easier to use."},
        {"date": "2026-10-09", "topic": "Transaction Delay", "sentiment": "Negative", "rating": 1, "customer": "Customer 1033", "comment": "Transfer failed but my account was debited."},
        {"date": "2026-10-08", "topic": "Customer Support", "sentiment": "Positive", "rating": 5, "customer": "Customer 1060", "comment": "Support team handled my issue quickly."},
        {"date": "2026-10-07", "topic": "Account Issues", "sentiment": "Neutral", "rating": 3, "customer": "Customer 1042", "comment": "I need clearer steps to update my details."},
        {"date": "2026-10-06", "topic": "App Experience", "sentiment": "Positive", "rating": 5, "customer": "Customer 1088", "comment": "Smooth experience and quick navigation."},
        {"date": "2026-10-05", "topic": "Other", "sentiment": "Neutral", "rating": 3, "customer": "Customer 1074", "comment": "Please add more options to the dashboard."},
    ]
)
feedback["date"] = pd.to_datetime(feedback["date"])

# Overall headline figures
TOTAL_FEEDBACK = 600
HAPPY_PERCENT = 61.8
UNHAPPY_PERCENT = 6.8
AVERAGE_RATING = 4.25
TOTAL_COMPLAINTS = 41
positive_count = 371
neutral_count = 188
negative_count = 41

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown(
        """
        <div class="brand">
          <div class="brand-mark">M</div>
          <div>
            <div class="brand-name">MoneyPoint</div>
            <div class="brand-sub">Customer Voice</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="side-section">Workspace</div>', unsafe_allow_html=True)
    st.markdown("Dashboard")
    st.markdown("Feedback")
    st.markdown("Customers")
    st.markdown("Complaints")
    st.markdown("Reports")
    st.markdown("Settings")
    st.divider()
    st.markdown('<div class="side-section">Filters</div>', unsafe_allow_html=True)
    date_range = st.date_input(
        "Date range",
        value=(date(2025, 1, 1), date(2026, 10, 13)),
        min_value=date(2024, 1, 1),
        max_value=date(2026, 10, 13),
    )
    customer_segment = st.selectbox("Customer segment", ["All customers", "New customers", "Returning customers", "Premium customers"])
    feedback_type = st.selectbox("Feedback type", ["All feedback", "Positive", "Neutral", "Negative"])
    star_rating = st.selectbox("Star rating", ["All ratings", "5 stars", "4 stars", "3 stars", "2 stars", "1 star"])
    st.divider()
    st.markdown('<div class="small-muted">MoneyPoint · Customer Voice Dashboard<br>Analytics workspace</div>', unsafe_allow_html=True)

# Apply filters to the sample detail data.
filtered = feedback.copy()
if isinstance(date_range, tuple) and len(date_range) == 2:
    filtered = filtered[
        (filtered["date"].dt.date >= date_range[0]) &
        (filtered["date"].dt.date <= date_range[1])
    ]
if feedback_type!= "All feedback":
    filtered = filtered[filtered["sentiment"] == feedback_type]
if star_rating!= "All ratings":
    selected_rating = int(star_rating[0])
    filtered = filtered[filtered["rating"] == selected_rating]

# ---------- Header ----------
header_left, header_right = st.columns([3.3, 1.7], vertical_alignment="center")
with header_left:
    st.markdown('<div class="page-title">Customer Voice Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Customer feedback, sentiment and service quality at a glance.</div>', unsafe_allow_html=True)
with header_right:
    st.markdown(
        f'<div style="text-align:right;color:{MUTED};font-size:12px;padding-top:8px;">'
        f'<b style="color:{TEXT};">MoneyPoint Admin</b> &nbsp; · &nbsp; Updated Oct 13, 2026</div>',
        unsafe_allow_html=True,
    )

st.markdown(
    """
    <div class="help-banner">
      <div class="help-icon">i</div>
      <div>
        <div class="help-title">Dashboard guide</div>
        <div class="help-copy">Start with the summary metrics, then review customer sentiment and feedback trends. Use the filters on the left to narrow the date range, feedback type or star rating. Open the complaint and feedback sections to identify issues that need action.</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- KPI row ----------
metrics = [
    ("Total feedback", f"{TOTAL_FEEDBACK:,}", "Reviews analysed in this period", "Up 12% vs previous period", "#DDF6EA", GREEN),
    ("Happy customers", f"{HAPPY_PERCENT:.1f}%", f"{positive_count} positive reviews", "Up 8% vs previous period", "#DDF6EA", GREEN),
    ("Unhappy customers", f"{UNHAPPY_PERCENT:.1f}%", f"{negative_count} negative reviews", "Down 5% vs previous period", "#FEE8E8", RED),
    ("Average rating", f"{AVERAGE_RATING:.2f} / 5", "Average customer rating", "Up 0.2 vs previous period", "#FFF3D6", AMBER),
    ("Total complaints", f"{TOTAL_COMPLAINTS}", "Complaints to resolve", "Down 18% vs previous period", "#E8EAFE", BLUE),
    ("Biggest complaint", "App Experience", "15 complaints recorded", "36.6% of all complaints", "#DDF6EA", GREEN),
]
cols = st.columns(6, gap="small")
for col, (label, value, note, change, tint, accent) in zip(cols, metrics):
    with col:
        st.markdown(
            f"""
            <div class="metric-card">
              <div class="metric-head"><span>{label}</span></div>
              <div class="metric-value" style="font-size:{'19px' if label == 'Biggest complaint' else '28px'};">{value}</div>
              <div class="metric-note">{note}</div>
              <div class="metric-change" style="color:{accent};">{change}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("<div style='height:17px'></div>", unsafe_allow_html=True)
# ---------- Main charts ----------
left, right = st.columns([1.65, 1], gap="medium")

with left:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Customer feedback trend</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-subtitle">Sentiment distribution over the last 10 months</div>', unsafe_allow_html=True)
    trend = pd.DataFrame({
        "Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct"],
        "Positive": [72, 89, 98, 120, 124, 111, 125, 116, 135, 158],
        "Neutral": [32, 45, 51, 62, 57, 57, 62, 53, 68, 85],
        "Negative": [15, 21, 24, 28, 21, 23, 22, 17, 23, 29],
    }).melt(id_vars="Month", var_name="Sentiment", value_name="Feedback")
    line_fig = px.line(
        trend, x="Month", y="Feedback", color="Sentiment", markers=True,
        color_discrete_map={"Positive": GREEN, "Neutral": AMBER, "Negative": RED},
        category_orders={"Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct"]},
    )
    line_fig.update_layout(
        height=300,
        margin={"l": 0, "r": 8, "t": 8, "b": 0},
        paper_bgcolor="white",
        plot_bgcolor="white",
        font={"family": "Inter, sans-serif", "size": 10, "color": "#475569"},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
        xaxis={"title": None, "showgrid": False, "linecolor": BORDER},
        yaxis={"title": None, "gridcolor": "#EDF2F7", "zeroline": False},
    )
    line_fig.update_traces(line={"width": 2.5}, marker={"size": 5})
    st.plotly_chart(line_fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Customer sentiment</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-subtitle">Share of all recorded feedback</div>', unsafe_allow_html=True)
    sentiment_df = pd.DataFrame({
        "Sentiment": ["Positive", "Neutral", "Negative"],
        "Count": [positive_count, neutral_count, negative_count],
        "Color": [GREEN, AMBER, RED],
    })
    donut = go.Figure(data=[go.Pie(
        labels=sentiment_df["Sentiment"], values=sentiment_df["Count"], hole=.68,
        marker={"colors": [GREEN, AMBER, RED], "line": {"color": "white", "width": 3}},
        textinfo="percent", textposition="inside", insidetextfont={"color": "white", "size": 11},
        hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
    )])
    donut.update_layout(
        height=260,
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        paper_bgcolor="white",
        showlegend=True,
        legend={"orientation": "v", "x": 1.0, "y": .5, "font": {"size": 11}},
        annotations=[{
            "text": "<b>600</b><br><span style='font-size:11px'>Responses</span>",
            "x": .39,
            "y": .5,
            "showarrow": False,
            "font": {"size": 19, "color": TEXT},
        }],
    )
    st.plotly_chart(donut, use_container_width=True, config={"displayModeBar": False})
    a, b, c = st.columns(3)
    a.metric("Positive", "61.8%", "371")
    b.metric("Neutral", "31.4%", "188")
    c.metric("Negative", "6.8%", "41")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

# ---------- Lower detail panels ----------
complaints_col, feedback_col, insights_col = st.columns([1.05, 1.25, 1], gap="medium")

with complaints_col:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Top complaint categories</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-subtitle">Issues generating the most customer friction</div>', unsafe_allow_html=True)
    complaint_data = pd.DataFrame({
        "Category": ["App Experience", "Account Issues", "Transaction Delay", "Customer Support", "Other"],
        "Count": [15, 10, 7, 5, 4],
    })
    for _, row in complaint_data.iterrows():
        percentage = row["Count"] / 41 * 100
        st.markdown(
            f"""
            <div style="margin:12px 0 14px 0;">
              <div style="display:flex;justify-content:space-between;gap:8px;margin-bottom:6px;">
                <span class="complaint-label">{row['Category']}</span>
                <span class="complaint-count">{row['Count']} <span style="color:{MUTED};font-weight:400;">&nbsp;·&nbsp; {row['Count']/41*100:.1f}%</span></span>
              </div>
              <div style="height:7px;background:#EDF2F7;border-radius:10px;overflow:hidden;">
                <div style="height:7px;width:{percentage}%;background:linear-gradient(90deg,{DARK_GREEN},{GREEN});border-radius:10px;"></div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown('</div>', unsafe_allow_html=True)

with feedback_col:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    title_col, action_col = st.columns([3, 1])
    with title_col:
        st.markdown('<div class="panel-title">Recent customer feedback</div>', unsafe_allow_html=True)
        st.markdown('<div class="panel-subtitle">Latest customer comments and ratings</div>', unsafe_allow_html=True)
    with action_col:
        st.markdown(f'<div style="text-align:right;color:{GREEN};font-size:11px;font-weight:700;padding-top:4px;">{len(filtered)} shown</div>', unsafe_allow_html=True)

    sentiment_colors = {"Positive": ("#DDF6EA", GREEN), "Neutral": ("#FFF3D6", AMBER), "Negative": ("#FEE8E8", RED)}
    recent = filtered.sort_values("date", ascending=False).head(5)
    if recent.empty:
        st.info("No feedback matches these filters. Try expanding the date range or changing the selected filters.")
    else:
        for _, item in recent.iterrows():
            tint, accent = sentiment_colors[item["sentiment"]]
            stars = "★" * int(item["rating"]) + "☆" * (5 - int(item["rating"]))
            st.markdown(
                f"""
                <div style="display:flex;gap:9px;padding:10px 0;border-bottom:1px solid #EEF2F6;">
                  <div style="width:31px;height:31px;min-width:31px;border-radius:50%;background:{tint};color:{accent};display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:800;">{item['sentiment'][0]}</div>
                  <div style="flex:1;min-width:0;">
                    <div class="feedback-text">{item['comment']}</div>
                    <div style="display:flex;justify-content:space-between;gap:8px;align-items:center;margin-top:5px;">
                      <span class="feedback-date">{item['date'].strftime('%b %d, %Y')} · {item['topic']}</span>
                      <span class="rating" style="font-size:11px;">{stars} <span style="color:{MUTED};letter-spacing:0;">{item['rating']}.0</span></span>
                    </div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    st.markdown('</div>', unsafe_allow_html=True)

with insights_col:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Quick insights</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-subtitle">Recommended priorities based on feedback</div>', unsafe_allow_html=True)
    insights = [
        ("#DDF6EA", GREEN, "Positive feedback is trending up", "Positive sentiment stands at 61.8%. Keep reinforcing the experiences customers value."),
        ("#FEE8E8", RED, "Reduce unresolved complaints", "There are 41 complaints to resolve. Prioritise issues affecting transfers and account access."),
        ("#FFF3D6", AMBER, "App Experience is the top issue", "15 complaints relate to app experience, accounting for 36.6% of all complaints."),
    ]
    for tint, accent, title, copy in insights:
        st.markdown(
            f"""
            <div class="insight">
              <div class="insight-bubble" style="background:{tint};color:{accent};">•</div>
              <div><div class="insight-title">{title}</div><div class="insight-copy">{copy}</div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    import streamlit as st
    st.markdown("<div style='height:7px'></div>", unsafe_allow_html=True)