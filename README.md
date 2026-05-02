WeekenderRank

WeekenderRank is a mobile-first Python web application built with Flask, designed for clubs and sports groups to establish player rankings through anonymous peer-rating. It features a professional, minimalist UI and automated logic to balance teams based on current skill levels.

🚀 Features

Identity-Based Polling: Only players registered in the roster can vote. Users select their name to begin.

One-Vote-Per-User: The system tracks submissions per identity, allowing users to update their previous ratings rather than creating duplicates.

Real-Time Leaderboard: A dynamic ranking view that calculates average scores across all peer submissions.

Balanced Team Generation: Automatically splits the roster into "Team A" and "Team B" by alternating ranking positions (1st to A, 2nd to B, 3rd to A, etc.) to ensure fair play.

Admin Panel: A password-protected section to add or delete players from the roster and manage the data.

Persistent Storage: All data is saved to a local rankings.json file on the server.

🛠️ Installation & Setup

Prerequisites

Python 3.x

Flask

Running Locally

Clone or download the app.py file to your project folder.

Install Flask:

pip install Flask

Run the application:

python app.py

Access the app: Open http://127.0.0.1:5000 in your web browser. (Use "Responsive Design Mode" in your browser's developer tools for the best mobile experience).

🔐 Admin Access

Click the lock icon in the header to access the Admin Panel.

Default Password: admin

Note: In a production environment, change the ADMIN_PASSWORD variable or set it via an environment variable.

☁️ Hosting on the Internet

To make this app available to your players on their mobile devices, consider these options:

ngrok: Best for temporary testing. Run ngrok http 5000 to create a public tunnel to your local machine.

PythonAnywhere: A great free/low-cost option for persistent Python hosting.

Render / Railway: Modern cloud platforms. Ensure you set the FLASK_SECRET_KEY and ADMIN_PASSWORD environment variables in their dashboard.

📁 Data Management

The application stores all state in rankings.json.

Persistence: Data remains available even if the server restarts.

Portability: You can backup the rankings.json file to move your data to a different server.

Created for the Weekender Badminton Group.
