#!/usr/bin/python
import requests
import argparse
import pandas as pd
import csv
from bs4 import BeautifulSoup, Comment
from urllib.parse import *

def get_soup(url) -> BeautifulSoup:
    s = requests.get(url).content
    # a workaround to avoid beautiful soup applying the wrong encoding
    s = s.decode('utf-8')
    return BeautifulSoup(s, features="lxml")

def get_table(soup: BeautifulSoup) -> pd.DataFrame:
    # Stats are in comment section
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))
    # Loop through all comments to find stats
    for comment in comments:
        if "div_players_spring" in str(comment):
            # Store stats as soup object
            stats_soup=BeautifulSoup(comment, 'html.parser')
    table = stats_soup.find_all('table')[0]
    data = []
    headings = [th.get_text() for th in table.find("tr").find_all("th")][1:]
    headings.append("mlbID")
    data.append(headings)
    table_body = table.find('tbody')
    rows = table_body.find_all('tr')
    for row in rows:
        cols = row.find_all('td')
        row_anchor = row.find("a")
        mlbid = row_anchor["href"].split("mlb_ID=")[-1] if row_anchor else pd.NA  # ID str or nan
        cols = [ele.text.strip() for ele in cols]
        cols.append(mlbid)
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

# Parse the input
args = parser.parse_args()

# Store the arguments
year = str(args.year)
playerlist_file = str(args.playerlist)
out_file = str(args.outfile)

# Define urls for spring training stats
batting_stats = "https://www.baseball-reference.com/leagues/majors/" + year + "-spring-training-batting.shtml"
pitching_stats = "https://www.baseball-reference.com/leagues/majors/" + year + "-spring-training-pitching.shtml"

# Get all pitching stats for input date
try:
    stats = get_soup(pitching_stats)
    all_pitchers = get_table(stats)
    all_pitchers.drop(['Age', 'OppQual', 'GS', 'W', 'L', 'W-L%', 'GF', 'CG', 'SHO', 'SV', 'IBB', 'H9', 'BB9', 'SO9', 'SO/W', 'mlbID'], axis=1, inplace=True)
    all_pitchers["Name"] = all_pitchers["Name"].str.replace("\u00a0", " ").str.replace(r'[*#]','',regex=True)
except:
    all_pitchers = pd.DataFrame()

# Get all batting stats for input date
try:
    stats = get_soup(batting_stats)
    all_batters = get_table(stats)
    all_batters.drop(['Age', 'OppQual', 'GS', 'G', 'PA', 'TB', 'SH', 'SF', 'IBB', 'mlbID'], axis=1, inplace=True)
    all_batters["Name"] = all_batters["Name"].str.replace("\u00a0", " ").str.replace(r'[*#]','',regex=True)
except:
    all_batters = pd.DataFrame()

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
        if not all_batters.empty and player_type == "B" and all_batters['Name'].isin([player_name]).any():
#           print(all_batters[all_batters['Name'] == player_name])
            batters = pd.concat([batters,all_batters[all_batters['Name'] == player_name]])
        if not all_pitchers.empty and player_type == "P" and all_pitchers['Name'].isin([player_name]).any():
#           print(all_pitchers[all_pitchers['Name'] == player_name])
            pitchers = pd.concat([pitchers,all_pitchers[all_pitchers['Name'] == player_name]])

# If dataframe is populated set player name to dataframe index
if not batters.empty:
    batters.set_index('Name', inplace=True)
    batters.index.name = None
    # Remove DH from position listing
    batters["Pos Summary"] = batters["Pos Summary"].str.replace(r', DH-\d+','',regex=True).str.replace(r'DH-\d+, ','',regex=True)
    print(batters)
    # Write out styled data to html table for batters
    styled_batters = batters.style.set_table_styles([
        {'selector': 'th', 'props': [('text-align', 'right'), ('border', 'none')]},
        {'selector': 'td', 'props': [('text-align', 'right'), ('border', 'none'), ('width', '45')]}
    ])
    html_batters_table = styled_batters.to_html()
else:
    html_batters_table = '<p>No batters have hit yet in spring training</p>\n'
if not pitchers.empty:
    pitchers.set_index('Name', inplace=True)
    pitchers.index.name = None
    print(pitchers)
    # Write out styled data to html table for pitchers
    styled_pitchers = pitchers.style.set_table_styles([
        {'selector': 'th', 'props': [('text-align', 'right'), ('border', 'none')]},
        {'selector': 'td', 'props': [('text-align', 'right'), ('border', 'none'), ('width', '45')]}
    ])
    html_pitchers_table = styled_pitchers.to_html()
else:
    html_pitchers_table = '<p>No pitchers have pitched yet in spring training</p>\n'

# Create header for html file
html_header = '<h2>Spring Training Stats for ' + year + '</h2></center>\n<b style="margin-left:10px">Batters</b>\n' 
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