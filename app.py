# import os
# import requests
# from flask import Flask, jsonify, abort, render_template, request
# from dotenv import load_dotenv

# # Import ALL logic functions, including the new persona generator
# from logic import (
#     fetch_github_data,
#     fetch_user_repos,
#     analyze_repo_languages,
#     calculate_activity_streak,
#     fetch_pinned_repos,
#     get_ai_summary,
#     generate_developer_summary # Added new import
# )

# load_dotenv()
# app = Flask(__name__)


# @app.route('/')
# def index():
#     """Serves the main HTML page."""
#     return render_template('index.html')


# @app.route('/api/user/<string:username>')
# def get_user_profile(username):
#     """Handles requests for user data, including pinned repos."""
#     page = request.args.get('page', 1, type=int)

#     if page == 1:
#         # For the initial load, fetch all primary data
#         user_data = fetch_github_data(username)
#         if not user_data:
#             abort(404, description=f"User '{username}' not found.")

#         # Fetch pinned repos and the first page of regular repos
#         repos = fetch_user_repos(username, page=page)
#         pinned_repos = fetch_pinned_repos(username)

#         # Combine both lists for a complete language analysis
#         all_repos_for_analysis = (pinned_repos or []) + (repos or [])
#         language_stats = analyze_repo_languages(all_repos_for_analysis)

#         response_data = {
#             "profile": user_data,
#             "pinned_repos": pinned_repos,
#             "repos": repos,
#             "language_stats": language_stats.most_common(5)
#         }
#     else:
#         # For 'Load More', we only need the next page of regular repos
#         repos = fetch_user_repos(username, page=page)
#         response_data = {"repos": repos}

#     return jsonify(response_data)


# @app.route('/api/user/<string:username>/activity')
# def get_user_activity(username):
#     """Calculates and returns the user's longest contribution streak."""
#     streak = calculate_activity_streak(username)
#     return jsonify({"longest_streak": streak})


# @app.route('/api/summarize', methods=['POST'])
# def summarize_readme_route():
#     """
#     Receives owner/repo and calls the robust get_ai_summary function.
#     Handles potential errors returned from the logic function.
#     """
#     data = request.get_json()
#     if not data or 'owner' not in data or 'repo' not in data:
#         abort(400, description="Missing 'owner' or 'repo' in request body.")

#     owner = data['owner']
#     repo = data['repo']

#     summary_result = get_ai_summary(owner, repo)

#     if isinstance(summary_result, str) and summary_result.startswith('Error:'):
#         abort(500, description=summary_result)

#     return jsonify({"summary": summary_result})

# # --- NEW: API Endpoint for AI Persona Summary ---
# @app.route('/api/user/<string:username>/persona')
# def get_developer_persona(username):
#     """Generates and returns an AI persona summary for the user."""
#     # Fetch required data first (leverages existing caching)
#     user_data = fetch_github_data(username)
#     if not user_data:
#          abort(404, description=f"User '{username}' not found for persona generation.")
         
#     # Fetch first page of repos for language analysis
#     repos_data = fetch_user_repos(username, page=1) 
    
#     # Generate the summary
#     persona_summary = generate_developer_summary(user_data, repos_data)

#     # Handle potential errors from the generator function
#     if isinstance(persona_summary, str) and persona_summary.startswith('Error:'):
#         abort(500, description=persona_summary)

#     return jsonify({"persona_summary": persona_summary})


# if __name__ == '__main__':
#     # Runs the Flask development server
#     app.run(debug=True, port=5001)



import os
import requests
from flask import Flask, jsonify, abort, render_template, request
from dotenv import load_dotenv
from flask_cors import CORS # Import CORS

# Import ALL of our final logic functions
from logic import (
    fetch_github_data,
    fetch_user_repos,
    analyze_repo_languages,
    calculate_activity_streak,
    fetch_pinned_repos, # Make sure this is imported
    get_ai_summary, # The robust summarizer
    generate_developer_summary # The AI persona
)

load_dotenv()
app = Flask(__name__)
CORS(app) # Enable CORS for all routes


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
            print(f"Aborting: User '{username}' not found.")
            abort(404, description=f"User '{username}' not found.")

        # --- THIS IS THE FIX ---
        # Fetch pinned repos and the first page of regular repos
        repos = fetch_user_repos(username, page=page)
        pinned_repos = fetch_pinned_repos(username) # Call the function

        # Combine both lists for a complete language analysis
        all_repos_for_analysis = (pinned_repos or []) + (repos or [])
        language_stats = analyze_repo_languages(all_repos_for_analysis)

        response_data = {
            "profile": user_data,
            "pinned_repos": pinned_repos, # Add pinned repos to the response
            "repos": repos,
            "language_stats": language_stats.most_common(5)
        }
    else:
        # For 'Load More' (which we removed from UI, but API logic is safe)
        repos = fetch_user_repos(username, page=page)
        response_data = {"repos": repos if repos else []}

    return jsonify(response_data)


@app.route('/api/user/<string:username>/activity')
def get_user_activity(username):
    """Calculates and returns the user's longest contribution streak."""
    streak = calculate_activity_streak(username)
    return jsonify({"longest_streak": streak})


@app.route('/api/summarize', methods=['POST'])
def summarize_readme_route():
    """
    Receives owner/repo and calls the robust get_ai_summary function from logic.py.
    """
    data = request.get_json()
    if not data or 'owner' not in data or 'repo' not in data:
        print("Summarize error: Missing owner or repo in request")
        abort(400, description="Missing 'owner' or 'repo' in request body.")

    owner = data['owner']
    repo = data['repo']

    # --- THIS IS THE FIX ---
    # Call the final, robust logic function which handles caching, retries, etc.
    summary_result = get_ai_summary(owner, repo)

    # Check if the logic function returned an error string
    if isinstance(summary_result, str) and summary_result.startswith('Error:'):
        print(f"Summarize error from logic: {summary_result}")
        abort(500, description=summary_result)

    # If successful, return the summary
    return jsonify({"summary": summary_result})


@app.route('/api/user/<string:username>/persona')
def get_developer_persona(username):
    """Generates and returns an AI persona summary for the user."""
    user_data = fetch_github_data(username)
    if not user_data:
         print(f"Persona error: User '{username}' not found.")
         abort(404, description=f"User '{username}' not found for persona generation.")

    repos_data = fetch_user_repos(username, page=1)
    persona_summary = generate_developer_summary(user_data, repos_data)

    if isinstance(persona_summary, str) and persona_summary.startswith('Error:'):
        print(f"Persona error from logic: {persona_summary}")
        abort(500, description=persona_summary)

    return jsonify({"persona_summary": persona_summary})


if __name__ == '__main__':
    # Runs the Flask development server
    app.run(debug=True, port=5001)

