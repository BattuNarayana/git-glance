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
