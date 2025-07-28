import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load .env file from current directory
load_dotenv()

api_key = os.getenv("API_KEY")

# Page configuration
st.set_page_config(
    page_title="Player Analysis",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load and prepare data
@st.cache_data
def load_data():
    df = pd.read_csv('data/players_data/epl_player_stats_2024_25.csv')
    
    # Map detailed positions to categories
    def map_pos(p):
        p = str(p).upper()
        if 'GKP' in p:
            return 'Goalkeeper'
        if any(tag in p for tag in ['DEF']):
            return 'Defender'
        if any(tag in p for tag in ['MID']):
            return 'Midfielder'
        if any(tag in p for tag in ['FWD']):
            return 'Forward'
        return 'Other'
    df['PosCat'] = df['Position'].apply(map_pos)

    # Create per90 columns for relevant stats
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

# Theme color
PRIMARY = '#37003C'

# Header
st.markdown(f"<h1 style='text-align:center; color:{PRIMARY};'>🔍 Player Analysis</h1>", unsafe_allow_html=True)
st.markdown("---")

# Team selector
teams = sorted(df['Club'].unique())
team = st.selectbox('Select Team:', teams)

df_team = df[df['Club'] == team]

# Position selector
pos_order = ['Goalkeeper','Defender','Midfielder','Forward']
avail = [p for p in pos_order if p in df_team['PosCat'].unique()]
pos = st.selectbox('Select Position:', avail)

df_pos = df_team[df_team['PosCat'] == pos]

# Player selector
player = st.selectbox('Select Player:', sorted(df_pos['Player Name']))
row = df_pos[df_pos['Player Name'] == player].iloc[0]

# Stat map per position
stats_map = {
    'Goalkeeper': [
        'Saves','Saves %','Penalties Saved','Goals Prevented',
        'Clean Sheets','Punches','High Claims','Goals Conceded','Own Goals'
    ],
    'Defender': [
        'Tackles','Interceptions','Blocks','Clearances','Possession Won',
        'gDuels %','aDuels %','Goals','Assists','Passes','Passes%','Own Goals'
    ],
    'Midfielder': [
        'Goals','Assists','Touches','Shots','Passes','Passes%',
        'Through Balls','Progressive Carries','fThird Passes','fThird Passes %',
        'Tackles','Interceptions','gDuels %','aDuels %','Fouls'
    ],
    'Forward': [
        'Goals','Assists','Shots','Conversion %','Big Chances Missed','Hit Woodwork',
        'Passes','Passes%','fThird Passes','fThird Passes %'
    ]
}

# Compute percentiles
def fmt_val(col):
    # Decide which minutes bucket this player is in
    mins = row['Minutes']
    if mins > 1500:
        mask_mins = (df['Minutes'] > 1500)
    elif mins >= 700:
        mask_mins = (df['Minutes'] >= 700) & (df['Minutes'] <= 1500)
    else:
        mask_mins = (df['Minutes'] < 700)

    # Pool: same position and same usage bucket
    pool = df[(df['PosCat'] == pos) & mask_mins]

    # Fallback if pool too small
    if len(pool) < 5:  
        # broaden to entire position
        pool = df[df['PosCat'] == pos]

    # Choose per90 or raw column
    per90_col = col + ' per90'
    use_col = per90_col if per90_col in df.columns else col

    # Get value and series
    val = row[use_col]
    series = pool[use_col]

    # Format numeric vs. string
    try:
        num_val = float(val)
        val_str = f"{num_val:.2f}"
    except:
        val_str = str(val)

    # Compute percentile: invert for “less is better” stats
    try:
        if col in ['Goals Conceded', 'Own Goals', 'Fouls', 'Hit Woodwork', 'Big Chances Missed']:
            pct = 100 - int(series.rank(pct=True, ascending=True)[row.name] * 100)
        else:
            pct = int(series.rank(pct=True)[row.name] * 100)
    except:
        pct = None

    return f"{val_str} (P{pct if pct is not None else 'N/A'})"


# Display header info
st.markdown(f"<h2 style='color:{PRIMARY};'>{player} — {pos}</h2>", unsafe_allow_html=True)
st.write(f"**Nationality:** {row['Nationality']}  |  **Appearances:** {row['Appearances']}  |  **Minutes:** {row['Minutes']} |  **Yellow Cards:** {row['Yellow Cards']} |  **Red Cards:** {row['Red Cards']}")
st.markdown("---")

# Determine usage bucket
mins = row['Minutes']
if mins > 1500:
    bucket = "🔴 High‑usage (> 1500 min)"
    bucket_expl = "This player is a regular starter—percentiles compare to other > 1500 min players."
elif mins >= 700:
    bucket = "🟡 Medium‑usage (700–1500 min)"
    bucket_expl = "This player is a semi‑regular—percentiles compare to other 700–1500 min players."
else:
    bucket = "🟢 Low‑usage (< 700 min)"
    bucket_expl = "This player is a rotational/young player/got injured—percentiles compare to other < 700 min players."

# Display the bucket info
st.markdown(f"<h4 style='color:{PRIMARY};'>{bucket}</h4>", unsafe_allow_html=True)
st.caption(bucket_expl)
st.markdown("---")

# Display key metrics table
stats = stats_map.get(pos, [])
d = {}

for col in stats:
    per90_col = col + ' per90'
    label = f"{col} (per90)" if per90_col in df.columns else col
    d[label] = fmt_val(col)

st.subheader('Key Metrics')
for label, val in d.items():
    # Extract numeric percentile
    try:
        pct = int(val.split('(P')[-1].strip(')'))
    except:
        pct = 0

    # Three‑stop gradient: red → yellow → green
    bar_gradient = "linear-gradient(90deg, #dc3545 0%, #ffc107 50%, #28a745 100%)"

    st.markdown(f"""
    <div style="display: flex; align-items: center; margin-bottom: 20px;">
        <div style="flex: 1; min-width: 300px;">
            <strong>{label}:</strong> {val}
        </div>
        <div style="flex: none; width: 500px; background: #e0e0e0; border-radius: 4px; overflow: hidden; height: 12px; margin-left: 16px;">
            <div style="background: {bar_gradient}; width: {pct}%; height: 100%;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# Define your radar stats per position
radar_stats_map = {
    'Goalkeeper': ['Saves %', 'Clean Sheets', 'Goals Prevented', 'Goals Conceded', 'High Claims'],
    'Defender':   ['Tackles', 'Interceptions', 'Blocks', 'gDuels %', 'aDuels %','Passes%','Goals','Assists'],
    'Midfielder': ['Goals', 'Assists','Shots','fThird Passes', 'Passes%', 'Touches', 'Progressive Carries', 'Through Balls','Fouls'],
    'Forward':    ['Goals', 'Shots', 'Assists','Passes%', 'Big Chances Missed']
}

# Build a dict of percentiles using fmt_val
radar_stats = radar_stats_map.get(pos, [])
radar_vals = {}
for stat in radar_stats:
    # fmt_val returns "X.XX (PYY)"; split out the numeric percentile
    txt = fmt_val(stat)
    try:
        pct = int(txt.split('(P')[-1].strip(')'))
    except:
        pct = 0
    radar_vals[stat] = pct / 100  # scale 0–1 for radar

# Build a small DataFrame for the radar
categories = list(radar_vals.keys())
values = list(radar_vals.values())

# Close the loop for radar
categories += [categories[0]]
values += [values[0]]

radar_df = pd.DataFrame({
    'Metric': categories,
    'Percentile': values
})

st.subheader(f"{player} Performance Radar")

fig = px.line_polar(
    radar_df,
    r='Percentile',
    theta='Metric',
    line_close=True,
    template=None
)
fig.update_traces(fill='toself', line_color=PRIMARY)
fig.update_layout(
    polar=dict(
        radialaxis=dict(range=[0,1], showticklabels=False, ticks=''),
        angularaxis=dict(tickfont_size=14)
    ),
    showlegend=False,
    margin=dict(l=120, r=120, t=100, b=100),
    width=600,
    height=600
)

col1, col2, col3 = st.columns([2, 6, 2])

with col2:
    st.plotly_chart(
        fig,
        use_container_width=False
    )

nlp_stats_map = radar_stats_map

client = OpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1"
)

chosen = nlp_stats_map.get(pos, [])
stats_summary = "\n".join(f"{stat}: {fmt_val(stat)}" for stat in chosen)

st.subheader(f"{player} AI-Powered Analysis")
st.markdown("---")
if st.button("📝 Generate Analysis"):
    with st.spinner("Generating..."):
        messages = [
            {"role": "system", "content": "You are an expert football analyst and scout."},
            {"role": "user", "content": f"Here are percentile stats for {player}, a {pos}:\n\n{stats_summary}\n\nWrite a 3‑4 sentence analysis and scouting report."}
        ]
        resp = client.chat.completions.create(model="deepseek/deepseek-r1:free", messages=messages)
        report = resp.choices[0].message.content.strip()
        st.write(report)



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

