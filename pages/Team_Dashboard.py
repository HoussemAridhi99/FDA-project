import streamlit as st
import pandas as pd
import altair as alt
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load .env file from current directory
load_dotenv()

api_key = os.getenv("API_KEY")

# Set page configuration
st.set_page_config(
    page_title="Team Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premier League colors
PL_PRIMARY_COLOR = "#37003C"
PL_HOVER_COLOR = "#500050"
PL_TEXT_COLOR = "#FFFFFF"
PL_WIN_COLOR = "#2ECC71"      # Green
PL_DRAW_COLOR = "#000000"     # Black
PL_LOSS_COLOR = "#E74C3C"     # Red
PL_XG_COLOR = "#1F78B4"       # Blue for xG
PL_XGA_COLOR = "#A6CEE3"      # Light blue for xGA

# Custom CSS for theme
st.markdown(f"""
    <style>
    .reportview-container {{
        background-color: #FFFFFF;
        color: {PL_PRIMARY_COLOR};
    }}
    .stMetric {{
        background-color: #F5F5F5;
        border-radius: 8px;
        padding: 1em;
    }}
    .memory-card {{
        background-color: #F0F0F0;
        padding: 1em;
        border-radius: 8px;
        margin-bottom: 2em;
    }}
    .memory-card h3 {{ color: {PL_PRIMARY_COLOR}; }}
    .memory-card p {{ margin: 0.5em 0; }}
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown(f"<h1 style='text-align: center; color: {PL_PRIMARY_COLOR};'>📈 Team Dashboard</h1>", unsafe_allow_html=True)
st.markdown("---")

# Teams list
teams = sorted([
    "Arsenal", "Aston Villa", "Bournemouth", "Brentford", "Brighton",
    "Chelsea", "Crystal Palace", "Everton", "Fulham", "Liverpool",
    "Manchester City", "Manchester United", "Newcastle United", "Nottingham Forest", "Southampton",
    "Tottenham", "West Ham", "Wolverhampton Wanderers", "Leicester", "Ipswich"
])

# Team selector
selected_team = st.selectbox("Select a Premier League Team (2024-25):", teams)

# Display team logo (centered using columns, bigger size)
logo_path = f"data/team_logos/{selected_team}.png"
col1, col2, col3 = st.columns([2, 1, 2])  # Side-middle-side layout
with col2:
    st.image(logo_path, width=220)

# Load team data CSV
csv_path = f"data/team_data/{selected_team}.csv"
df = pd.read_csv(csv_path)

# Compute match outcomes
df['Outcome'] = df['MatchPoints'].map({3: 'Win', 1: 'Draw', 0: 'Loss'}) if 'MatchPoints' in df else df['result'].map({'w': 'Win','d': 'Draw','l': 'Loss'})

# Compute xG metrics
if 'xg' in df.columns and 'xga' in df.columns:
    df['xGD'] = df['xg'] - df['xga']
    df['cum_xG'] = df['xg'].cumsum()
    df['cum_xGA'] = df['xga'].cumsum()

# Compute expected points
df['xpts'] = df.get('xpts', df['Outcome'].map({'Win':3,'Draw':1,'Loss':0}))
df['cum_xpts'] = df['xpts'].cumsum()

# Display KPIs
latest = df.iloc[-1]
col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Total Points", latest.TotalPoints)
col2.metric("League Position", latest.Position)
col3.metric("Goals", latest.GoalsForCumulative)
col4.metric("Goals Against", latest.GoalsAgainstCumulative)
col5.metric("xG (Total)", round(latest.cum_xG,2) if 'cum_xG' in latest else "N/A")
col6.metric("xGA (Total)", round(latest.cum_xGA,2) if 'cum_xGA' in latest else "N/A")
st.markdown("---")

# Section: Points Over Season
st.subheader("Points Over Season")
points_line = alt.Chart(df).mark_line(point=True).encode(
    x='Round:O', y=alt.Y('TotalPoints:Q', title='Total Points'), color=alt.value(PL_PRIMARY_COLOR)
)
outcome_points = alt.Chart(df).mark_circle(size=100).encode(
    x='Round:O', y='TotalPoints:Q', color=alt.Color('Outcome:N', scale=alt.Scale(domain=['Win','Draw','Loss'], range=[PL_WIN_COLOR,PL_DRAW_COLOR,PL_LOSS_COLOR])),
    tooltip=['Round','TotalPoints','Outcome']
)
st.altair_chart((points_line+outcome_points).properties(height=350), use_container_width=True)

# Section: League Position Over Season
st.subheader("League Position Over Season")
position_chart = alt.Chart(df).mark_line(point=True).encode(
    x='Round:O', y=alt.Y('Position:Q', sort='descending', title='League Position (1 = Top)'), color=alt.value(PL_PRIMARY_COLOR)
).properties(height=300)
st.altair_chart(position_chart, use_container_width=True)

# Other Sections: Match Points, Goals, xG & xGA, xPTS
st.markdown("---")
for title, chart in [
    ("Match Points by Round", alt.Chart(df).mark_bar().encode(
        x='Round:O', y='MatchPoints:Q', color=alt.Color('Outcome:N', scale=alt.Scale(domain=['Win','Draw','Loss'], range=[PL_WIN_COLOR,PL_DRAW_COLOR,PL_LOSS_COLOR]))
    ).properties(height=300)),
    ("Goals For vs. Goals Against (Cumulative)", alt.layer(
        alt.Chart(df).mark_area(opacity=0.6).encode(x='Round:O', y='GoalsForCumulative:Q', color=alt.value(PL_WIN_COLOR)),
        alt.Chart(df).mark_area(opacity=0.6).encode(x='Round:O', y='GoalsAgainstCumulative:Q', color=alt.value(PL_LOSS_COLOR))
    ).properties(height=300)),
    ("Goals For & Against per Round", alt.Chart(df).transform_fold(['GF','GA'], as_=['Type','Goals']).mark_bar().encode(
        x='Round:O', y='Goals:Q', color=alt.Color('Type:N', scale=alt.Scale(domain=['GF','GA'], range=[PL_WIN_COLOR,PL_LOSS_COLOR]))
    ).properties(height=300)),
    ("Expected Goals (xG) vs xGA", alt.layer(
        alt.Chart(df).mark_bar().encode(x='Round:O', y='xg:Q', color=alt.value(PL_XG_COLOR)),
        alt.Chart(df).mark_bar().encode(x='Round:O', y='xga:Q', color=alt.value(PL_XGA_COLOR))
    ).properties(height=300)),
    ("Cumulative xG & xGA", alt.layer(
        alt.Chart(df).mark_line(point=True).encode(x='Round:O', y='cum_xG:Q', color=alt.value(PL_XG_COLOR)),
        alt.Chart(df).mark_line(point=True).encode(x='Round:O', y='cum_xGA:Q', color=alt.value(PL_XGA_COLOR))
    ).properties(height=300)),
    ("Expected Points (xPTS) Over Season", alt.Chart(df).mark_line(point=True).encode(
        x='Round:O', y='cum_xpts:Q', color=alt.value(PL_WIN_COLOR)
    ).properties(height=300))
]:
    st.subheader(title)
    st.altair_chart(chart, use_container_width=True)
    st.markdown("---")

# Section: Most Memorable Performance
st.subheader("Most Memorable Performance")
mem_df = pd.read_csv("data/team_data/memorable_performances_2024_25.csv")
row = mem_df[mem_df['team']==selected_team].iloc[0]

# Improved memory card layout
st.markdown(f"""
<div class='memory-card'>
  <h3>{row['description']}</h3>
  <div class='row'>
    <div class='col'><strong>Date: </strong><span>{pd.to_datetime(row['date']).strftime('%d %b %Y')}</span></div>
    <div class='col'><strong>Opponent: </strong><span>{row['opponent'].title()} ({row['venue'].capitalize()})</span></div>
    <div class='col'><strong>Score: </strong><span>{row['score']}</span></div>
  </div>
  <div class='row'>
    <div class='col'>🎯 <strong>xG:</strong><span>{row['xg']}</span></div>
    <div class='col'>🛡️ <strong>xGA:</strong><span>{row['xga']}</span></div>
    <div class='col'>#️⃣ <strong>xGD:</strong><span>{round(row['xg']-row['xga'],2)}</span></div>
  </div>
  <div class='row'>
    <div class='col'>⚽️ <strong>Shots:</strong><span>{row['shots']} ({row['shots_on_target']} on target)</span></div>
    <div class='col'>🚫 <strong>Against:</strong><span>{row['shots_against']} ({row['shots_on_target_against']} on target)</span></div>
    <div class='col'>📊 <strong>PPDA:</strong><span>{row['ppda']}</span></div>
    <div class='col'>⚡ <strong>Opp PPDA:</strong><span>{row['ppda_against']}</span></div>
  </div>
</div>
""", unsafe_allow_html=True)

# Initialize OpenRouter client for DeepSeek‑R1 (free tier)
client = OpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1"
)

# --- Build a simple metrics summary for the team ---
metrics = [
    ("Total Points", latest.TotalPoints),
    ("League Position", latest.Position),
    ("Goals For", latest.GoalsForCumulative),
    ("Goals Against", latest.GoalsAgainstCumulative)
]
if hasattr(latest, "cum_xG"):
    metrics.append(("xG (Total)", round(latest.cum_xG, 2)))
if hasattr(latest, "cum_xGA"):
    metrics.append(("xGA (Total)", round(latest.cum_xGA, 2)))

metrics_block = "\n".join(f"{name}: {value}" for name, value in metrics)

st.markdown("---")
st.subheader(f"{selected_team} AI-Powered Analysis")
if st.button("📝 Generate Team Analysis"):
    with st.spinner("Analyzing team performance…"):
        messages = [
            {"role": "system", "content": "You are an expert football analyst and scout."},
            {"role": "user", "content": (
                f"Here are the key season stats for {selected_team} in 2024‑25:\n\n"
                f"{metrics_block}\n\n"
                "Write a concise scouting report (3 paragraphs of 2-3 sentences) highlighting strengths, style of play, and areas to improve."
            )}
        ]
        try:
            resp = client.chat.completions.create(
                model="deepseek/deepseek-r1:free",
                messages=messages
            )
            report = resp.choices[0].message.content.strip()
            st.write(report)
        except Exception as e:
            st.error(f"Failed to generate report: {e}")


# Footer
st.markdown("""
    <br><br>
    <div style='text-align: center; color: #37003C;'>
        Built with passion for Premier League fans ⚽️
    </div>
""", unsafe_allow_html=True)
st.markdown(
    "<div style='text-align:center; margin-top:50px; color:gray;'>© 2025 Houssem Aridhi</div>",
    unsafe_allow_html=True
)