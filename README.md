# Baseball Player Stats Extractor
## Overview:

There are 2 codes here for pulling baseball statistics from baseball reference using the [pybaseball](https://github.com/jldbc/pybaseball) python package:

br_splits.py - pulls player total stats and split stats for a season and outputs them to an html file.
game_stats.py - pulls player stats for a day and outputs them to an html file

Users should supply a file containing a list of players. A sample, players.csv, is provided. It's important that the player name match exactly what is used by baseball reference otherwise the player will not be found. Accent marks are often needed.

It is recommended that the br_splits.py code is run first to check that all players are found. This code will alert for missed players. The game_stats.py code will not. 

Baseball reference limits the number of requests per minute so the br_splits.py sleeps 10 seconds between player request. Generally, assume the script will be able to pull about 5 players per minute.

## Installation:

```
git clone https://github.com/jnocera3/baseball.git
```

## Dependencies:

```
pip install pandas
pip install pybaseball
```

## Running the code:

### For Player Season Stats:

```
python br_splits.py -h
usage: br_splits.py [-h] [-url URL] -year YEAR -playerlist PLAYERLIST -outfile OUTFILE

options:
  -h, --help            show this help message and exit
  -url URL, --url URL   URL to scrape
  -year YEAR, --year YEAR
                        Year to pull stats for
  -playerlist PLAYERLIST, --playerlist PLAYERLIST
                        File containing list of players
  -outfile OUTFILE, --outfile OUTFILE
                        Name of file to output player stats to
```

The year to extract, file containing the player list and the output file name are all required.

Example for extraction player stats for 2024:
```
python br_splits.py -year 2024 -playerlist players.csv -outfile splits_2024.html
```

### For single game player stats:

```
python game_stats.py -h
usage: game_stats.py [-h] -playerlist PLAYERLIST [-date DATE]

options:
  -h, --help            show this help message and exit
  -playerlist PLAYERLIST, --playerlist PLAYERLIST
                        File containing list of players
  -date DATE, --date DATE
                        Date to pull stats for in YYYY-MM-DD format
```

The file containing the player list is required here. If no -date option is provided, stats are provided for the previous day. Output will be placed in: stats_YYYY-MM-DD.html

Example for pulling player game stats for 2024-08-05:
```
python game_stats.py -date 2024-08-05 -playerlist players.csv
```
Output will be placed in: stats_2024-08-05.html