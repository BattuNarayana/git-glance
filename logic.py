
import os
import requests
import redis
import json
import time 
from collections import Counter
from datetime import datetime, timedelta

# --- Redis Connection (Unchanged) ---
try:
    # --- Ensure connection uses localhost if that's what worked ---
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True) 
    redis_client.ping()
    print("Successfully connected to Redis.") 
except redis.exceptions.ConnectionError as e:
    print(f"CRITICAL ERROR: Could not connect to Redis at localhost:6379. {e}")
    print("Please ensure the Redis Docker container is running ('docker start redis-stack').")
    redis_client = None 
CACHE_DURATION = 600 

# --- FINAL, ROBUST AI Summarizer (Unchanged) ---
def get_ai_summary(owner, repo):
    print(f"--- Entering get_ai_summary for {owner}/{repo} ---") 
    if not redis_client:
        return "Error: Redis connection not available."

    cache_key = f"summary:{owner}/{repo}"
    if cached_summary := redis_client.get(cache_key):
        print(f"CACHE HIT for summary: {owner}/{repo}")
        return cached_summary

    print(f"CACHE MISS for summary: {owner}/{repo}. Processing...")
    
    # Step 1: Fetch README content using download_url
    readme_content = None
    readme_url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    token = os.getenv("GITHUB_TOKEN")
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"} if token else {"Accept": "application/vnd.github.v3+json"}
    try:
        readme_response = requests.get(readme_url, headers=headers, timeout=10) 
        readme_response.raise_for_status() 
        readme_data = readme_response.json()
        download_url = readme_data.get('download_url')
        if download_url:
            content_response = requests.get(download_url, timeout=10) 
            content_response.raise_for_status()
            readme_content = content_response.content.decode('utf-8', errors='replace') 
        else:
            print(f"Could not find download_url in README response for {owner}/{repo}")
            return "Error: Could not retrieve README download URL from GitHub."
            
    except requests.exceptions.Timeout:
         print(f"Timeout fetching README for {owner}/{repo}")
         return "Error: Timeout fetching README from GitHub."
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"README not found for {owner}/{repo}")
            return "Error: This repository does not have a readable README file."
        else:
            print(f"HTTP error fetching README for {owner}/{repo}: {e}")
            return f"Error: Could not fetch README (HTTP {e.response.status_code})."
    except requests.exceptions.RequestException as e:
        print(f"Network error fetching README for {owner}/{repo}: {e}")
        return f"Error: Could not fetch README from GitHub due to network issue."
    except Exception as e: 
        print(f"Unexpected error fetching README content for {owner}/{repo}: {e}")
        return "Error: Failed to process README content."

    if not readme_content:
         return "Error: Failed to retrieve valid README content."

    # Step 2: Call the Gemini API with retry logic
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Error: GEMINI_API_KEY is not configured on the server."

    gemini_api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={api_key}"
    max_readme_length = 15000 
    truncated_content = readme_content[:max_readme_length] + ("..." if len(readme_content) > max_readme_length else "")
    prompt = f"Summarize this README file in 3-4 concise bullet points for a technical recruiter. Focus on the project's purpose, its main features, and the technology stack used. README content:\n\n{truncated_content}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    max_retries = 3
    base_delay = 1

    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt + 1} to call Gemini API for {owner}/{repo}")
            response = requests.post(gemini_api_url, json=payload, timeout=25) 
            
            if 500 <= response.status_code < 600:
                print(f"Attempt {attempt + 1}: Received server error {response.status_code}. Retrying...")
                time.sleep(base_delay * (2 ** attempt))
                continue

            if response.status_code == 400:
                 print(f"Attempt {attempt + 1}: Received 400 Bad Request from Gemini. Content might be invalid/too long? Error: {response.text}")
                 return "Error: AI service rejected the request (Bad Request). Content might be invalid or too long."

            response.raise_for_status() 
            result = response.json()
            
            candidates = result.get('candidates')
            if candidates and isinstance(candidates, list) and len(candidates) > 0:
                content = candidates[0].get('content')
                if content and 'parts' in content and isinstance(content['parts'], list) and len(content['parts']) > 0:
                    summary = content['parts'][0].get('text')
                    if summary:
                        print(f"Successfully generated summary for {owner}/{repo}")
                        redis_client.setex(cache_key, 86400, summary) 
                        return summary 

            finish_reason = candidates[0].get('finishReason', 'UNKNOWN') if candidates else 'NO_CANDIDATES'
            safety_ratings = candidates[0].get('safetyRatings', []) if candidates else []
            print(f"Unexpected Gemini API response structure for {owner}/{repo}. Finish Reason: {finish_reason}, Safety: {safety_ratings}. Response: {result}")
            return f"AI model returned a non-standard response (Finish Reason: {finish_reason})."

        except requests.exceptions.Timeout:
            print(f"Attempt {attempt + 1}: Gemini API call timed out for {owner}/{repo}. Retrying...")
            if attempt >= max_retries - 1:
                 return f"Error: AI service timed out after {max_retries} attempts."
            time.sleep(base_delay * (2 ** attempt))
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            print(f"Attempt {attempt + 1}: Network or JSON error calling Gemini ({e}). Retrying...")
            if attempt >= max_retries - 1:
                return f"Error: Failed to communicate with the AI service after {max_retries} attempts."
            time.sleep(base_delay * (2 ** attempt))

    return f"Error: AI service is unavailable after {max_retries} attempts."


