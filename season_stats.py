#!/usr/bin/python
import requests
import argparse
import pandas as pd
import csv
import sys
from bs4 import BeautifulSoup, Comment
from urllib.parse import *

def get_soup(url) -> BeautifulSoup:
    s = requests.get(url).content
    # a workaround to avoid beautiful soup applying the wrong encoding
    s = s.decode('utf-8')
    return BeautifulSoup(s, features="lxml")

def get_table(soup: BeautifulSoup, table_id: str) -> pd.DataFrame:
    # Get spring stats if requested
    if table_id == "div_players_spring":
        # Stats are in comment section
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        # Loop through all comments to find stats
        for comment in comments:
            if "div_players_spring" in str(comment):
                # Store stats as soup object
                stats_soup=BeautifulSoup(comment, 'html.parser')
        table = stats_soup.find_all('table')[0]
    # Regular season stats
    else:
        table = soup.find('table', attrs={'id': table_id})
    data = []
    headings = [th.get_text() for th in table.find("tr").find_all("th")][1:]
    data.append(headings)
    table_body = table.find('tbody')
    rows = table_body.find_all('tr')
    for row in rows:
        cols = row.find_all('td')
        row_anchor = row.find("a")
        cols = [ele.text.strip() for ele in cols]
        data.append([ele for ele in cols])
    df = pd.DataFrame(data)
    df = df.rename(columns=df.iloc[0])
    df = df.reindex(df.index.drop(0))
    return df

# Argument Parsing
parser = argparse.ArgumentParser()

# Read in arguments
parser.add_argument("-year","--year", type=int, required=True, help='Year to pull stats for')
parser.add_argument("-playerlist","--playerlist", required=True, help='File containing list of players')
parser.add_argument("-outfile","--outfile", required=True, help='Name of file to output player stats to')
parser.add_argument("-spring_stats","--spring_stats", action='store_true', help='Get spring stats instead of regular season stats')

# Parse the input
args = parser.parse_args()

# Store the arguments
year = str(args.year)
playerlist_file = str(args.playerlist)
out_file = str(args.outfile)

# Define urls for stats to get
if args.spring_stats:
    # Spring Stats
    batting_stats = "https://www.baseball-reference.com/leagues/majors/" + year + "-spring-training-batting.shtml"
    pitching_stats = "https://www.baseball-reference.com/leagues/majors/" + year + "-spring-training-pitching.shtml"
    player_or_name = "Name"
    stats_season = "Spring Training"
else:
    # Regular Season Stats
    batting_stats = "https://www.baseball-reference.com/leagues/majors/" + year + "-standard-batting.shtml"
    pitching_stats = "https://www.baseball-reference.com/leagues/majors/" + year + "-standard-pitching.shtml"
    player_or_name = "Player"
    stats_season = "Regular Season"

# Get all pitching stats for input date
try:
    stats = get_soup(pitching_stats)
    if args.spring_stats:
        all_pitchers = get_table(stats, "div_players_spring")
    else:
        all_pitchers = get_table(stats, "players_standard_pitching")
    all_pitchers.drop(['Age', 'OppQual', 'Lg', 'W', 'L', 'W-L%', 'GF', 'BF', 'ERA+', 'IBB', 'H9', 'BB9', 'SO9', 'SO/W', 'SO/BB', 'mlbID', 'Awards'], axis=1, inplace=True, errors='ignore')
    all_pitchers[player_or_name] = all_pitchers[player_or_name].str.replace("\u00a0", " ").str.replace(r'[*#]','',regex=True)
    all_pitchers.drop_duplicates(subset=[player_or_name], keep='first', inplace=True)
except:
    all_pitchers = pd.DataFrame()

