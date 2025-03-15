import requests
from bs4 import BeautifulSoup
import json
import stashapi
import os

def fetch_rule34(character):
    url = f"https://rule34.xxx/index.php?page=dapi&q=index&s=post&json=1&tags={character}&limit=100"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        sorted_data = sorted(data, key=lambda x: x.get('score', 0), reverse=True)
        return sorted_data[:20]
    return []

def fetch_gelbooru(character):
    url = f"https://gelbooru.com/index.php?page=dapi&q=index&s=post&json=1&tags={character}&limit=100"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json().get('post', [])
        sorted_data = sorted(data, key=lambda x: x.get('score', 0), reverse=True)
        return sorted_data[:20]
    return []

def fetch_e621(character):
    url = f"https://e621.net/posts.json?tags={character}&limit=100"
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json().get('posts', [])
        sorted_data = sorted(data, key=lambda x: x.get('score', {}).get('total', 0), reverse=True)
        return sorted_data[:20]
    return []

def parse_results(results, source):
    parsed = []
    for item in results:
        image_url = item.get('file_url') or item.get('sample_url')
        tags = item.get('tags', {})
        if isinstance(tags, str):
            tags = tags.split()
        parsed.append({
            'url': image_url,
            'source': source
        })
    return parsed

def scrape_character(character):
    rule34_results = fetch_rule34(character)
    gelbooru_results = fetch_gelbooru(character)
    e621_results = fetch_e621(character)
    
    images = parse_results(rule34_results, 'Rule34.xxx') + \
             parse_results(gelbooru_results, 'Gelbooru') + \
             parse_results(e621_results, 'e621')
    
    tags = list(set(tag for image in rule34_results + gelbooru_results + e621_results for tag in image.get('tags', [])))
    description = f"Auto-generated performer data for {character}."
    
    performer_data = {
        "name": character,
        "aliases": [],
        "description": description,
        "tags": tags,
        "images": images,
        "metadata": {
            "source": "Multiple",
            "additional_info": "Fetched from Rule34.xxx, Gelbooru, and e621"
        }
    }
    
    return performer_data

def get_performer_name_from_stash(stash):
    performers = stash.get_performers()
    if performers and len(performers) > 0:
        return performers[0]['name']
    return None

def upload_to_stash(performer_data, stash):
    stash.add_performer(performer_data)
    print(f"Uploaded {performer_data['name']} to Stash")

def run(stash, params):
    api_key = params.get("api_key", "") or os.getenv("STASH_API_KEY", "")
    if not api_key:
        raise ValueError("API key is missing. Please provide it in the plugin settings or as an environment variable.")
    
    character_name = params.get("performer_name", "")
    
    if not character_name:
        character_name = get_performer_name_from_stash(stash)
    
    if character_name:
        data = scrape_character(character_name)
        upload_to_stash(data, stash)
        return {"success": True, "message": f"Uploaded {character_name} to Stash"}
    
    return {"success": False, "message": "No performer found in Stash"}