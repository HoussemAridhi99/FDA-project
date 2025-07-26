import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load .env file from current directory
load_dotenv()

api_key = os.getenv("API_KEY")

# Page setup
st.set_page_config(
    page_title="Player Comparison",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

PRIMARY = '#37003C'

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv('data/players_data/epl_player_stats_2024_25.csv')

    def map_pos(p):
        p = str(p).upper()
        if 'GKP' in p: return 'Goalkeeper'
        if 'DEF' in p: return 'Defender'
        if 'MID' in p: return 'Midfielder'
        if 'FWD' in p: return 'Forward'
        return 'Other'
    
    df['PosCat'] = df['Position'].apply(map_pos)

    per90_cols = [
        'Goals','Assists','Shots','Touches','Passes','Successful Passes','Through Balls',
        'Progressive Carries','fThird Passes','Successful fThird Passes','Tackles','Interceptions',
        'Blocks','Clearances','Clearances Off Line','Possession Won','Ground Duels','Aerial Duels',
        'Fouls','Saves','Penalties Saved','Own Goals','Goals Conceded','Punches','High Claims'
    ]
    for col in per90_cols:
        if col in df.columns and df['Minutes'].dtype in [np.float64, np.int64]:
            df[col + ' per90'] = df[col] / df['Minutes'] * 90

    return df

df = load_data()

radar_stats_map = {
    'Goalkeeper': ['Saves %', 'Clean Sheets', 'Goals Prevented', 'Goals Conceded', 'High Claims'],
    'Defender': ['Tackles', 'Interceptions', 'Blocks', 'gDuels %', 'aDuels %','Passes%','Goals','Assists'],
    'Midfielder': ['Goals', 'Assists','Shots','fThird Passes', 'Passes%', 'Touches', 'Progressive Carries', 'Through Balls','Fouls'],
    'Forward': ['Goals', 'Shots', 'Assists','Passes%', 'Conversion %', 'Big Chances Missed']
}

# --- SELECTION ---
st.markdown(f"<h1 style='text-align:center; color:{PRIMARY};'>📊 Player Comparison</h1>", unsafe_allow_html=True)
st.markdown("---")

teams = sorted(df['Club'].unique())

col1, col2 = st.columns(2)

with col1:
    team1 = st.selectbox("Team 1", teams, key="team1")
    df1_team = df[df['Club'] == team1]
    player1 = st.selectbox("Player 1", sorted(df1_team['Player Name']), key="player1")
    row1 = df1_team[df1_team['Player Name'] == player1].iloc[0]
    pos = row1['PosCat']
    mins1 = row1['Minutes']
    bucket = 'high' if mins1 > 1500 else 'mid' if mins1 >= 700 else 'low'

with col2:
    team2 = st.selectbox("Team 2", teams, key="team2")
    df2_team = df[(df['Club'] == team2) & (df['PosCat'] == pos)]
    if bucket == 'high':
        df2_team = df2_team[df2_team['Minutes'] > 1500]
    elif bucket == 'mid':
        df2_team = df2_team[(df2_team['Minutes'] >= 700) & (df2_team['Minutes'] <= 1500)]
    else:
        df2_team = df2_team[df2_team['Minutes'] < 700]

    player2 = st.selectbox("Player 2", sorted(df2_team['Player Name']), key="player2")
    row2 = df2_team[df2_team['Player Name'] == player2].iloc[0]

st.markdown(f"### Position: {pos}  |  Usage Bucket: {'🔴' if bucket=='high' else '🟡' if bucket=='mid' else '🟢'}", unsafe_allow_html=True)
st.markdown("---")

# --- KEY METRICS ---
stats = radar_stats_map[pos]

st.subheader("Key Metrics Comparison")
col1, col2 = st.columns(2)
for stat in stats:
    for r, label, c in [(row1, player1, col1), (row2, player2, col2)]:
        per90_col = stat + ' per90'
        use_col = per90_col if per90_col in df.columns else stat
        try:
            val = f"{r[use_col]:.2f}"
        except:
            val = str(r[use_col])
        c.write(f"**{label}** — {stat}: {val}")

# --- RADAR CHART ---
st.subheader("Comparative Performance Radar")
def get_radar_vals(row, pos):
    mins = row['Minutes']
    if mins > 1500:
        mask = (df['Minutes'] > 1500)
    elif mins >= 700:
        mask = (df['Minutes'] >= 700) & (df['Minutes'] <= 1500)
    else:
        mask = (df['Minutes'] < 700)
    pool = df[(df['PosCat'] == pos) & mask]

    out = []
    for stat in radar_stats_map[pos]:
        col = stat + ' per90' if stat + ' per90' in df.columns else stat
        try:
            pct = 100 - pool[col].rank(pct=True, ascending=True)[row.name]*100 if stat in ['Goals Conceded','Own Goals','Fouls'] else pool[col].rank(pct=True)[row.name]*100
        except:
            pct = 0
        out.append(pct/100)
    return out

vals1 = get_radar_vals(row1, pos)
vals2 = get_radar_vals(row2, pos)
categories = radar_stats_map[pos] + [radar_stats_map[pos][0]]

# Prepare a DataFrame for both players
metrics = radar_stats_map[pos]
# Close the loop (append first metric at end)
cat_loop = metrics + [metrics[0]]
vals1_loop = vals1 + [vals1[0]]
vals2_loop = vals2 + [vals2[0]]

radar_df = pd.DataFrame({
    'Metric': cat_loop * 2,
    'Percentile': vals1_loop + vals2_loop,
    'Player': [player1] * len(cat_loop) + [player2] * len(cat_loop)
})

fig = px.line_polar(
    radar_df,
    r='Percentile',
    theta='Metric',
    color='Player',
    line_close=True,
    template=None,
    color_discrete_map={
        player1: '#1f77b4',  # blue
        player2: '#ff7f0e'   # orange
    }
)
fig.update_traces(fill='toself')
fig.update_layout(
    polar=dict(
        radialaxis=dict(range=[0,1], showticklabels=False, ticks=''),
        angularaxis=dict(tickfont_size=14)
    ),
    showlegend=True,
    margin=dict(l=120, r=120, t=100, b=100),
    width=620,
    height=620
)

col1, col2, col3 = st.columns([2, 6, 2])
with col2:
    st.plotly_chart(fig, use_container_width=False)

# --- LLM COMPARATIVE ANALYSIS ---
client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")

def fmt_stat(row, stat):
    per90_col = stat + ' per90'
    col = per90_col if per90_col in df.columns else stat
    try:
        val = f"{row[col]:.2f}"
    except:
        val = str(row[col])
    return f"{stat}: {val}"

sum1 = "\n".join([fmt_stat(row1, s) for s in radar_stats_map[pos]])
sum2 = "\n".join([fmt_stat(row2, s) for s in radar_stats_map[pos]])

st.subheader(f"{player1} vs {player2} AI-Powered Comparative Analysis")
if st.button("📝 Generate Comparison"):
    with st.spinner("Generating..."):
        messages = [
            {"role": "system", "content": "You are a professional football analyst."},
            {"role": "user", "content": f"Compare these two {pos}s based on their stats:\n\n{player1}:\n{sum1}\n\n{player2}:\n{sum2}\n\nWrite a 3-5 sentence comparative report outlining strengths, differences, and who may fit better in a high-intensity pressing team."}
        ]
        response = client.chat.completions.create(model="deepseek/deepseek-r1:free", messages=messages)
        st.write(response.choices[0].message.content.strip())



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
