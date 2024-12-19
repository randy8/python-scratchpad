import csv
import random
import time
import os
from datetime import datetime
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

LETTERBOXD_BASE_URL = "https://letterboxd.com"
YTS_API_URL = "https://yts.mx/api/v2/"
TORRENT_DIRECTORY = os.getcwd()
EXISTING_MOVIES_DIRECTORY = os.getcwd() # Replace with actual directory
DEFAULT_OUTPUT_DIR = "./torrents"

def fetch_movie_year(slug):
    try:
        return BeautifulSoup(requests.get(f"{LETTERBOXD_BASE_URL}{slug}").content, "html.parser").select_one("a[href*='/films/year/']").text.strip() or "Unknown"
    except requests.RequestException as e:
        print(f"Error fetching year for {slug}: {e}")
        return "Unknown"

def extract_movie_data_from_poster(poster):
    try:
        slug = poster.select_one(".film-poster")["data-target-link"]
        return {"Name": poster.find("img")["alt"], "Year": fetch_movie_year(slug), "Letterboxd URI": f"{LETTERBOXD_BASE_URL}{slug}"}
    except Exception as e:
        print(f"Error processing poster: {e}")
        return None

def get_total_movies(user):
    total_movies, page_number = 0, 1
    while True:
        try:
            response = requests.get(f"https://letterboxd.com/{user}/watchlist/page/{page_number}/")
            soup = BeautifulSoup(response.content, "html.parser")
            posters = soup.select(".poster-container")
            if not posters:
                break
            total_movies += len(posters)
            if len(posters) < 20:
                break
            page_number += 1
        except requests.RequestException as e:
            print(f"Error fetching page {page_number}: {e}")
            break
    return total_movies

def scrape_watchlist(user, total_movies):
    movies, page_number = [], 1
    with tqdm(total=total_movies, desc=f"Scraping {user}'s watchlist", unit="movies") as pbar:
        while True:
            try:
                response = requests.get(f"https://letterboxd.com/{user}/watchlist/page/{page_number}/")
                soup = BeautifulSoup(response.content, "html.parser")
                posters = soup.select(".poster-container")
                if not posters:
                    break
                with ThreadPoolExecutor(max_workers=10) as executor:
                    future_to_poster = {executor.submit(extract_movie_data_from_poster, poster): poster for poster in posters}
                    for future in as_completed(future_to_poster):
                        movie_data = future.result()
                        if movie_data:
                            movies.append(movie_data)
                            pbar.update(1)
                time.sleep(1)
                if len(posters) < 20:
                    break
                page_number += 1
            except requests.RequestException as e:
                print(f"Error fetching page {page_number}: {e}")
                break
    return movies

def save_to_csv(movies, username):
    if not movies:
        print("No movies to save.")
        return
    filename = f"watchlist-{username}-{datetime.utcnow().strftime('%Y-%m-%d-%H-%M')}-utc.csv"
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["Name", "Year", "Letterboxd URI"])
        writer.writeheader()
        writer.writerows(movies)
    print(f"Saved {len(movies)} movies to {filename}.")
    return filename

def read_csv(file_path):
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        return [{"Name": row["Name"], "Year": int(row["Year"]), "Letterboxd URI": row["Letterboxd URI"]} for row in reader]

def get_movie_data(title, year):
    try:
        response = requests.get(f"{YTS_API_URL}list_movies.json", params={"query_term": title})
        response.raise_for_status() 
        data = response.json()

        if "data" in data and "movies" in data["data"]:
            return next(
                (movie for movie in data["data"]["movies"]
                 if movie["title"].lower() == title.lower() and movie["year"] == year),
                None
            )
        else:
            return None
    except requests.RequestException as e:
        print(f"Error fetching movie data from YTS API for {title} ({year}): {e}")
        return None
    except ValueError as e:
        print(f"Error parsing JSON response for {title} ({year}): {e}")
        return None

def get_best_quality_torrent(torrents):
    return next((torrent for torrent in torrents if torrent["quality"] == "2160p"), next((torrent for torrent in torrents if torrent["quality"] == "1080p"), None))

def download_torrent(torrent_url, movie_title, movie_year, missing_files, output_dir, downloaded_movies, skipped_movies):
    torrent_filename = f"{movie_title} ({movie_year}).torrent"
    torrent_file_path = os.path.join(output_dir, torrent_filename)

    if os.path.exists(torrent_file_path):
        print(f"Skipping {movie_title} ({movie_year}) as the torrent already exists in {output_dir}.")
        skipped_movies.append(f"{movie_title} ({movie_year})")
        return

    # Check if the movie already exists in the existing directory
    matched_dir = next(
        (existing_dir for existing_dir in os.listdir(EXISTING_MOVIES_DIRECTORY)
         if movie_title.lower() in existing_dir.lower() and os.path.isdir(os.path.join(EXISTING_MOVIES_DIRECTORY, existing_dir))),
        None
    )

    if matched_dir:
        print(f"Skipping {movie_title} ({movie_year}) since '{matched_dir}' already exists.")
        skipped_movies.append(f"{movie_title} ({movie_year})")
        return

    try:
        print(f"Downloading torrent for {movie_title} ({movie_year})...")
        response = requests.get(torrent_url, stream=True)
        response.raise_for_status()

        with open(torrent_file_path, "wb") as torrent_file:
            for chunk in response.iter_content(chunk_size=8192):
                torrent_file.write(chunk)
        print(f"Downloaded {movie_title} ({movie_year}) torrent to {output_dir}.")
        downloaded_movies.append(f"{movie_title} ({movie_year})")
    except requests.RequestException as e:
        print(f"Error downloading {movie_title} ({movie_year}): {str(e)}")
        missing_files.append({"title": movie_title, "year": movie_year, "error": str(e)})

