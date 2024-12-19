
Movie Torrent Downloader
========================

This script allows you to scrape a Letterboxd user's watchlist and download torrents of movies from YTS.

Installation
------------

1. Install required libraries:
   
  .. code-block:: bash

    pip3 install requests beautifulsoup4 tqdm


Usage
-----

You can use this script in three different modes:

1. **Scraping a user's watchlist**: Use the `-u` flag followed by the Letterboxd username to scrape the user's watchlist.
2. **Using an existing CSV file**: Use the `-f` flag to specify the path to an existing CSV file containing movie details.
3. **Manual search**: Use the `-t` flag followed by the movie title and the `-y` flag followed by the year for a manual search.

Examples:

1. Scraping a user's watchlist:
   
  .. code-block:: bash

   python script.py -u <username>

2. Using an existing CSV file:
   
  .. code-block:: bash

   python script.py -f <file_path>

3. Manual search:
   
  .. code-block:: bash

   python script.py -t <movie_title> -y <year>

Options
-------
- `-u`, `--user`: Letterboxd username to scrape watchlist from.
- `-f`, `--file`: CSV file containing movies to download.
- `-t`, `--title`: Manually input the title of the movie.
- `-y`, `--year`: Manually input the year of the movie.
- `-o`, `--output-dir`: Directory to save torrents (default is "torrents" in the current directory).

Features
--------
- **Scrapes Letterboxd Watchlist**: Fetch movie details from a user's Letterboxd watchlist.
- **Downloads Torrents**: Downloads movie torrents from YTS, selecting the highest quality available (2160p > 1080p).
- **Error Handling**: Handles various errors like missing torrents, movie not found, and existing torrents.

File Output
-----------
The script will save the watchlist as a CSV file with the format:

  .. code-block:: text

    watchlist-<username>-<timestamp>-utc.csv

Each row in the CSV contains the following fields:

- **Name**: Name of the movie.
- **Year**: Year of the movie.
- **Letterboxd URI**: Link to the movie's page on Letterboxd.

Error Handling and Logs
------------------------
If a movie is missing or if there is any issue downloading the torrent, the script will output an error message and log the issue. Skipped movies and successfully downloaded movies are also logged.

