from flask import Flask, request, jsonify, render_template
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, quote
app = Flask(__name__)
def archive_search(query="lost media", page=1, per_page=10):
    url = "https://archive.org/advancedsearch.php"
    params = {
        'q': query,
        'fl[]': ['title', 'description', 'identifier'],
        'sort[]': 'downloads desc',
        'rows': per_page,
        'page': page,
        'output': 'json'
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    docs = response.json().get("response", {}).get("docs", [])
    results = []
    for doc in docs:
        results.append({
            "title": doc.get("title", ""),
            "url": f"https://archive.org/details/{doc.get('identifier', '')}",
            "snippet": doc.get("description", ""),
            "link": f"https://archive.org/details/{doc.get('identifier', '')}"
        })
    return results
def ahmia_search(query="lost media", page=1):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/114.0.0.0 Safari/537.36"
        )
    }
    url = f"https://onionland.io/scrape.php?page={page}&q={query.replace(' ', '+')}"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching OnionLand: {e}")
        return []
    soup = BeautifulSoup(response.text, "html.parser")
    results = []
    for a in soup.select("a.onionRecord[href]"):
        href = a["href"]
        title = a.get_text(strip=True)
        if not href or ".onion" not in href:
            continue
        results.append({
            "title": title,
            "url": href,
            "snippet": "",  
            "link": href
        })
    return results
def openverse_search(query="lost media", page=1, per_page=10):
    url = "https://api.openverse.engineering/v1/images"
    params = {
        "q": query,
        "page": page,
        "page_size": per_page,
        "license_type": "all",
        "extension": "jpg"  
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        results_json = response.json().get("results", [])
    except requests.RequestException as e:
        print(f"Error fetching Openverse: {e}")
        return []
    results = []
    for item in results_json:
        results.append({
            "title": item.get("title", "Untitled"),
            "url": item.get("url", ""),
            "snippet": item.get("creator", "Unknown creator"),
            "link": item.get("url", "")
        })
    return results
@app.route('/')
def index():
    return render_template('index.html')
@app.route('/api/media')
def media_api():
    source = request.args.get('source', 'archive').lower()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    query = request.args.get('q', 'lost media')
    if source == 'archive':
        results = archive_search(query=query, page=page, per_page=per_page)
    elif source == 'ahmia':
        results = ahmia_search(query=query, page=page)
    elif source == 'openverse':
        results = openverse_search(query=query, page=page, per_page=per_page)
    else:
        return jsonify({"error": "Unsupported source"}), 400
    return jsonify({
        "source": source,
        "page": page,
        "per_page": per_page,
        "results": results
    })
if __name__ == '__main__':
    app.run(debug=True)