def get_watchlist(args):
    """Reads or scrapes the watchlist based on arguments."""
    if args.file:
        if not os.path.exists(args.file):
            print(f"Error: File {args.file} does not exist.")
            return None
        print(f"Using existing watchlist file: {args.file}")
        return read_csv(args.file)

    if args.user:
        watchlist_file = f"watchlist-{args.user}-{datetime.now().strftime('%Y-%m-%d-%H-%M')}.csv"
        if os.path.exists(watchlist_file):
            print(f"Watchlist file {watchlist_file} already exists. Skipping extraction.")
            return read_csv(watchlist_file)
        else:
            total_movies = get_total_movies(args.user)
            print(f"Total number of movies to scrape: {total_movies}")
            movies = scrape_watchlist(args.user, total_movies)
            save_to_csv(movies, args.user)
            return movies
    elif args.title and args.year:
        print(f"Searching for {args.title} ({args.year})...")
        return [{"Name": args.title, "Year": args.year, "Letterboxd URI": "Manual Search"}]
    else:
        print("Error: You must provide either a Letterboxd username (-u), a watchlist file (-f), or a movie title (-t) and year (-y) for manual search.")
        return None

def process_movie(movie, missing_files, skipped_movies, downloaded_movies, output_dir):
    movie_data = get_movie_data(movie["Name"], int(movie["Year"]))

    if movie_data:
        print(f"Found movie in {EXISTING_MOVIES_DIRECTORY}: {movie_data['title']} ({movie_data['year']})")
        best_torrent = get_best_quality_torrent(movie_data["torrents"])

        if best_torrent:
            torrent_url = best_torrent["url"]
            torrent_filename = f"{movie['Name']} ({movie['Year']}).torrent"
            torrent_file_path = os.path.join(output_dir, torrent_filename)

            if os.path.exists(torrent_file_path):
                print(f"Skipping {movie['Name']} ({movie['Year']}) as the torrent already exists in {output_dir}.")
                skipped_movies.append(f"{movie['Name']} ({movie['Year']}) - Torrent already exists.")
            else:
                download_torrent(torrent_url, movie["Name"], int(movie["Year"]), missing_files, output_dir)
                downloaded_movies.append(f"{movie['Name']} ({movie['Year']})")
        else:
            skipped_movies.append(f"{movie['Name']} ({movie['Year']}) - No suitable quality found.")
    else:
        missing_files.append({"title": movie["Name"], "year": movie["Year"], "error": "Not found."})

def display_summary(missing_files, skipped_movies, downloaded_movies):
    print("\n-----------------------------------------")
    print(" Processing Complete ")
    print("-----------------------------------------")

    if downloaded_movies:
        print(f"\n✅ Downloaded {len(downloaded_movies)} movie{'s' if len(downloaded_movies) > 1 else ''}:")
        for movie in downloaded_movies:
            print(f"  - {movie}")
    else:
        print("\n❌ No movies were downloaded.")

    if skipped_movies:
        print(f"\n🔍 Skipped {len(skipped_movies)} movie{'s' if len(skipped_movies) > 1 else ''}:")
        for movie in skipped_movies:
            print(f"  - {movie}")
    else:
        print("\n❌ No movies were skipped.")

    if missing_files:
        print(f"\n⚠️ Missing {len(missing_files)} movie{'s' if len(missing_files) > 1 else ''}:")
        for movie in missing_files:
            print(f"  - {movie['title']} ({movie['year']}) - Error: {movie['error']}")
    else:
        print("\n❌ No missing movies.")

def parse_arguments():
    parser = argparse.ArgumentParser(description="Scrape a Letterboxd user's watchlist or manually search for movies and download torrents.")
    parser.add_argument("-u", "--user", help="Letterboxd username to scrape watchlist from.")
    parser.add_argument("-f", "--file", help="CSV file containing movies to download.")
    parser.add_argument("-t", "--title", help="Manually input the title of the movie.")
    parser.add_argument("-y", "--year", type=int, help="Manually input the year of the movie.")
    parser.add_argument("-o", "--output-dir", default=DEFAULT_OUTPUT_DIR, help="Directory to save torrents.")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()

    missing_files, skipped_movies, downloaded_movies = [], [], []
    output_dir = TORRENT_DIRECTORY
    watchlist = get_watchlist(args)

    if watchlist:
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(process_movie, movie, missing_files, skipped_movies, downloaded_movies, output_dir) for movie in watchlist]
            for future in as_completed(futures):
                pass

    display_summary(missing_files, skipped_movies, downloaded_movies)
    