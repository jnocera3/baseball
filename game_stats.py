#!/usr/bin/python
import argparse
import pandas as pd
import csv
import sys
import time
import os
import datetime
from pybaseball.league_batting_stats import batting_stats_range
from pybaseball.league_pitching_stats import pitching_stats_range

# Get current working directory
cwd = os.getcwd()

# Argument Parsing
parser = argparse.ArgumentParser()

# Read in arguments
parser.add_argument("-playerlist","--playerlist", required=True, help='File containing list of players')
parser.add_argument("-date","--date", required=False, default=datetime.date.today()-datetime.timedelta(days=1), help='Date to pull stats for in YYYY-MM-DD format')

# Parse the input
args = parser.parse_args()

# Store the date as datetime object
date = datetime.datetime.strptime(str(args.date), "%Y-%m-%d").date()
# Find previous and next dates
previous_date = str(date - datetime.timedelta(days=1))
next_date = str(date + datetime.timedelta(days=1))
# Set current date to type string
date = str(date)

# Store list of players
playerlist_file = str(args.playerlist)

# Define output file and links to files before and after current date
out_file = "stats_" + date + ".html"
previous_file = "file://" + cwd + "/stats_" + previous_date + ".html"
next_file = "file://" + cwd + "/stats_" + next_date + ".html"

# Get all pitching stats for input date
try:
    all_pitchers = pitching_stats_range(date)
    all_pitchers.drop(['Age', '#days', 'Lev', 'Date', 'Tm', 'Opp', 'W', 'L', 'ERA', 'GSc', 'AB', 'IBB', 'SF', 'Str', 'StL', 'StS', 'GB/FB', 'LD', 'PU', 'WHIP', 'BAbip', 'SO9', 'SO/W', 'mlbID'], axis=1, inplace=True) 
    all_pitchers.drop(all_pitchers.columns[1], axis=1, inplace=True)
    all_pitchers["SV"] = all_pitchers["SV"].fillna(0).astype(int)
except:
    all_pitchers = pd.DataFrame()

# Get all batting stats for input date
try: 
    all_batters = batting_stats_range(date)
    all_batters.drop(['Age', '#days', 'Lev', 'Date', 'Tm', 'Opp', 'G', 'PA', 'BA', 'OBP', 'SLG', 'OPS', 'mlbID'], axis=1, inplace=True) 
    all_batters.drop(all_batters.columns[1], axis=1, inplace=True)
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
#       print(player_type + " " + first_letter + " " + player_name + " " + letter_url)
#       print (player_url)
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
    print(batters)
    # Write out styled data to html table for batters
    styled_batters = batters.style.set_table_styles([
        {'selector': 'th', 'props': [('text-align', 'right'), ('border', 'none')]},
        {'selector': 'td', 'props': [('text-align', 'right'), ('border', 'none'), ('width', '50')]}
    ])
    html_batters_table = styled_batters.to_html()
else:
    html_batters_table = '<p>No batters hit on this day</p>\n'
if not pitchers.empty:
    pitchers.set_index('Name', inplace=True)
    pitchers.index.name = None
    #Set IP to 1 decimal place and ERA to 2 decimal places
    pitchers['IP'] = pitchers['IP'].astype(str)
    #pitchers['ERA'] = pitchers['ERA'].apply(lambda x: '{:,.2f}'.format(x))
    print(pitchers)
    # Write out styled data to html table for pitchers
    styled_pitchers = pitchers.style.set_table_styles([
        {'selector': 'th', 'props': [('text-align', 'right'), ('border', 'none')]},
        {'selector': 'td', 'props': [('text-align', 'right'), ('border', 'none'), ('width', '50')]}
    ])
    html_pitchers_table = styled_pitchers.to_html()
else:
    html_pitchers_table = '<p>No pitchers pitched on this day</p>\n'

# Create header for html file
html_header = '<center><a href="' + previous_file + '">Previous</a>&nbsp;<a href="' + next_file + '">Next</a>\n<h2>Stats for ' + date + '</h2></center>\n<b style="margin-left:10px">Batters</b>\n' 
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