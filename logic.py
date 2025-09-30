# import os
# import requests
# import redis
# import json
# from collections import Counter
# from datetime import datetime, timedelta

# # --- Redis Connection (Unchanged) ---
# try:
#     redis_client = redis.Redis(host='host.docker.internal', port=6379, db=0, decode_responses=True)
#     redis_client.ping()
# except redis.exceptions.ConnectionError:
#     print("Error: Could not connect to Redis.")
#     redis_client = None

# CACHE_DURATION = 600

# # --- THIS IS THE CORRECTED FUNCTION ---
# def fetch_pinned_repos(username):
#     """Fetches pinned repos for either a User or an Organization using GraphQL."""
#     if not redis_client: return []
    
#     cache_key = f"pinned:{username}"
#     if cached_data := redis_client.get(cache_key):
#         return json.loads(cached_data)

#     token = os.getenv("GITHUB_TOKEN")
#     if not token:
#         return [] 

#     headers = {"Authorization": f"bearer {token}"}
    
#     # This advanced query can handle both Users and Organizations
#     graphql_query = {
#         "query": """
#         query($username: String!) {
#           repositoryOwner(login: $username) {
#             ... on User {
#               pinnedItems(first: 6, types: REPOSITORY) {
#                 nodes { ... on Repository { ...repoFields } }
#               }
#             }
#             ... on Organization {
#               pinnedItems(first: 6, types: REPOSITORY) {
#                 nodes { ... on Repository { ...repoFields } }
#               }
#             }
#           }
#         }
#         fragment repoFields on Repository {
#           name
#           description
#           stargazerCount
#           forkCount
#           url
#           owner { login }
#           primaryLanguage { name }
#         }
#         """,
#         "variables": {"username": username}
#     }
    
#     api_url = "https://api.github.com/graphql"
#     try:
#         response = requests.post(api_url, headers=headers, json=graphql_query)
#         if response.status_code == 200:
#             raw_data = response.json()
#             owner_data = raw_data.get("data", {}).get("repositoryOwner", {})
#             if not owner_data: return [] # Handle case where user/org doesn't exist
            
#             pinned_items = owner_data.get("pinnedItems", {}).get("nodes", [])
            
#             formatted_repos = []
#             for repo in pinned_items:
#                 formatted_repos.append({
#                     "name": repo.get("name"),
#                     "description": repo.get("description"),
#                     "stargazers_count": repo.get("stargazerCount"),
#                     "forks_count": repo.get("forkCount"),
#                     "html_url": repo.get("url"),
#                     "owner": repo.get("owner"),
#                     "language": (repo.get("primaryLanguage") or {}).get("name")
#                 })

#             redis_client.setex(cache_key, 3600, json.dumps(formatted_repos))
#             return formatted_repos
#         return []
#     except requests.exceptions.RequestException:
#         return []

# # --- All other functions are unchanged ---
# def fetch_github_data(username):
#     if not redis_client: return None
#     cache_key = f"user:{username}"
#     if cached_data := redis_client.get(cache_key):
#         return json.loads(cached_data)
#     token = os.getenv("GITHUB_TOKEN")
#     headers = {"Authorization": f"token {token}"} if token else {}
#     api_url = f"https://api.github.com/users/{username}"
#     try:
#         response = requests.get(api_url, headers=headers)
#         if response.status_code == 200:
#             user_data = response.json()
#             redis_client.setex(cache_key, CACHE_DURATION, json.dumps(user_data))
#             return user_data
#         return None
#     except requests.exceptions.RequestException:
#         return None

# def fetch_user_repos(username, page=1):
#     if not redis_client: return []
#     cache_key = f"repos:{username}:{page}" # Page-specific cache key
#     if cached_data := redis_client.get(cache_key):
#         return json.loads(cached_data)

#     token = os.getenv("GITHUB_TOKEN")
#     headers = {"Authorization": f"token {token}"} if token else {}
#     api_url = f"https://api.github.com/users/{username}/repos?sort=pushed&per_page=30&page={page}"
#     try:
#         response = requests.get(api_url, headers=headers)
#         if response.status_code == 200:
#             repos_data = response.json()
#             redis_client.setex(cache_key, CACHE_DURATION, json.dumps(repos_data))
#             return repos_data
#         return []
#     except requests.exceptions.RequestException:
#         return []

# def analyze_repo_languages(repos):
#     languages = [repo['language'] for repo in repos if repo and repo.get('language') is not None]
#     return Counter(languages)

# def calculate_activity_streak(username):
#     if not redis_client: return 0
#     cache_key = f"streak:{username}"
#     if cached_streak := redis_client.get(cache_key):
#         return int(cached_streak)
#     token = os.getenv("GITHUB_TOKEN")
#     headers = {"Authorization": f"token {token}"} if token else {}
#     api_url = f"https://api.github.com/users/{username}/events?per_page=100"
#     active_dates = set()
#     for page in range(1, 4):
#         try:
#             response = requests.get(f"{api_url}&page={page}", headers=headers)
#             if response.status_code == 200:
#                 events = response.json()
#                 if not events: break
#                 for event in events:
#                     if event['type'] in ['PushEvent', 'CreateEvent', 'PullRequestEvent', 'IssuesEvent']:
#                         event_date = datetime.strptime(event['created_at'], "%Y-%m-%dT%H:%M:%SZ").date()
#                         active_dates.add(event_date)
#             else: break
#         except requests.exceptions.RequestException: break
#     if not active_dates: return 0
#     sorted_dates = sorted(list(active_dates), reverse=True)
#     longest_streak = 0
#     current_streak = 1
#     if len(sorted_dates) == 1:
#         longest_streak = 1
#     else:
#         for i in range(len(sorted_dates) - 1):
#             if sorted_dates[i] - sorted_dates[i+1] == timedelta(days=1):
#                 current_streak += 1
#             else:
#                 longest_streak = max(longest_streak, current_streak)
#                 current_streak = 1
#         longest_streak = max(longest_streak, current_streak)
#     redis_client.setex(cache_key, 3600, longest_streak)
#     return longest_streak





