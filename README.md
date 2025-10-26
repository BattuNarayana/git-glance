GitGlance – AI-Powered GitHub Analytics Dashboard




A full-stack, AI-driven analytics platform that delivers an instant, comprehensive view of any GitHub profile — blending data visualization, caching, and AI summarization into one elegant dashboard.

► Get The Application

Access the latest release for developers and users on the GitHub Releases page
.

Key Features

GitGlance transforms how developers, recruiters, and hiring managers interpret GitHub activity, providing real-time, AI-enhanced insights:

📌 Core Profile Overview: Displays name, bio, company, location, and join date in a clean layout.

📊 Key Statistics: Shows follower/following counts, repository totals, and contribution activity.

⭐ Pinned Repositories: Fetches highlighted projects using the GitHub GraphQL API.

🧠 AI Persona Summary: Generates a concise AI-driven summary of the developer’s skills, focus areas, and strengths.

📜 Recent Repositories: Lists latest repositories with metadata—stars, forks, and topic tags.

🤖 AI README Summarizer: Summarizes repository README files using the Google Gemini API.

🔥 Activity Streak Analysis: Computes the user’s longest contribution streak using real GitHub event data.

🎨 Top Languages Visualization: Displays a dynamic doughnut chart of the most-used languages via Chart.js.

🌓 Theme Toggle: Supports light/dark modes with persistent local storage.

🔗 Shareable URLs: Enables direct profile links using query parameters (/?q=username).

Technology Stack

GitGlance is architected with scalability, modularity, and performance in mind.

Backend

Language: Python 3

Framework: Flask

APIs:

GitHub REST API (v3)

GitHub GraphQL API (v4)

Google Gemini API

Caching: Redis (via Docker) for storing user, repo, and summary data

Configuration: python-dotenv for secure environment management

Testing: pytest for backend validation

Frontend

Structure: HTML5 + Vanilla JavaScript (ES6+)

Styling: CSS3 (Flexbox, Grid, CSS Variables, animations)

Visualization: Chart.js for graphical insights

Behavior:

Asynchronous data fetching

Dynamic DOM updates

URL state management

Local theme persistence

DevOps & Packaging

Containerization: Docker & Dockerfile for Redis and optional Flask deployment

Version Control: Git & GitHub

Logging: Console-based and extendable for production environments

Installation & Usage (for Developers)

To run GitGlance locally from the source code:

Clone the repository:

git clone https://github.com/BattuNarayana/git-glance.git
cd git-glance


Create and configure the .env file:

GITHUB_TOKEN=ghp_YourGitHubPersonalAccessToken
GEMINI_API_KEY=YourGoogleGeminiAPIKey


(Refer to GitHub and Google AI Studio documentation for API key creation.)

Install Python dependencies:

pip install -r requirements.txt


Start the Redis container:

docker run -d --name redis-stack -p 6379:6379 -p 8001:8001 redis/redis-stack:latest


(If already created, use docker start redis-stack.)

Run the Flask application:

python app.py


Open the dashboard:
Visit http://localhost:5000 in your browser.

Run backend tests (optional):

pytest

Project Structure
git-glance/
├── templates/
│   └── index.html        # Frontend structure (HTML, CSS, JS)
├── .env                  # Environment variables (not committed)
├── .gitignore            # Git ignore rules
├── app.py                # Flask backend web server & API
├── logic.py              # Core logic (API calls, caching, AI)
├── main.py               # Original CLI prototype
├── Dockerfile            # Optional container setup
├── requirements.txt      # Dependencies list
├── test_main.py          # Unit tests (pytest)
└── README.md             # Documentation

License

This project is licensed under the MIT License.
See the LICENSE file for full details.