# --- FINAL, DEBUGGED Pinned Repos ---
def fetch_pinned_repos(username):
    """Fetches pinned repos using GraphQL, handles User/Org, includes detailed logging."""
    print(f"--- DEBUG: Inside fetch_pinned_repos for {username} ---")
    if not redis_client: 
        print("--- DEBUG: Exiting fetch_pinned_repos early (no Redis) ---")
        return []
        
    cache_key = f"pinned:{username}"
    
    # --- TEMPORARY DEBUGGING: Clear cache to force API call ---
    # print(f"--- DEBUG: Clearing cache key {cache_key} for testing ---")
    # try:
    #     redis_client.delete(cache_key)
    # except Exception as e:
    #     print(f"--- DEBUG: Error clearing cache key {cache_key}: {e} ---")
    # --- END TEMPORARY DEBUGGING ---

    if cached_data := redis_client.get(cache_key): 
        print(f"--- DEBUG: Cache HIT for pinned repos: {username} ---")
        try:
             parsed_data = json.loads(cached_data)
             # print(f"--- DEBUG: Parsed cached data: {parsed_data}") # Optional: uncomment for extreme debugging
             return parsed_data
        except json.JSONDecodeError as e:
             print(f"--- DEBUG: ERROR parsing cached data for {cache_key}: {e} ---")
             print(f"--- DEBUG: Corrupted cached data was: {cached_data}")
             redis_client.delete(cache_key) # Delete corrupted cache

    print(f"--- DEBUG: Cache MISS for pinned repos: {username}. Calling GraphQL... ---")
    token = os.getenv("GITHUB_TOKEN")
    
    if not token:
        print("--- DEBUG: GITHUB_TOKEN is MISSING for GraphQL! ---")
        return []
    print(f"--- DEBUG: Using GitHub Token for Pinned Repos: {token[:10]}... ---")

    headers = {"Authorization": f"bearer {token}"}
    # --- CORRECTED GraphQL QUERY ---
    graphql_query = { "query": """
        query($username: String!) {
          repositoryOwner(login: $username) {
            ... on User {
              pinnedItems(first: 6, types: REPOSITORY) { 
                nodes { 
                  ... on Repository { 
                    name 
                    description 
                    stargazerCount 
                    forkCount 
                    url 
                    owner { login } 
                    repositoryTopics(first: 5) { nodes { topic { name } } } # Correct field for topics
                    primaryLanguage { name } 
                  } 
                } 
              }
            }
            ... on Organization {
              pinnedItems(first: 6, types: REPOSITORY) { 
                nodes { 
                  ... on Repository { 
                    name 
                    description 
                    stargazerCount 
                    forkCount 
                    url 
                    owner { login } 
                    repositoryTopics(first: 5) { nodes { topic { name } } } # Correct field for topics
                    primaryLanguage { name } 
                  } 
                } 
              }
            }
          }
        }
        """, "variables": {"username": username} }
        
    api_url = "https://api.github.com/graphql"
    try:
        response = requests.post(api_url, headers=headers, json=graphql_query, timeout=15) 
        response.raise_for_status() 
        raw_data = response.json()
        
        # --- Check for GraphQL Errors within the response body ---
        if "errors" in raw_data:
             print(f"--- DEBUG: GraphQL API returned errors for {username}: ---")
             print(json.dumps(raw_data["errors"], indent=2))
             print("---------------------------------------------------------")
             # Decide if you want to return [] or handle partially
             # For simplicity, we'll return empty on any GraphQL error now
             return [] 

        print(f"--- DEBUG: Raw GraphQL Response (No Errors) for {username}: ---")
        print(json.dumps(raw_data, indent=2))
        print("-----------------------------------------------")

        owner_data = raw_data.get("data", {}).get("repositoryOwner", {})
        if not owner_data:
             print(f"--- DEBUG: No repositoryOwner data found in GraphQL response for {username}. Returning empty list. ---")
             return [] 

        pinned_items = owner_data.get("pinnedItems", {}).get("nodes", None) 
        if pinned_items is None: 
             print(f"--- DEBUG: pinnedItems.nodes was null in GraphQL response for {username}. Returning empty list. ---")
             return []
        
        if not isinstance(pinned_items, list):
             print(f"--- DEBUG: pinnedItems.nodes was not a list ({type(pinned_items)}). Returning empty list. ---")
             return []

        print(f"--- DEBUG: Found {len(pinned_items)} pinned items for {username}. Processing... ---")
        formatted_repos = []
        for repo in pinned_items:
            if not repo or not isinstance(repo, dict): 
                print(f"--- DEBUG: Skipping invalid repo item: {repo} ---")
                continue
            owner_info = repo.get("owner", {})
            owner_login = owner_info.get("login") if isinstance(owner_info, dict) else None
                
            formatted_repos.append({
                "name": repo.get("name"),
                "description": repo.get("description"),
                "stargazers_count": repo.get("stargazerCount"),
                "forks_count": repo.get("forkCount"),
                "html_url": repo.get("url"),
                "owner": {"login": owner_login }, 
                "language": (repo.get("primaryLanguage") or {}).get("name"),
                 # --- CORRECTED Topic Extraction ---
                "topics": [
                    node['topic']['name'] 
                    for node in repo.get("repositoryTopics", {}).get("nodes", []) # Use repositoryTopics
                    if node and isinstance(node, dict) and 'topic' in node and isinstance(node['topic'], dict) and 'name' in node['topic']
                ] 
            })
        
        print(f"--- DEBUG: Successfully formatted {len(formatted_repos)} pinned repos for {username}. Caching... ---")
        redis_client.setex(cache_key, 3600, json.dumps(formatted_repos)) 
        return formatted_repos
        
    except requests.exceptions.Timeout:
        print(f"--- DEBUG: Timeout calling GraphQL API for {username}. Returning empty list. ---")
        return [] 
    except requests.exceptions.RequestException as e:
        print(f"--- DEBUG: Error calling GraphQL API for {username}: {e} ---")
        if e.response: 
            print(f"--- DEBUG: Response Status Code: {e.response.status_code} ---")
            print(f"--- DEBUG: Response Text: {e.response.text} ---")
        return [] 
    except json.JSONDecodeError as e:
        print(f"--- DEBUG: Error decoding JSON response from GraphQL for {username}: {e} ---")
        return []
    except Exception as e: 
         print(f"--- DEBUG: Unexpected error processing GraphQL response for {username}: {e} ---")
         return []


