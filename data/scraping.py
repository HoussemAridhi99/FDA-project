from understatapi import UnderstatClient
import pandas as pd

understat = UnderstatClient()

teams = [
    "Arsenal", "Aston Villa", "Bournemouth", "Brentford", "Brighton",
    "Chelsea", "Crystal Palace", "Everton", "Fulham", "Liverpool",
    "Manchester City", "Manchester United", "Newcastle United", "Nottingham Forest", "Southampton",
    "Tottenham", "West Ham", "Wolverhampton Wanderers", "Leicester", "Ipswich"
]

for team_name in teams:
    print(f'Processing {team_name}...')

    try:
        team_match_data = understat.team(team=team_name).get_match_data(season="2024")

        rows = []
        for gw, m in enumerate(team_match_data, start=1):
            side = m['side']
            xg = float(m['xG'][side])
            xga = float(m['xG']['h' if side == 'a' else 'a'])
            npxg = float(m.get('npxG', {}).get(side, None) or 0)
            npxga = float(m.get('npxG', {}).get('h' if side == 'a' else 'a', 0))
            fx = m['forecast']
            xpts = 3 * fx['w'] + 1 * fx['d']
            pts = 3 if m['result'] == 'w' else 1 if m['result'] == 'd' else 0
            xgd = xg - xga

            rows.append({
                'gw': gw,
                'xg': xg,
                'xga': xga,
                'npxg': npxg,
                'npxga': npxga,
                'xpts': round(xpts, 3),
                'result': m['result'],
                'pts': pts,
                'xgd': round(xgd, 3),
            })

        df = pd.DataFrame(rows)
        df['cum_xg'] = df['xg'].cumsum()
        df['cum_xga'] = df['xga'].cumsum()
        df['cum_pts'] = df['pts'].cumsum()

        df = df[['gw', 'xg', 'xga', 'npxg', 'npxga', 'xpts', 'result', 'pts', 'xgd', 'cum_xg', 'cum_xga', 'cum_pts']]

        # Sanitize filename (remove special characters, spaces to underscores)
        file_name = team_name.lower().replace(' ', '_').replace('/', '_') + '_stats.csv'
        df.to_csv(file_name, index=False)

        print(f'Done: {file_name}')
    except Exception as e:
        print(f'Error processing {team_name}: {e}')
