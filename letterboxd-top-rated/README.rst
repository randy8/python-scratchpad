Letterboxd Top Rated
====================

This Streamlit-based application allows users to fetch, compare, and download 5-star rated films from Letterboxd. The app accepts Letterboxd usernames, retrieves films rated 5 stars by those users, and creates a CSV file containing mutual films that both users have rated 5 stars.

Installation
------------
To install the necessary dependencies, run the following command:

.. code-block:: bash

    pip3 install requests beautifulsoup4 tqdm

Usage
-----
1. Run the Streamlit app:

.. code-block:: bash

    streamlit run streamlit-letterboxd-top-rati

2. Open the web browser, input one or more Letterboxd usernames, and hit "⌘ + Enter."
3. The app will display a table of films and provide the option to download a CSV containing the 5-star films.
4. If multiple users are provided, mutual 5-star films will be compared and displayed.

