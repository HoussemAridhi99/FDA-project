import pandas as pd

teams = [
    "Arsenal", "Aston Villa", "Bournemouth", "Brentford", "Brighton",
    "Chelsea", "Crystal Palace", "Everton", "Fulham", "Liverpool",
    "Manchester City", "Manchester United", "Newcastle United", "Nottingham Forest", "Southampton",
    "Tottenham", "West Ham", "Wolverhampton Wanderers", "Leicester", "Ipswich"
]

for team in teams:
    # build filenames
    key = team.lower().replace(' ', '_').replace('/', '_')
    raw_file   = f"data/team_csvs/{key}_data.csv"   # e.g. arsenal_data.csv
    stats_file = f"data/team_csvs/{key}_stats.csv"  # e.g. arsenal_stats.csv

    try:
        # load both datasets
        df_raw   = pd.read_csv(raw_file)
        df_stats = pd.read_csv(stats_file)

        # make sure stats has a 'gw' column
        # (if you named it something else, adjust here)
        if 'gw' not in df_stats.columns:
            raise ValueError(f"`{stats_file}` missing 'gw' column")

        # merge on Round (raw) == gw (stats)
        df_combined = df_raw.merge(
            df_stats,
            left_on='Round',
            right_on='gw',
            how='left',
            suffixes=('', '_stats')
        )

        # optionally drop the duplicate 'gw' column if you don't need both
        df_combined.drop(columns=['gw'], inplace=True)

        # save combined file
        out_file = f"data/team_data/{key}_combined.csv"
        df_combined.to_csv(out_file, index=False)
        print(f"✓ {team}: wrote {out_file}")

    except FileNotFoundError as fnf:
        print(f"✗ {team}: missing file – {fnf.filename}")
    except Exception as e:
        print(f"✗ {team}: error – {e}")