import os
import requests
import redis
import json
from collections import Counter
from datetime import datetime, timedelta

# --- Redis Connection (Unchanged) ---
try:
    redis_client = redis.Redis(host='host.docker.internal', port=6379, db=0, decode_responses=True)
    redis_client.ping()
except redis.exceptions.ConnectionError:
    print("Error: Could not connect to Redis.")
    redis_client = None

CACHE_DURATION = 600

# --- UPDATED: GraphQL Function now fetches topics ---
def fetch_pinned_repos(username):
    """Fetches pinned repos for either a User or an Organization using GraphQL."""
    if not redis_client: return []
    
    cache_key = f"pinned:{username}"
    if cached_data := redis_client.get(cache_key):
        return json.loads(cached_data)

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return [] 

    headers = {"Authorization": f"bearer {token}"}
    
    graphql_query = {
        "query": """
        query($username: String!) {
          repositoryOwner(login: $username) {
            ... on User {
              pinnedItems(first: 6, types: REPOSITORY) {
                nodes { ... on Repository { ...repoFields } }
              }
            }
            ... on Organization {
              pinnedItems(first: 6, types: REPOSITORY) {
                nodes { ... on Repository { ...repoFields } }
              }
            }
          }
        }
        fragment repoFields on Repository {
          name
          description
          stargazerCount
          forkCount
          url
          owner { login }
          primaryLanguage { name }
          repositoryTopics(first: 5) {
            nodes {
              topic {
                name
              }
            }
          }
        }
        """,
        "variables": {"username": username}
    }
    
    api_url = "https://api.github.com/graphql"
    try:
        response = requests.post(api_url, headers=headers, json=graphql_query)
        if response.status_code == 200:
            raw_data = response.json()
            owner_data = raw_data.get("data", {}).get("repositoryOwner", {})
            if not owner_data: return []
            
            pinned_items = owner_data.get("pinnedItems", {}).get("nodes", [])
            
            formatted_repos = []
            for repo in pinned_items:
                # Extract topics from the nested structure
                topics = [node['topic']['name'] for node in repo.get('repositoryTopics', {}).get('nodes', [])]
                
                formatted_repos.append({
                    "name": repo.get("name"),
                    "description": repo.get("description"),
                    "stargazers_count": repo.get("stargazerCount"),
                    "forks_count": repo.get("forkCount"),
                    "html_url": repo.get("url"),
                    "owner": repo.get("owner"),
                    "language": (repo.get("primaryLanguage") or {}).get("name"),
                    "topics": topics # Add the list of topics
                })

            redis_client.setex(cache_key, 3600, json.dumps(formatted_repos))
            return formatted_repos
        return []
    except requests.exceptions.RequestException:
        return []

# --- All other functions are unchanged ---
def fetch_github_data(username):
    if not redis_client: return None
    cache_key = f"user:{username}"
    if cached_data := redis_client.get(cache_key):
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
        return None
    except requests.exceptions.RequestException:
        return None

def fetch_user_repos(username, page=1):
    if not redis_client: return []
    cache_key = f"repos:{username}:{page}"
    if cached_data := redis_client.get(cache_key):
        return json.loads(cached_data)

    token = os.getenv("GITHUB_TOKEN")
    headers = {"Authorization": f"token {token}"} if token else {}
    api_url = f"https://api.github.com/users/{username}/repos?sort=pushed&per_page=30&page={page}"
    try:
        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            repos_data = response.json()
            redis_client.setex(cache_key, CACHE_DURATION, json.dumps(repos_data))
            return repos_data
        return []
    except requests.exceptions.RequestException:
        return []

def analyze_repo_languages(repos):
    languages = [repo['language'] for repo in repos if repo and repo.get('language') is not None]
    return Counter(languages)

def calculate_activity_streak(username):
    if not redis_client: return 0
    cache_key = f"streak:{username}"
    if cached_streak := redis_client.get(cache_key):
        return int(cached_streak)
    token = os.getenv("GITHUB_TOKEN")
    headers = {"Authorization": f"token {token}"} if token else {}
    api_url = f"https://api.github.com/users/{username}/events?per_page=100"
    active_dates = set()
    for page in range(1, 4):
        try:
            response = requests.get(f"{api_url}&page={page}", headers=headers)
            if response.status_code == 200:
                events = response.json()
                if not events: break
                for event in events:
                    if event['type'] in ['PushEvent', 'CreateEvent', 'PullRequestEvent', 'IssuesEvent']:
                        event_date = datetime.strptime(event['created_at'], "%Y-%m-%dT%H:%M:%SZ").date()
                        active_dates.add(event_date)
            else: break
        except requests.exceptions.RequestException: break
    if not active_dates: return 0
    sorted_dates = sorted(list(active_dates), reverse=True)
    longest_streak = 0
    current_streak = 1
    if len(sorted_dates) == 1:
        longest_streak = 1
    else:
        for i in range(len(sorted_dates) - 1):
            if sorted_dates[i] - sorted_dates[i+1] == timedelta(days=1):
                current_streak += 1
            else:
                longest_streak = max(longest_streak, current_streak)
                current_streak = 1
        longest_streak = max(longest_streak, current_streak)
    redis_client.setex(cache_key, 3600, longest_streak)
    return longest_streak

