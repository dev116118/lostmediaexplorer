from flask import Flask, request, jsonify, render_template
import requests
from bs4 import BeautifulSoup
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
from urllib.parse import urlparse, parse_qs
def ahmia_search(query="lost media"):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/114.0.0.0 Safari/537.36"
        )
    }
    url = f"https://ahmia.fi/search/?q={query}"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching Ahmia: {e}")
        return []
    soup = BeautifulSoup(response.text, "html.parser")
    results = []
    for li in soup.select("li.result"):
        h4 = li.find("h4")
        if not h4:
            continue
        a = h4.find("a", href=True)
        if not a:
            continue
        href = a['href']
        onion_link = None
        if "ahmia.fi/redirect" in href or href.startswith('/search/redirect'):
            full_redirect_url = href
            if href.startswith('/'):
                full_redirect_url = "https://ahmia.fi" + href
            parsed = urlparse(full_redirect_url)
            query_params = parse_qs(parsed.query)
            if "redirect_url" in query_params:
                onion_link = query_params["redirect_url"][0]
        elif ".onion" in href:
            onion_link = href
        if not onion_link or ".onion" not in onion_link:
            continue
        title = a.get_text(strip=True)
        p = li.find("p")
        description = p.get_text(strip=True) if p else ""
        results.append({
            "title": title,
            "url": onion_link,
            "snippet": description,
            "link": onion_link
        })
    return results
def wikimedia_commons_search(query="lost media", page=1, per_page=10):
    return []
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
    elif source == 'wikimedia':
        results = wikimedia_commons_search(query=query, page=page, per_page=per_page)
    elif source == 'ahmia':
        results = ahmia_search(query=query)
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
