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

def scrape_films(user, page_content):
    """Extracts films rated exactly 5 stars from page content."""
    soup = BeautifulSoup(page_content, 'html.parser')
    return [
        {
            'title': film.find('img')['alt'] if film.find('img') else "Unknown",
            'user_review': f"https://letterboxd.com{film.find('a')['href']}" if film.find('a') else "Unknown",
            'rating': 5
        }
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
        films_on_page = scrape_films(user, page_content)
        if not films_on_page:
            break
        films.extend(films_on_page)
        page += 1

    return films

def find_mutual_films(films_dict, users):
    """Finds mutual films and includes both users' review links."""
    mutual_films = []

    if len(users) == 1:
        user1 = users[0]
        mutual_films = [{'title': film['title'], f"{user1}_review": film['user_review'], 'rating': 5} for film in films_dict.get(user1, [])]
        return mutual_films

    user1 = users[0]
    user1_titles = {film['title'].strip() for film in films_dict.get(user1, [])}

    mutual_titles = user1_titles  # Initialize mutual_titles with the first user's films

    # Loop through other users and find mutual titles
    for user in users[1:]:
        user_titles = {film['title'].strip() for film in films_dict.get(user, [])}
        mutual_titles &= user_titles

    for title in mutual_titles:
        mutual_film = {'title': title, 'rating': 5}
        for user in users:
            mutual_film[f"{user}_review"] = next(
                (film['user_review'] for film in films_dict.get(user, []) if film['title'].strip() == title), None)
        
        mutual_films.append(mutual_film)
    
    return mutual_films

def save_films_to_csv(films, filename, num_users, users):
    """Saves films to CSV and provides download functionality."""
    if films:
        # Define fieldnames dynamically based on the number of users
        if num_users == 1:
            fieldnames = ["title", f"{users[0]}_review", "rating"]
        else:
            fieldnames = ["title"] + [f"{user}_review" for user in users] + ["rating"]

        for film in films:
            # Rename or move 'user_review' to the correct user review key
            if 'user_review' in film:
                for i, user in enumerate(users):
                    user_key = f"{user}_review"
                    film[user_key] = film.pop('user_review', None)

            for user in users:
                user_key = f"{user}_review"
                if user_key in film and (film[user_key] is None or film[user_key] == ""):
                    del film[user_key] 

            if 'rating' not in film:
                film['rating'] = 5

            # Remove any keys that are not in fieldnames to avoid the error
            keys_to_remove = [key for key in film.keys() if key not in fieldnames]
            for key in keys_to_remove:
                film.pop(key)

        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(films)

        output.seek(0)
        df = pd.read_csv(output)
        st.dataframe(df, use_container_width=True, height=600)  # Display the CSV content inline

        st.download_button("Download CSV", data=output.getvalue(), file_name=filename, mime="text/csv")
    else:
        st.write("No films found.")

def main():
    st.title("Letterboxd Top Ratings")
    user1_input = st.text_input("Enter the first Letterboxd username:", "")
    user2_input = st.text_input("Enter the second Letterboxd username (optional):", "")
    
    if st.button("Search"):
        if user1_input:
            users = [user1_input.strip()]
            
            if user2_input:
                users.append(user2_input.strip())
            
            user_films = {user: get_user_films(user) for user in users}
            
            if len(users) == 2:
                mutual_films = find_mutual_films(user_films, users)
                filename = f"mutual_5_star_films_{'_'.join(users)}_{datetime.utcnow().strftime('%Y-%m-%d-%H-%M')}.csv"
                save_films_to_csv(mutual_films, filename, len(users), users)
            else:
                filename = f"{users[0]}_5_star_films_{datetime.utcnow().strftime('%Y-%m-%d-%H-%M')}.csv"
                save_films_to_csv(user_films[users[0]], filename, len(users), users)

if __name__ == "__main__":
    main()
