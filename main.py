# main.py

import requests
import argparse
from datetime import datetime
from collections import Counter
import os
from dotenv import load_dotenv
import redis
import json
import time  # NEW: Import the time module

load_dotenv()

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

try:
    redis_client = redis.Redis(host='host.docker.internal', port=6379, db=0, decode_responses=True)
    redis_client.ping()
except redis.exceptions.ConnectionError:
    console.print("[bold red]Error: Could not connect to Redis.[/bold red]")
    console.print("[dim]Please ensure the Redis Docker container is running.[/dim]")
    exit()

CACHE_DURATION = 600

# --- All functions below are unchanged ---
def fetch_github_data(username):
    cache_key = f"user:{username}"
    cached_data = redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)
    
    token = os.getenv("GITHUB_TOKEN")
    headers = {"Authorization": f"token {token}"} if token else {}
    api_url = f"https://api.github.com/users/{username}"
    
    try:
        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            user_data = response.json()
            redis_client.setex(cache_key, CACHE_DURATION, json.dumps(user_data))
            return user_data
        elif response.status_code == 404:
            return None
        else:
            return None
    except requests.exceptions.RequestException:
        return None

def fetch_user_repos(username):
    cache_key = f"repos:{username}"
    cached_data = redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)

    token = os.getenv("GITHUB_TOKEN")
    headers = {"Authorization": f"token {token}"} if token else {}
    api_url = f"https://api.github.com/users/{username}/repos?sort=pushed&per_page=30"
    
    try:
        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            repos_data = response.json()
            redis_client.setex(cache_key, CACHE_DURATION, json.dumps(repos_data))
            return repos_data
        else:
            return []
    except requests.exceptions.RequestException:
        return []

def analyze_repo_languages(repos):
    languages = [repo['language'] for repo in repos if repo['language'] is not None]
    return Counter(languages)

def display_user_data(user_data, repos, language_stats):
    if not user_data: return
    name = user_data.get('name') or 'N/A'
    login = user_data.get('login', 'N/A')
    bio = user_data.get('bio') or 'N/A'
    location = user_data.get('location') or 'N/A'
    company = user_data.get('company') or 'N/A'
    profile_text = (f"[b]{name}[/b] ([cyan]@{login}[/cyan])\n{bio}\n\n[dim]{company} • {location}[/dim]")
    console.print(Panel(profile_text, title="GitHub Profile", border_style="green"))
    stats_table = Table(show_header=False, padding=(0, 2))
    stats_table.add_column(style="bold magenta"); stats_table.add_column(style="bold cyan")
    stats_table.add_row("Followers", str(user_data.get('followers', 0))); stats_table.add_row("Following", str(user_data.get('following', 0))); stats_table.add_row("Public Repos", str(user_data.get('public_repos', 0)))
    lang_table = Table(title="Top Languages", border_style="blue")
    lang_table.add_column("Language", style="bold yellow"); lang_table.add_column("Repos", style="bold green", justify="right")
    if language_stats:
        for lang, count in language_stats.most_common(5): lang_table.add_row(lang, str(count))
    repo_table = Table(title="Latest Repositories", border_style="blue")
    repo_table.add_column("Repository Name", style="bold white")
    if repos:
        for repo in repos[:5]: repo_table.add_row(repo.get('name', 'N/A'))
    layout_table = Table(box=None, show_header=False, expand=True)
    layout_table.add_column(); layout_table.add_column()
    layout_table.add_row(stats_table, lang_table)
    console.print(layout_table)
    console.print(repo_table)

# --- UPDATED MAIN BLOCK with Timer ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch and display GitHub user data.")
    parser.add_argument("username", help="The GitHub username to look up.")
    args = parser.parse_args()
    
    # --- START TIMER ---
    start_time = time.time()
    
    user_data = fetch_github_data(args.username)
    
    if user_data:
        repos = fetch_user_repos(args.username)
        language_stats = analyze_repo_languages(repos)
        display_user_data(user_data, repos, language_stats)
    
    # --- END TIMER and print result ---
    end_time = time.time()
    duration = end_time - start_time
    console.print(f"\n[bold yellow]Execution Time: {duration:.2f} seconds[/bold yellow]")