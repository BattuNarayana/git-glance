GitGlance AI Dashboard
<!-- Replace with a real screenshot URL -->

GitGlance is a full-stack, AI-powered web application designed to provide deep, at-a-glance analytics for GitHub user profiles. Created for developers, hiring managers, and technical recruiters, it transforms a standard GitHub profile into a rich, interactive dashboard, saving time and revealing key insights about a developer's activity, skills, and focus.

This project evolved from a simple command-line tool into a complete, containerized, high-performance web service with an AI-driven feature set, demonstrating a wide breadth of modern software engineering principles and technologies.

✨ Core Features
Interactive Web Dashboard: A clean, dynamic, and responsive UI built with vanilla JavaScript, HTML, and CSS.

Comprehensive Profile Analytics: Displays key stats, top languages (visualized with Chart.js), and pinned repositories.

AI-Powered README Summaries: Integrates the Gemini API to provide on-demand, AI-generated summaries of any project's README file, saving recruiters valuable time.

Deep Activity Insights: Features a custom-built backend process to analyze a user's event history and calculate their longest consecutive contribution streak.

Infinite Scroll: A "Load More" feature allows users to seamlessly browse through a developer's entire repository history.

Shareable URLs: The application state is managed in the URL, allowing users to share direct links to a specific user's dashboard.

🛠️ Architecture & Tech Stack
This project was architected as a modern, multi-tiered web application, showcasing skills in both backend and frontend development.

Tier

Technology / Concept

Purpose

Frontend

HTML5, CSS3, JavaScript

To build a dynamic, responsive, and user-friendly single-page application.



Chart.js

For rich data visualization of language statistics.

Backend

Python

The core programming language for the application logic.



Flask

A lightweight web framework used to build the backend REST API.



Gemini API

For state-of-the-art AI-powered text summarization.

Database

Redis

A high-performance, in-memory database used for caching API responses.

DevOps

Docker

For containerizing both the Redis server and the core application.

APIs

GitHub REST API & GraphQL API

Used to fetch user profiles, repositories, activity events, and pinned projects.

Testing

pytest

To ensure the reliability and correctness of the backend logic.

🚀 Running the Project Locally
To run GitGlance on your local machine, you will need Docker and Python installed.

1. Clone the Repository
git clone [https://github.com/your-username/git-glance.git](https://github.com/your-username/git-glance.git)
cd git-glance

2. Set Up Environment Variables
Create a .env file in the root of the project and add your API keys:

GITHUB_TOKEN=ghp_YourGitHubPersonalAccessToken
GEMINI_API_KEY=YourGoogleAIGeminiAPIKey

3. Start the Redis Server
Run the Redis database using Docker:

docker run -d --name redis-stack -p 6379:6379 redis/redis-stack:latest

4. Install Dependencies
Install all the required Python packages:

pip install -r requirements.txt

5. Run the Web Application
Start the Flask development server:

python app.py

The application will be available at http://127.0.0.1:5001.

🧪 Running the Tests
To ensure the backend logic is working correctly, you can run the automated test suite:

pytest
