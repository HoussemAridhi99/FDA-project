import pandas as pd

df = pd.read_csv("data/players_data/epl_player_stats_24_25.csv")

df.loc[df["Club"] == "Brighton", "Club"] = "Brighton & Hove Albion"

df.loc[df["Club"] == "Brighton & Hove Albion", "Club"] = "Brighton"

df.loc[df["Club"] == "Ipswich Town", "Club"] = "Ipswich"

df.loc[df["Club"] == "Leicester City", "Club"] = "Leicester"

df.loc[df["Club"] == "Tottenham Hotspur", "Club"] = "Tottenham"

df.loc[df["Club"] == "West Ham United", "Club"] = "West Ham"

df.to_csv("data/players_data/epl_player_stats_2024_25.csv")