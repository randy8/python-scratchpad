from flask import Flask, render_template_string, request
import urllib.parse
from itertools import combinations
import webbrowser

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Letterboxd Fan Finder</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f4f6f8;
            color: #333;
            margin: 0;
            padding: 0;
        }
        .container {
            max-width: 600px;
            margin: 20px auto;
            background-color: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        }
        h1 {
            color: #1877f2;
            margin-bottom: 20px;
            text-align: center
        }
        form {
            display: grid;
            gap: 15px;
        }
        input[type="text"] {
            padding: 12px;
            font-size: 1em;
            border: 1px solid #ccc;
            border-radius: 5px;
            width: 100%;
            background-color: #f9f9f9;
            box-sizing: border-box;
        }
        button {
            padding: 12px;
            background-color: #4caf50;
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 1.1em;
            cursor: pointer;
            width: 100%;
        }
        button:hover {
            background-color: #388e3c;
        }
        .results {
            margin-top: 30px;
        }
        .results ul {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        .results li {
            margin: 10px 0;
        }
        .result-button {
            padding: 10px;
            background-color: #0366d6;
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 1em;
            cursor: pointer;
            width: 100%;
        }
        .result-button:hover {
            background-color: #024ea2;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Letterboxd Fan Finder</h1>
        <p>Enter up to 4 movie titles to find Letterboxd users who love these movies:</p>
        <form method="post">
            {% for i in range(1, 5) %}
                <input type="text" name="movie{{ i }}" placeholder="Movie {{ i }}" value="{{ movie_titles[i-1] if i-1 < movie_titles|length else '' }}">
            {% endfor %}
            <button type="submit">Find Fans</button>
        </form>
        {% if links %}
        <div class="results">
            <h2>Search Results</h2>
            <ul>
                {% for link, title in links %}
                    <li>
                        <button class="result-button" onclick="window.open('{{ link }}', '_blank')">
                            {{ title }}
                        </button>
                    </li>
                {% endfor %}
            </ul>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

def to_slug(title: str) -> str:
    return urllib.parse.quote(title.lower().replace(" ", "-"))

def format_title(title: str) -> str:
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

def generate_links(movie_titles: list) -> list:
    links = []
    for n in range(1, len(movie_titles) + 1):
        for pair in combinations(movie_titles, n):
            link = f"https://letterboxd.com/search/{'+'.join(f'fan:{to_slug(title)}' for title in pair)}/"
            title = ", ".join(map(format_title, pair))
            links.append((link, title))
    return links

def get_movie_titles(form_data) -> list:
    return [form_data.get(f"movie{i}", "").strip() for i in range(1, 5) if form_data.get(f"movie{i}", "").strip()]

@app.route("/", methods=["GET", "POST"])
def index():
    movie_titles = get_movie_titles(request.form)

    if not movie_titles:
        return render_template_string(HTML_TEMPLATE, links=[], movie_titles=movie_titles)
    
    links = generate_links(movie_titles)
    return render_template_string(HTML_TEMPLATE, links=links, movie_titles=movie_titles)

if __name__ == "__main__":
    webbrowser.open("http://127.0.0.1:5000/") 
    app.run()