#print(all_pitchers)
# Get all batting stats for input date
try:
    stats = get_soup(batting_stats)
    if args.spring_stats:
        all_batters = get_table(stats, "div_players_spring")
    else:
        all_batters = get_table(stats, "players_standard_batting")
    all_batters.drop(['Age', 'OppQual', 'Lg', 'GS', 'PA', 'TB', 'OPS+', 'rOBA', 'Rbat+', 'SH', 'SF', 'IBB', 'mlbID', 'Awards'], axis=1, inplace=True, errors='ignore')
    all_batters[player_or_name] = all_batters[player_or_name].str.replace("\u00a0", " ").str.replace(r'[*#]','',regex=True)
    all_batters.drop_duplicates(subset=[player_or_name], keep='first', inplace=True)
except:
    all_batters = pd.DataFrame()

#print(all_batters)

# Define dataframes for storing batter and pitcher stats
batters = pd.DataFrame()
pitchers = pd.DataFrame()

# Loop over player list
with open(playerlist_file, encoding='utf-8') as csvfile:

    # Skips the headersg
    # Using next() method
    next(csvfile)
    next(csvfile)

    # Create reader object by passing the file
    # object to reader method
    reader_obj = csv.reader(csvfile)

    # Iterate over each row in the csv file
    # using reader object
    for row in reader_obj:
        player_type = row[2].strip().upper()
        player_name = row[1].strip() + " " + row[0].strip()
#       Check to see if player played
        if not all_batters.empty and player_type == "B" and all_batters[player_or_name].isin([player_name]).any():
#           print(all_batters[all_batters[player_or_name] == player_name])
            batters = pd.concat([batters,all_batters[all_batters[player_or_name] == player_name]])
        if not all_pitchers.empty and player_type == "P" and all_pitchers[player_or_name].isin([player_name]).any():
#           print(all_pitchers[all_pitchers[player_or_name] == player_name])
            pitchers = pd.concat([pitchers,all_pitchers[all_pitchers[player_or_name] == player_name]])

# If dataframe is populated set player name to dataframe index
if not batters.empty:
    batters.set_index(player_or_name, inplace=True)
    batters.index.name = None
    # Remove DH or unwanted chars from position listing
    if args.spring_stats:
        batters["Pos Summary"] = batters["Pos Summary"].str.replace(r', DH-\d+','',regex=True).str.replace(r'DH-\d+, ','',regex=True)
    else:
        batters["Pos"] = batters["Pos"].str.replace(r'[DH/*]','',regex=True)
    print(batters)
    # Write out styled data to html table for batters
    styled_batters = batters.style.set_table_styles([
        {'selector': 'th', 'props': [('text-align', 'right'), ('border', 'none')]},
        {'selector': 'td', 'props': [('text-align', 'right'), ('border', 'none'), ('width', '45')]}
    ])
    html_batters_table = styled_batters.to_html()
else:
    html_batters_table = '<p>No batters have hit yet</p>\n'
if not pitchers.empty:
    pitchers.set_index(player_or_name, inplace=True)
    pitchers.index.name = None
    print(pitchers)
    # Write out styled data to html table for pitchers
    styled_pitchers = pitchers.style.set_table_styles([
        {'selector': 'th', 'props': [('text-align', 'right'), ('border', 'none')]},
        {'selector': 'td', 'props': [('text-align', 'right'), ('border', 'none'), ('width', '45')]}
    ])
    html_pitchers_table = styled_pitchers.to_html()
else:
    html_pitchers_table = '<p>No pitchers have pitched yet</p>\n'

# Create header for html file
html_header = '<h2>' + stats_season + ' Stats for ' + year + '</h2></center>\n<b style="margin-left:10px">Batters</b>\n' 
# Add header to html batters table
html_table = html_header + html_batters_table
# Add header for pitchers
html_table = html_table + '<br><br><b style="margin-left:10px">Pitchers</b>\n'
# Add html pitchers table
html_table = html_table + html_pitchers_table

# Open output file
f = open(out_file, "w")
# Read player list file
# Write out data to output file
f.write(html_table)
# Close output file
f.close()
