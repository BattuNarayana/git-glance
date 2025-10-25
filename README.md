GitGlance AI Dashboard

GitGlance is a deep-dive analytics platform for GitHub profiles, designed to provide comprehensive insights at a glance. It goes beyond basic stats, offering AI-powered summaries, activity analysis, and a polished user interface.

![GitGlance Dashboard Screenshot](https://github.com/user-attachments/assets/d85f1ccc-070d-4cde-9277-852a42891144)

The Problem Solved

Recruiters, hiring managers, and developers often need a quick, comprehensive overview of a GitHub user's profile to understand their skills, activity, and key projects. Navigating the full GitHub UI can be time-consuming and doesn't always surface the most critical information immediately.

The Solution: GitGlance

GitGlance provides a fast, insightful, and visually appealing web dashboard that aggregates and analyzes key GitHub profile data, including:

Core Profile Info: Name, bio, location, company, join date.

Key Stats: Follower/following count, public repository count.

📌 Pinned Repositories: Highlights the user's most important projects.

📊 Top Languages: A visual chart (doughnut) showing the primary languages used in recent repositories.

✨ AI Persona Summary: A concise, AI-generated summary of the developer's profile, highlighting their likely skills and focus areas.

📜 Latest Repositories: A scrollable list of the user's recent public repositories with descriptions, star/fork counts, and topic tags (skills).

🤖 AI README Summarizer: On-demand, AI-powered summaries of individual repository README files.

🏃 Activity Streak: Calculates the user's longest streak of consecutive contribution days based on recent public events.

🌓 Theme Toggle: Switch between professional dark and light modes.

🔗 Shareable URLs: Search results update the URL (/?q=username), allowing direct linking to specific profiles.

Technologies & Architecture

GitGlance is a full-stack application built with a modern, professional technology stack:

Backend:

Language: Python 3

Framework: Flask (for the web server and REST API)

API Integrations:

GitHub REST API (v3): For core profile and repository data.

GitHub GraphQL API (v4): For fetching pinned repositories efficiently.

Google Gemini API: For AI-powered README summarization and developer persona generation.

Caching: Redis (running in Docker) for high-performance caching of API results (user data, repos, summaries, personas, streaks), significantly reducing latency and API usage. Includes robust retry logic (exponential backoff) for external API calls.

Configuration: python-dotenv for securely managing API keys (.env file).

Frontend:

Structure: HTML5

Styling: CSS3 (including CSS Variables for theming, Flexbox, Grid, animations)

Interactivity: Vanilla JavaScript (ES6+)

Fetching data from the backend API (fetch).

Asynchronous loading for performance (profile loads instantly, stats update as ready).

Dynamic DOM manipulation to build the dashboard.

Chart.js for language visualization.

URL state management (history.pushState, URLSearchParams).

Local Storage for theme preference persistence.

Development & Deployment:

Containerization: Docker & Dockerfile used to package the Redis service and (optionally) the Flask application itself for easy setup and deployment.

Testing: pytest for backend unit tests (demonstrated in initial CLI version, can be expanded for Flask).

Version Control: Git & GitHub.

Project Structure

git-glance/
├── templates/
│   └── index.html       # Frontend HTML, CSS, and JavaScript
├── .env                 # Stores API keys (GITHUB_TOKEN, GEMINI_API_KEY) - *Not committed*
├── .gitignore           # Specifies files/folders for Git to ignore
├── app.py               # Flask backend web server and API endpoints
├── Dockerfile           # Recipe to containerize the Flask app (optional for running)
├── logic.py             # Core backend logic (API calls, caching, AI prompts, data processing)
├── main.py              # Original CLI version (kept for reference/testing)
├── README.md            # This file
├── requirements.txt     # Python dependencies
└── test_main.py         # Pytest tests for the original CLI logic


Running the Application Locally

Prerequisites:

Python 3.8+

Docker Desktop (running)

Git

Setup:

Clone the repository:

git clone [https://github.com/BattuNarayana/git-glance.git](https://github.com/BattuNarayana/git-glance.git)
cd git-glance


Create and configure the .env file:

Create a file named .env in the project root.

Add your API keys:

GITHUB_TOKEN=ghp_YourGitHubPersonalAccessToken
GEMINI_API_KEY=YourGoogleGeminiAPIKey


(See GitHub/Google AI Studio docs for how to generate these keys)

Install Python dependencies:

pip install -r requirements.txt


Start the Redis container:

docker run -d --name redis-stack -p 6379:6379 -p 8001:8001 redis/redis-stack:latest


(If the container already exists from a previous run, use docker start redis-stack instead)

Run the Flask application:

python app.py
