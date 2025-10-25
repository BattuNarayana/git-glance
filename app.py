import os
import requests
from flask import Flask, jsonify, abort, render_template, request
from dotenv import load_dotenv

# Import ALL of our logic functions, including the final get_ai_summary
from logic import (
    fetch_github_data,
    fetch_user_repos,
    analyze_repo_languages,
    calculate_activity_streak,
    fetch_pinned_repos,
    get_ai_summary # Make sure the final AI function is imported
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
        # Ensure lists are not None before combining
        all_repos_for_analysis = (pinned_repos or []) + (repos or [])
        language_stats = analyze_repo_languages(all_repos_for_analysis)

        response_data = {
            "profile": user_data,
            "pinned_repos": pinned_repos, # Include pinned repos in the response
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
def summarize_readme_route():
    """
    Receives owner/repo and calls the robust get_ai_summary function.
    Handles potential errors returned from the logic function.
    """
    data = request.get_json()
    if not data or 'owner' not in data or 'repo' not in data:
        abort(400, description="Missing 'owner' or 'repo' in request body.")

    owner = data['owner']
    repo = data['repo']

    # Call the robust logic function which handles caching, retries, etc.
    summary_result = get_ai_summary(owner, repo)

    # Check if the logic function returned an error string
    if isinstance(summary_result, str) and summary_result.startswith('Error:'):
        # Pass the specific error message back to the frontend
        abort(500, description=summary_result)

    # If successful, return the summary
    return jsonify({"summary": summary_result})


if __name__ == '__main__':
    # Runs the Flask development server
    # Note: Use host='0.0.0.0' if running inside Docker and need external access
    app.run(debug=True, port=5001)
