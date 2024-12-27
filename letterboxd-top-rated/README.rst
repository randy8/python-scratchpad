Letterboxd Top Rated
====================

This Streamlit-based application allows users to fetch, compare, and download 5-star rated films from Letterboxd. The app accepts Letterboxd usernames, retrieves films rated 5 stars by those users, and creates a CSV file containing mutual films that both users have rated 5 stars.

Installation
------------
To install the necessary dependencies, run the following command:

.. code-block:: bash

    pip3 install streamlit requests beautifulsoup4 tqdm

Usage
-----
1. Run the Streamlit app:

.. code-block:: bash

    streamlit run streamlit-letterboxd-top-rated.py
