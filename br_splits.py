#!/usr/bin/python
import requests
import argparse
import pandas as pd
import csv
import sys
import time
from pybaseball.split_stats import get_splits
from bs4 import BeautifulSoup
from urllib.parse import *

def find_url(url, playername):
    try:
        response = requests.get(url)
    except:
        print(f"Request failed {url}")
        return
#   print(response.request.headers)
#   print(response.text)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
#       print (soup)
        print ("Searching for " + playername)
#       playerurl = soup.find('a', string=playername).attrs["href"]
        players_active = soup.find_all('b')
        for player in players_active:
            playerurl = player.find('a', string=playername)
            if playerurl:
                print("Found: " + str(playerurl["href"]))
                return url + "/" + playerurl["href"].split('/')[3]
#       No player found. Return input url
        return "Missing"

# Argument Parsing
parser = argparse.ArgumentParser()

# Read in arguments
parser.add_argument("-url","--url", required=False, default="https://www.baseball-reference.com", help='URL to scrape')
parser.add_argument("-year","--year", type=int, required=True, help='Year to pull stats for')
parser.add_argument("-playerlist","--playerlist", required=True, help='File containing list of players')
parser.add_argument("-outfile","--outfile", required=True, help='Name of file to output player stats to')

# Parse the input
args = parser.parse_args()

# Store the arguments
url = str(args.url)
year = args.year
playerlist_file = str(args.playerlist)
out_file = str(args.outfile)

# Define search string for player totals
player_totals = str(year) + " Totals"

# Open output file
f = open(out_file, "w")

# Read player list file
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
        first_letter = row[0][0:1].lower()
        player_name = row[1].strip() + " " + row[0].strip()
        # Construct URL to search for player page
        letter_url = url + "/players/" + first_letter
#       print(player_type + " " + first_letter + " " + player_name + " " + letter_url)
        # Find player url
        player_url = find_url(letter_url,player_name)
#       print (player_url)
        if player_url != "Missing":
            # Extract out player id
            player_id = player_url.split('/')[-1].split('.')[0]
            print ("Player ID: " + str(player_id))
            # Create header with link for html table
            html_header = '<h2><a href="' + player_url + '" target="_blank">' + player_name + "</a></h2>\n"
            # Store splits in a dataframe
            if player_type == "P":
                df = get_splits(player_id, year=year, pitching_splits=True)[0]
                df_pitch = get_splits(player_id, year=year, pitching_splits=True)[1]
            else: 
                df = get_splits(player_id, year=year)
        else:
            print (player_name + " not found at " + url + ". Check to make sure player name is correct.")
            sys.exit(1)
        # Attempt to extract out season totals
        if player_totals in df.loc['Season Totals'].index:
            totals = pd.Series(df.loc['Season Totals'].loc[player_totals],name=player_totals)
            # Extract out platoon splits
            if player_type == "P":
                platoon = df.loc['Platoon Splits'].loc[['vs RHB','vs LHB']]
                totals_pitch = pd.Series(df_pitch.loc['Season Totals -- Game-Level'].loc[player_totals],name=player_totals)
                totals = pd.concat([totals,totals_pitch[["GS","ERA"]]])
                
                platoon["GS"] = [totals_pitch["GS"], totals_pitch["GS"]]
                platoon = platoon.assign(GS=[totals_pitch["GS"], totals_pitch["GS"]], ERA=[totals_pitch["ERA"], totals_pitch["ERA"]])
            else: 
                positions = df.loc['Defensive Positions'][df.loc["Defensive Positions"]["G"] > 1].index.str.replace("as ","").to_list()
                if "PH for DH" in positions:
                    positions.remove("PH for DH")
                if "PH" in positions:
                    positions.remove("PH")
                positions = ','.join(positions)
                platoon = df.loc['Platoon Splits'].loc[['vs RHP','vs LHP']]
            # Store needed data in new dataframe
            splits = pd.DataFrame()
            #splits = splits.append(totals)
            splits = pd.concat([splits,totals.to_frame().T])
            # Merge stats into final dataframe
            splits = pd.concat([splits, platoon], ignore_index=False)
            # Convert some stats to integers
            splits[['BA', 'OBP', 'SLG', 'OPS']] = splits[['BA', 'OBP', 'SLG', 'OPS']] * 1000.0
            # Remove unneeded stats
            if player_type == "P":
                splits.drop(['PA', 'SO/W', 'TB', 'SH', 'SF', 'IBB', 'ROE', 'BAbip', 'tOPS+', 'sOPS+', '1B'], axis=1, inplace=True) 
                # Convert ERA to an integer
                splits['ERA'] = splits['ERA'] * 100.0
            else:
                splits.drop(['GS', 'PA', 'TB', 'SH', 'SF', 'IBB', 'ROE', 'BAbip', 'tOPS+', 'sOPS+', '1B'], axis=1, inplace=True) 
            # Convert entire dataframe to integers
            splits = splits.fillna(0).astype(int)
            # Convert ERA back to float
            if player_type == "P":
                splits['ERA'] = (splits['ERA'].astype(float) * 0.01).round(2).astype(str)
                # Rearrange columns
                cols = splits.columns.to_list()
                cols = [cols[0]] + cols[17:] + cols[1:17]
                splits = splits[cols]
            else:
                # Add positions for batters
                splits = splits.assign(Pos=[positions, "N/A", "N/A"])
            # Convert dataframe to html table
            styled_splits = splits.style.set_table_styles([
                {'selector': 'th', 'props': [('text-align', 'right'), ('border', 'none')]},
                {'selector': 'td', 'props': [('text-align', 'right'), ('border', 'none'), ('width', '50')]}
            ])
            html_table = styled_splits.to_html()
        else:
            # Add message to html file that no stats are available.
            html_table = '<b>Did not play MLB in ' + str(year) + '.</b>'
        # Add header to html table
        html_table = html_header + html_table
        # Write out data to output file
        f.write(html_table)
        # Sleep 10 seconds between requests to avoid being blocked
        time.sleep(10)

# Close output file
f.close()