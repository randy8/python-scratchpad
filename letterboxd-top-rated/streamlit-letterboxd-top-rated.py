import requests
from bs4 import BeautifulSoup
import csv
import pandas as pd
from datetime import datetime
import streamlit as st
from io import StringIO

def fetch_page(url, headers):
    """Fetches a page and returns the HTML content if successful."""
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching {url}: {e}")
        return None

def scrape_films(page_content):
    """Extracts films rated exactly 5 stars from page content."""
    soup = BeautifulSoup(page_content, 'html.parser')
    return [
        {'title': film.find('img')['alt'] if film.find('img') else "Unknown",
         'link': f"https://letterboxd.com{film.find('a')['href']}" if film.find('a') else "Unknown",
         'rating': 5}
        for film in soup.select('li.poster-container')
        if film.find('span', class_='rating') and film.find('span', class_='rating').text.strip() == '★★★★★'
    ]

def get_user_films(user):
    """Fetches all 5-star films for the user."""
    base_url = f"https://letterboxd.com/{user}/films/rated/5/page/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    films = []
    page = 1

    while True:
        page_content = fetch_page(f"{base_url}{page}/", headers)
        if not page_content:
            break
        films_on_page = scrape_films(page_content)
        if not films_on_page:
            break
        films.extend(films_on_page)
        page += 1

    return films

def find_mutual_films(films1, films2):
    """Finds the intersection of two film lists."""
    return [film for film in films1 if film in films2]

def save_films_to_csv(films, filename):
    """Saves films to CSV and provides download functionality."""
    if films:
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=["title", "link", "rating"])
        writer.writeheader()
        writer.writerows(films)
        
        output.seek(0)
        df = pd.read_csv(output)
        st.dataframe(df)  # Display the CSV content inline

        st.download_button("Download CSV", data=output.getvalue(), file_name=filename, mime="text/csv")
    else:
        st.write("No films found.")

def main():
    st.title("Letterboxd Top Ratings")

    users_input = st.text_area("Enter Letterboxd username(s), separated by commas:", "")
    if users_input:
        users = [user.strip() for user in users_input.split(",")]

        user_films = {user: get_user_films(user) for user in users}
        
        if len(users) == 1:
            filename = f"{users[0]}_5_star_films_{datetime.utcnow().strftime('%Y-%m-%d-%H-%M')}.csv"
            save_films_to_csv(user_films[users[0]], filename)
        elif len(users) > 1:
            mutual_films = find_mutual_films(user_films[users[0]], user_films[users[1]])
            filename = f"mutual_5_star_films_{'_'.join(users)}_{datetime.utcnow().strftime('%Y-%m-%d-%H-%M')}.csv"
            save_films_to_csv(mutual_films, filename)

if __name__ == "__main__":
    main()
