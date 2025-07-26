import pandas as pd
import os

# 1. Load raw match data and parse dates
df = pd.read_csv('data/E0.csv', parse_dates=['Date'], dayfirst=True)

# 2. Build long-format matches (one row per team per match)
home = df[['Date','HomeTeam','AwayTeam','FTHG','FTAG','FTR']].copy()
away = df[['Date','AwayTeam','HomeTeam','FTAG','FTHG','FTR']].copy()

home.columns = ['Date','Team','Opponent','GF','GA','FTR']
away.columns = ['Date','Team','Opponent','GF','GA','FTR']

matches = pd.concat([home, away], ignore_index=True)

# 3. Sort per team by Date, then assign Round = occurrence index
matches = matches.sort_values(['Team','Date']).reset_index(drop=True)
matches['Round'] = matches.groupby('Team').cumcount() + 1

# 4. Calculate match points and cumulative stats
matches['MatchPoints'] = matches.apply(
    lambda r: 3 if r.GF > r.GA else (1 if r.GF == r.GA else 0), axis=1
)
matches['TotalPoints']            = matches.groupby('Team')['MatchPoints'].cumsum()
matches['GoalsForCumulative']     = matches.groupby('Team')['GF'].cumsum()
matches['GoalsAgainstCumulative'] = matches.groupby('Team')['GA'].cumsum()

# 5. Compute league position at each Round
positions = []
for rnd in sorted(matches['Round'].unique()):
    snap = (
        matches[matches['Round']==rnd]
        .groupby('Team')
        .agg({
            'TotalPoints'           : 'max',
            'GoalsForCumulative'    : 'max',
            'GoalsAgainstCumulative': 'max'
        })
        .reset_index()
    )
    snap['GD'] = snap.GoalsForCumulative - snap.GoalsAgainstCumulative
    snap = snap.sort_values(
        ['TotalPoints','GD','GoalsForCumulative'],
        ascending=False
    )
    snap['Position'] = range(1, len(snap)+1)
    snap['Round']    = rnd
    positions.append(snap[['Round','Team','Position']])

league = pd.concat(positions)

# 6. Merge back to get full detailed table
detailed = matches.merge(
    league, on=['Round','Team'], how='left'
)[[
    'Round','Team','MatchPoints','TotalPoints',
    'GF','GA','GoalsForCumulative',
    'GoalsAgainstCumulative','Position'
]]

# 7. Export one CSV per team
out_dir = 'data/team_csvs'
os.makedirs(out_dir, exist_ok=True)
for team, df_team in detailed.groupby('Team'):
    df_team = df_team.sort_values('Round')
    safe_name = team.replace('/', '_')
    df_team.to_csv(f"{out_dir}/{safe_name}_data.csv", index=False)

print(f"Per-team CSVs saved to {out_dir}")
