# app.py

# import requests
# import os # Make sure os is imported
# from flask import Flask, jsonify, abort, render_template, request
# from dotenv import load_dotenv

# # All our logic functions are imported from our refactored logic.py
# from logic import fetch_github_data, fetch_user_repos, analyze_repo_languages, calculate_activity_streak

# # Load environment variables from the .env file (GITHUB_TOKEN and GEMINI_API_KEY)
# load_dotenv()

# # Initialize the Flask application
# app = Flask(__name__)


# @app.route('/')
# def index():
#     """Serves the main HTML page from the 'templates' folder."""
#     return render_template('index.html')


# @app.route('/api/user/<string:username>')
# def get_user_profile(username):
#     """
#     Handles requests for user data.
#     If page=1, returns the full profile.
#     If page > 1, returns only the next set of repositories for pagination.
#     """
#     page = request.args.get('page', 1, type=int)

#     if page == 1:
#         # For the initial load, fetch and return the full dashboard data
#         user_data = fetch_github_data(username)
#         if not user_data:
#             abort(404, description=f"User '{username}' not found.")
        
#         repos = fetch_user_repos(username, page=page)
#         language_stats = analyze_repo_languages(repos)
        
#         response_data = {
#             "profile": user_data,
#             "repos": repos,
#             "language_stats": language_stats.most_common(5)
#         }
#     else:
#         # For 'Load More' requests, only fetch and return the next page of repos
#         repos = fetch_user_repos(username, page=page)
#         response_data = {"repos": repos}

#     return jsonify(response_data)


# @app.route('/api/user/<string:username>/activity')
# def get_user_activity(username):
#     """Calculates and returns the user's longest contribution streak."""
#     streak = calculate_activity_streak(username)
#     return jsonify({"longest_streak": streak})


# @app.route('/api/summarize', methods=['POST'])
# def summarize_readme():
#     """Receives README content and returns a summary using the Gemini API."""
    
#     data = request.get_json()
#     if not data or 'content' not in data:
#         abort(400, description="Missing 'content' in request body.")
    
#     readme_content = data['content']
    
#     # --- THIS IS THE FIX ---
#     # Load the Gemini API key from our environment variables
#     api_key = os.getenv("GEMINI_API_KEY")
#     if not api_key:
#         # This provides a clear error if the key is missing from the .env file
#         abort(500, description="GEMINI_API_KEY is not set in the environment.")

#     gemini_api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={api_key}"
    
#     # This prompt guides the AI to give us a structured, useful summary
#     prompt = f"Summarize this README file in 3-4 concise bullet points for a technical recruiter. Focus on the project's purpose, its main features, and the technology stack used. README content:\n\n{readme_content}"
#     payload = { "contents": [{ "parts": [{ "text": prompt }] }] }
    
#     try:
#         # Make the POST request to the Gemini API
#         response = requests.post(gemini_api_url, json=payload, timeout=20)
#         response.raise_for_status() # This will raise an error for bad status codes (like 403)
#         result = response.json()
        
#         # Safely extract the summary text from the response
#         if 'candidates' in result and result['candidates'][0]['content']['parts'][0]['text']:
#             summary = result['candidates'][0]['content']['parts'][0]['text']
#             return jsonify({"summary": summary})
#         else:
#             # Handle cases where the AI gives a valid but empty response
#             return jsonify({"summary": "AI model could not generate a summary for this content."})
        
#     except requests.exceptions.RequestException as e:
#         # Handle network errors or other issues with the API call
#         print(f"Error calling Gemini API: {e}")
#         abort(500, description="Failed to communicate with the AI service.")


# if __name__ == '__main__':
#     # Runs the Flask development server
#     app.run(debug=True, port=5001)













import os
import requests
from flask import Flask, jsonify, abort, render_template, request
from dotenv import load_dotenv

# Import ALL of our logic functions, including the new fetch_pinned_repos
from logic import (
    fetch_github_data,
    fetch_user_repos,
    analyze_repo_languages,
    calculate_activity_streak,
    fetch_pinned_repos
)

load_dotenv()
app = Flask(__name__)


@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html')


@app.route('/api/user/<string:username>')
def get_user_profile(username):
    """Handles requests for user data, including pinned repos."""
    page = request.args.get('page', 1, type=int)

    if page == 1:
        # For the initial load, fetch all primary data
        user_data = fetch_github_data(username)
        if not user_data:
            abort(404, description=f"User '{username}' not found.")

        # Fetch pinned repos and the first page of regular repos
        repos = fetch_user_repos(username, page=page)
        pinned_repos = fetch_pinned_repos(username)

        # Combine both lists for a complete language analysis
        all_repos_for_analysis = (pinned_repos or []) + (repos or [])
        language_stats = analyze_repo_languages(all_repos_for_analysis)

        response_data = {
            "profile": user_data,
            "pinned_repos": pinned_repos,  # Add pinned repos to the response
            "repos": repos,
            "language_stats": language_stats.most_common(5)
        }
    else:
        # For 'Load More', we only need the next page of regular repos
        repos = fetch_user_repos(username, page=page)
        response_data = {"repos": repos}

    return jsonify(response_data)


@app.route('/api/user/<string:username>/activity')
def get_user_activity(username):
    """Calculates and returns the user's longest contribution streak."""
    streak = calculate_activity_streak(username)
    return jsonify({"longest_streak": streak})


@app.route('/api/summarize', methods=['POST'])
def summarize_readme():
    """Receives README content and returns a summary using the Gemini API."""
    data = request.get_json()
    if not data or 'content' not in data:
        abort(400, description="Missing 'content' in request body.")

    readme_content = data['content']
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        abort(500, description="GEMINI_API_KEY is not set in the environment.")

    gemini_api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={api_key}"
    prompt = f"Summarize this README file in 3-4 concise bullet points for a technical recruiter. Focus on the project's purpose, its main features, and the technology stack used. README content:\n\n{readme_content}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(gemini_api_url, json=payload, timeout=20)
        response.raise_for_status()
        result = response.json()

        if 'candidates' in result and result['candidates'][0]['content']['parts'][0]['text']:
            summary = result['candidates'][0]['content']['parts'][0]['text']
            return jsonify({"summary": summary})
        else:
            return jsonify({"summary": "AI model could not generate a summary for this content."})

    except requests.exceptions.RequestException as e:
        print(f"Error calling Gemini API: {e}")
        abort(500, description="Failed to communicate with the AI service.")


if __name__ == '__main__':
    app.run(debug=True, port=5001)


