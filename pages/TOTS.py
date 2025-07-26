import streamlit as st
import pandas as pd
from mplsoccer.pitch import Pitch
from openai import OpenAI

api_key = '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'

# Page configuration
st.set_page_config(
    page_title="Team Of The Season",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded"
)

PRIMARY = '#37003C'

@st.cache_data
def load_data():
    df = pd.read_csv('data/players_data/epl_player_stats_2024_25.csv')
    # Position categories
    def map_pos(p):
        p = str(p).upper()
        if 'GKP' in p: return 'Goalkeeper'
        if 'DEF' in p: return 'Defender'
        if 'MID' in p: return 'Midfielder'
        if 'FWD' in p: return 'Forward'
        return 'Other'
    df['PosCat'] = df['Position'].apply(map_pos)
    # per90 columns
    per90_cols = ['Goals','Assists','Shots','Touches','Passes','Successful Passes',
                  'Through Balls','Progressive Carries','fThird Passes',
                  'Successful fThird Passes','Tackles','Interceptions',
                  'Blocks','Clearances','Possession Won','Ground Duels',
                  'Aerial Duels','Fouls','Saves','Penalties Saved',
                  'Goals Conceded','Own Goals','Punches','High Claims','Goals Prevented','Big Chances Missed']
    for col in per90_cols:
        if col in df.columns:
            df[col+' per90'] = df[col] / df['Minutes'] * 90
    return df

df = load_data()

# Only high-usage players
df_hi = df[df['Minutes'] > 2300]

# Helper for percentile
def pct_rank(s, val, invert=False):
    rank = s.rank(pct=True)[s == val].iloc[0]
    return 1 - rank if invert else rank

# metric groups
# Each stat has a weight; sums of weights per group decide influence
metric_groups = {
    'Goalkeeper': {
        'core': {
            'Saves %': 2.0,
            'Clean Sheets': 2.5,
            'Goals Prevented per90': 1,
            'Goals Conceded per90': 2.0,
            'High Claims per90': 1.0,
            'Own Goals per90': 0.5
        }
    },
    'Defender': {
        'def': {
            'Blocks per90': 3,
            'Possession Won per90': 1,
            'Tackles per90': 1.9,
            'Interceptions per90': 2,
            'Clearances' : 1.4,
            'gDuels %': 1,
            'aDuels %': 1,
            'Assists per90': 1,
            'Goals per90': 3.0,
            'Passes%': 1.5,
            'Passes per90': 2.5,
        },
        'att': {
            'Assists per90': 4.5,
            'Goals per90': 3.0,
            'Passes%': 0.5,
            'Passes per90': 0.5,
            'Blocks per90': 0.5,
            'Possession Won per90': 0.5,
            'Tackles per90': 0.5,
            'Interceptions per90': 0.5,
            'gDuels %': 0.5,
            'aDuels %': 0.5
        }
    },
    'Midfielder': {
        'def': {
            'Touches per90': 1.0,
            'Progressive Carries per90': 5.0,
            'Fouls per90': 0.5,
            'Shots per90': 0.5,
            'Tackles per90' : 5.0,
            'fThird Passes per90': 1.0,
            'Passes%': 4.0,
            'Assists per90': 1.0,
            'Goals per90': 1.0,
        },
        'att': {
            'Goals per90': 4.0,
            'Assists per90': 4.0,
            'Shots per90': 2.5,
            'Passes%': 1.0,
            'Touches per90': 0.5,
            'Touches per90': 0.5
        }
    },
    'Forward': {
        'core': {
            'Goals per90': 5.0,
            'Shots per90': 1.0,
            'Assists per90': 1.0,
            'Big Chances Missed per90': 0.5
        }
    }
}


# Compute weighted scores by subgroup
subgroup_scores = {}

