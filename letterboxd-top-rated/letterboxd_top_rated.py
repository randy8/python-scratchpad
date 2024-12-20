import requests
from bs4 import BeautifulSoup
import argparse
import csv
import os
from datetime import datetime
from tqdm import tqdm

def fetch_page(url, headers):
    """Fetches a page and returns the HTML content if successful."""
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.text
        print(f"Failed to fetch {url}. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return None

def scrape_page(film_soup):
    """Extracts film details from a single BeautifulSoup object."""
    films = []
    for film in film_soup.select('li.poster-container'):
        title = film.find('img')['alt'] if film.find('img') else "Unknown"
        link_tag = film.find('a')
        link = f"https://letterboxd.com{link_tag['href']}" if link_tag and 'href' in link_tag.attrs else "Unknown"
        rating_tag = film.find('span', class_='rating')

        rating = None
        if rating_tag:
            rating_stars = rating_tag.text.strip()
            rating = rating_stars.count('★')  # Convert '★★★★★' to the number of stars
        
        if rating == 5:  # Only keep films rated exactly 5
            films.append({'title': title, 'link': link, 'rating': rating})
    
    return films

def scrape_letterboxd(user):
    """Scrapes films rated exactly 5 stars from all pages of Letterboxd."""
    base_url = f"https://letterboxd.com/{user}/films/rated/5/page/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    films = []
    page = 1
    while True:
        # Fetch the page
        page_url = f"{base_url}{page}/"  # Construct the page URL
        page_content = fetch_page(page_url, headers)
        
        if page_content:
            soup = BeautifulSoup(page_content, 'html.parser')
            page_films = scrape_page(soup)
            if not page_films:  # If no films are found, break the loop (end of pagination)
                print(f"No more films on page {page}. Ending scraping.")
                break

            films.extend(page_films)
            page += 1  # Go to the next page
        else:
            break

    return films

def read_csv_for_5_star_films(filename):
    """Reads a CSV file and returns films with a 5-star rating."""
    films = []
    if os.path.exists(filename):
        with open(filename, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if int(row['rating']) == 5:  # Only 5-star films
                    films.append({'title': row['title'], 'link': row['link'], 'rating': row['rating']})
    return films

def find_mutual_films(films_user1, films_user2):
    """Finds mutual 5-star films between two users, comparing only title and rating."""
    # Use sets of tuples (title, rating) for comparison
    user1_titles_and_ratings = set((film['title'], film['rating']) for film in films_user1)  # No lowercase conversion
    user2_titles_and_ratings = set((film['title'], film['rating']) for film in films_user2)

    # Find mutual films by intersecting the sets
    mutual_films = user1_titles_and_ratings & user2_titles_and_ratings
    return [{'title': title, 'rating': rating} for title, rating in mutual_films]

def save_mutual_films(mutual_films, users):
    """Saves the mutual 5-star films to a CSV file and displays mutual count."""
    if mutual_films:
        # Calculate mutual count
        mutual_count = len(mutual_films)
        print(f"Found {mutual_count} mutual 5-star films.")

        filename = f"mutual_5_star_films_{'_'.join(users)}_{datetime.utcnow().strftime('%Y-%m-%d-%H-%M')}-utc.csv"
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            fieldnames = ["title", "rating"]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for film in mutual_films:
                writer.writerow(film)
        print(f"Mutual 5-star films saved to {filename}")
    else:
        print("No mutual 5-star films found.")

def main(users):
    """Main function to scrape, find mutual films, and save the 5-star films for the given users."""
    user_films = {}

    # Scrape the 5-star films for each user and store them
    for user in users:
        print(f"Scraping films for user: {user}")
        user_films[user] = scrape_letterboxd(user)

    if len(users) == 1:
        # If only one user is provided, save their 5-star films
        filename = f"user_5_star_films-{users[0]}-{datetime.utcnow().strftime('%Y-%m-%d-%H-%M')}-utc.csv"
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            fieldnames = ["title", "link", "rating"]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for film in user_films[users[0]]:
                writer.writerow(film)
        print(f"5-star films saved to {filename}.")
    
    elif len(users) > 1:
        # If multiple users are provided, compare their films
        mutual_films = find_mutual_films(user_films[users[0]], user_films[users[1]])
        save_mutual_films(mutual_films, users)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare and save mutual 5-star films for users on Letterboxd.")
    parser.add_argument('-u', '--user', action='append', required=True, help="Letterboxd username(s) of the user(s).")
    args = parser.parse_args()
    main(args.user)
