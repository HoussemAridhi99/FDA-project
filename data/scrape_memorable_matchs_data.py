from understatapi import UnderstatClient
import pandas as pd

# Initialize Understat client
understat = UnderstatClient()

# Input list of memorable matches
memorable_performances_2024_25 = [
    ("Arsenal", 23, "5–1 thrashing of Manchester City at the Emirates"),
    ("Aston Villa", 32, "4–1 victory over Newcastle United"),
    ("Bournemouth", 9, "2–1 upset win over Manchester City on November 2, 2024—ended City's 32-match unbeaten streak"),
    ("Brentford", 8, "Dramatic 4–3 late win over Ipswich"),
    ("Brighton", 10, "2-1 comeback win vs Manchester City"),
    ("Chelsea", 5, "Cole Palmer's four-goal first-half performance in a 4–2 win over Brighton on September 28, 2024"),
    ("Crystal Palace", 26, "4–1 victory over Aston Villa on February 25, 2025—Ismaïla Sarr's birthday double"),
    ("Everton", 23, "2–2 Merseyside Derby draw against Liverpool on February 12, 2025—Tarkowski's 98th-minute volley"),
    ("Fulham", 30, "3-2 Home win against Liverpool"),
    ("Ipswich", 18, "2–0 win over Chelsea at Portman Road on December 30, 2024—Liam Delap scored and assisted"),
    ("Leicester", 36, "2-0 win vs Ipswich, Vardy scores 200th goal for Leicester at his last game at home"),
    ("Liverpool", 33, "5–1 destruction of Tottenham on April 27, 2025—clinched title with emphatic home display"),
    ("Manchester City", 31, "5–2 comeback win against Crystal Palace on April 12, 2025—mounted dramatic turnaround"),
    ("Manchester United", 15, "Amad Diallo's late winner to win away in the Manchester Derby"),
    ("Newcastle United", 16, "Alexander Isak's hat-trick in a 4–0 win at Ipswich"),
    ("Nottingham Forest", 23, "Record 7–0 victory against Brighton on February 1, Chris Wood hat-trick"),
    ("Southampton", 11, "3–2 loss vs Liverpool, they tried at least..."),
    ("Tottenham", 5, "Destroying Manchester United 3-0 at Old Trafford"),
    ("West Ham", 35, "Victory vs Manchester United 2-0 at Old Trafford"),
    ("Wolverhampton Wanderers", 11, "Cunha amazing performance and destroying Fulham 1-4 away from home")
]

# Helper function to transform match data
def transform_match_data(match_data, team, description):
    is_home = match_data['team_h'] == team
    opponent = match_data['team_a'] if is_home else match_data['team_h']
    
    return {
        "team": team,
        "opponent": opponent,
        "venue": "home" if is_home else "away",
        "date": match_data["date"],
        "score": f"{match_data['h_goals']}–{match_data['a_goals']}" if is_home else f"{match_data['a_goals']}–{match_data['h_goals']}",
        "xg": round(float(match_data['h_xg']) if is_home else float(match_data['a_xg']), 3),
        "xga": round(float(match_data['a_xg']) if is_home else float(match_data['h_xg']), 3),
        "shots": int(match_data['h_shot']) if is_home else int(match_data['a_shot']),
        "shots_against": int(match_data['a_shot']) if is_home else int(match_data['h_shot']),
        "shots_on_target": int(match_data['h_shotOnTarget']) if is_home else int(match_data['a_shotOnTarget']),
        "shots_on_target_against": int(match_data['a_shotOnTarget']) if is_home else int(match_data['h_shotOnTarget']),
        "ppda": round(float(match_data['h_ppda']) if is_home else float(match_data['a_ppda']), 3),
        "ppda_against": round(float(match_data['a_ppda']) if is_home else float(match_data['h_ppda']), 3),
        "description": description
    }

# Collect all transformed matches
transformed_rows = []

# Loop through matches and process
for team, index, description in memorable_performances_2024_25:
    try:
        team_matches = understat.team(team=team).get_match_data(season="2024")
        match_id = team_matches[index]["id"]
        match_data = understat.match(match=match_id).get_match_info()
        
        row = transform_match_data(match_data, team, description)
        transformed_rows.append(row)
        print(f"✓ Processed: {team} (match #{index})")
    
    except Exception as e:
        print(f"✗ Failed: {team} (match #{index}) — {e}")

# Save all to CSV
df = pd.DataFrame(transformed_rows)
df.to_csv("memorable_performances_2024_25.csv", index=False)

print("✅ Saved to memorable_performances_2024_25.csv")