for pos, groups in metric_groups.items():
    dfp = df_hi[df_hi['PosCat'] == pos]

    for group_name, metrics in groups.items():  # group_name: 'core', 'def', 'att'
        key = f"{pos}_{group_name}"  # e.g., 'Defender_def'
        scores = []

        for idx, row in dfp.iterrows():
            weighted_sum = 0.0
            total_weight = 0.0

            for stat, weight in metrics.items():
                if stat not in dfp.columns:
                    continue
                invert = stat in ['Goals Conceded per90', 'Own Goals per90', 'Fouls per90', 'Big Chances Missed per90']
                pr = pct_rank(dfp[stat], row[stat], invert=invert)
                weighted_sum += pr * weight
                total_weight += weight

            if total_weight > 0:
                avg_pct = weighted_sum / total_weight
                score10 = round(avg_pct * 10, 2)
                scores.append((idx, score10))

        subgroup_scores[key] = sorted(scores, key=lambda x: x[1], reverse=True)

# Build Best XI using specialized subgroup scores
best11 = {}

# Goalkeeper
best11['GK'] = subgroup_scores['Goalkeeper_core'][0][0]

# Defensive Defenders
best11['Def (Defensive)'] = [idx for idx, _ in subgroup_scores['Defender_def'][:2]]

# Attacking Defenders
best11['Def (Attacking)'] = [idx for idx, _ in subgroup_scores['Defender_att'][:2]]

# Defensive Midfielders
best11['Mid (Defensive)'] = [idx for idx, _ in subgroup_scores['Midfielder_def'][:2]]

# Attacking Midfielders
best11['Mid (Attacking)'] = [idx for idx, _ in subgroup_scores['Midfielder_att'][:3]]

# Striker
best11['ST'] = subgroup_scores['Forward_core'][0][0]


pitch = Pitch(pitch_color='grass', 
    line_color='white', 
    stripe=True,
    pitch_type='statsbomb',
    axis=False)
fig, ax = pitch.draw()

# Position coordinates (x, y)
positions = {
    'GK': (8, 40),
    'CB1': (25, 30), 'CB2': (25, 50),
    'LB': (30, 10), 'RB': (30, 70),
    'CM1': (55, 20), 'CM2': (55, 60),
    'CAM': (85, 40), 'LW': (85, 15), 'RW': (85, 65),
    'ST': (110, 40)
}

# Assign each role to best11 players
assigned_positions = {
    'GK': best11['GK'],
    'CB1': best11['Def (Defensive)'][0],
    'CB2': best11['Def (Defensive)'][1],
    'LB': best11['Def (Attacking)'][1],
    'RB': best11['Def (Attacking)'][0],
    'CM1': best11['Mid (Defensive)'][0],
    'CM2': best11['Mid (Defensive)'][1],
    'CAM': best11['Mid (Attacking)'][1],
    'LW': best11['Mid (Attacking)'][2],
    'RW': best11['Mid (Attacking)'][0],
    'ST': best11['ST']
}

# Header
st.markdown(f"<h1 style='text-align:center; color:{PRIMARY};'>⚽️ Team Of The Season</h1>", unsafe_allow_html=True)
st.markdown("---")


st.subheader("Team Of The Season")


for role, idx in assigned_positions.items():
    name = df_hi.loc[idx, 'Player Name']
    x, y = positions[role]
    pitch.annotate(text=name, xy=(x, y), xytext=(x, y), 
                   ha='center', va='center', ax=ax, fontsize=7, color='black',
                   arrowprops={'facecolor': 'black', 'linewidth':0})

st.pyplot(fig)

# Initialize OpenRouter client for DeepSeek‑R1
client = OpenAI(
    api_key=api_key, 
    base_url="https://openrouter.ai/api/v1"
)

# Build a roster block from assigned_positions
lines = []
for role, idx in assigned_positions.items():
    name = df_hi.loc[idx, 'Player Name']
    lines.append(f"{role}: {name}")
roster_block = "\n".join(lines)

st.markdown("---")
st.subheader("Team Of The Season AI-Powered Summary")

if st.button("📝 Generate TOTS Description"):
    with st.spinner("Generating summary…"):
        prompt = (
            "You are a football analyst. Here is our 4-2-3-1 Team of the Season:\n\n"
            f"{roster_block}\n\n"
            "Write a concise 3–4 sentence summary explaining why each position was filled by these players—"
            "highlight their key strengths."
        )
        response = client.chat.completions.create(
            model="deepseek/deepseek-r1:free",
            messages=[
                {"role": "system", "content": "You are an expert football scout."},
                {"role": "user",   "content": prompt}
            ]
        )
        description = response.choices[0].message.content.strip()
        st.write(description)




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