# --- fetch_github_data (Unchanged from final) ---
def fetch_github_data(username):
    # ... (code is correct) ...
    if not redis_client: return None
    cache_key = f"user:{username}"
    if cached_data := redis_client.get(cache_key):
        return json.loads(cached_data)
    token = os.getenv("GITHUB_TOKEN")
    headers = {"Authorization": f"token {token}"} if token else {}
    api_url = f"https://api.github.com/users/{username}"
    try:
        response = requests.get(api_url, headers=headers, timeout=10) 
        response.raise_for_status() 
        user_data = response.json()
        redis_client.setex(cache_key, CACHE_DURATION, json.dumps(user_data))
        return user_data
    except requests.exceptions.Timeout:
         print(f"Timeout fetching user data for {username}")
         return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching user data for {username}: {e}")
        return None

# --- fetch_user_repos (Unchanged from final) ---
def fetch_user_repos(username, page=1):
    # ... (code is correct) ...
    if not redis_client: return []
    cache_key = f"repos:{username}"
    if page == 1:
        if cached_data := redis_client.get(cache_key):
            return json.loads(cached_data)
    token = os.getenv("GITHUB_TOKEN")
    headers = {"Authorization": f"token {token}"} if token else {}
    api_url = f"https://api.github.com/users/{username}/repos?sort=pushed&per_page=30&page={page}"
    try:
        response = requests.get(api_url, headers=headers, timeout=10) 
        response.raise_for_status() 
        repos_data = response.json()
        if page == 1:
            redis_client.setex(cache_key, CACHE_DURATION, json.dumps(repos_data))
        return repos_data
    except requests.exceptions.Timeout:
        print(f"Timeout fetching repos page {page} for {username}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"Error fetching repos page {page} for {username}: {e}")
        return []

# --- analyze_repo_languages (Unchanged from final) ---
def analyze_repo_languages(repos):
    # ... (code is correct) ...
    if not repos: return Counter() 
    languages = [repo['language'] for repo in repos if repo and isinstance(repo, dict) and repo.get('language') is not None]
    return Counter(languages)

# --- calculate_activity_streak (Unchanged from final) ---
def calculate_activity_streak(username):
    # ... (code is correct) ...
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
            response = requests.get(f"{api_url}&page={page}", headers=headers, timeout=10) 
            response.raise_for_status() 
            events = response.json()
            if not events: break
            for event in events:
                if event.get('type') in ['PushEvent', 'CreateEvent', 'PullRequestEvent', 'IssuesEvent']:
                    created_at = event.get('created_at')
                    if created_at:
                        try:
                           event_date = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ").date()
                           active_dates.add(event_date)
                        except (ValueError, TypeError):
                             print(f"Warning: Could not parse date {created_at} in event for {username}")
        except requests.exceptions.Timeout:
            print(f"Timeout fetching events page {page} for {username}")
            break 
        except requests.exceptions.RequestException as e:
            print(f"Error fetching events page {page} for {username}: {e}")
            break 
        
    if not active_dates: 
        redis_client.setex(cache_key, 3600, 0) 
        return 0
        
    sorted_dates = sorted(list(active_dates), reverse=True)
    longest_streak = 0
    current_streak = 0
    
    if sorted_dates: 
        longest_streak = 1
        current_streak = 1
        for i in range(len(sorted_dates) - 1):
            if sorted_dates[i] - sorted_dates[i+1] == timedelta(days=1):
                current_streak += 1
            else:
                if sorted_dates[i] - sorted_dates[i+1] > timedelta(days=1): 
                   longest_streak = max(longest_streak, current_streak)
                   current_streak = 1 
        longest_streak = max(longest_streak, current_streak) 

    redis_client.setex(cache_key, 3600, longest_streak) 
    return longest_streak

