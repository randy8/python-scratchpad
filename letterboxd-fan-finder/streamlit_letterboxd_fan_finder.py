import streamlit as st
import urllib.parse
from itertools import combinations
import webbrowser

def to_slug(title):
    return urllib.parse.quote(title.lower().replace(" ", "-"))
    
def format_title(title):
    exceptions = {
        "a", "an", "the", "and", "but", "or", "nor", "for", 
        "so", "yet", "to", "as", "at", "by", "from", "in", 
        "of", "on", "with"
    }
    return " ".join(
        [
            word.capitalize() if i == 0 or word.lower() not in exceptions else word.lower()
            for i, word in enumerate(title.split())
        ]
    )

def generate_links(movie_titles):
    links = []
    for n in range(1, len(movie_titles) + 1):
        for pair in combinations(movie_titles, n):
            link = f"https://letterboxd.com/search/{'+'.join(f'fan:{to_slug(title)}' for title in pair)}/"
            title = ", ".join(map(format_title, pair))
            links.append((link, title))
    return links

def app():
    st.set_page_config(page_title="Letterboxd Fan Finder", layout="wide")
    st.title("Letterboxd Fan Finder") 

    with st.container():
        st.subheader("Enter up to 4 movie titles:")
        movie_titles = []
        for i in range(1, 5):
            movie_title = st.text_input(f"Movie {i}", key=f"movie{i}", placeholder=f"Enter Movie {i}")
            if movie_title.strip():
                movie_titles.append(movie_title.strip())

        submit_button = st.button("🔍 Find Fans", key="submit")

    if submit_button:
        if len(movie_titles) == 0:
            st.warning("Please enter at least one movie title to search.")
        else:
            with st.spinner("Searching for fans..."):
                links = generate_links(movie_titles)
                # Store results in session state to persist them
                st.session_state.links = links

    if 'links' in st.session_state:
        if st.session_state.links:
            st.subheader("Search Results:")
            # Use columns for a grid display of results
            cols = st.columns(3) 
            for idx, (link, title) in enumerate(st.session_state.links):
                col = cols[idx % 3] 
                with col:
                    st.button(title, key=link, on_click=lambda url=link: webbrowser.open(url))

if __name__ == "__main__":
    app()
