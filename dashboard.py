# dashboard.py
from flask import Flask, render_template_string
from db_manager import DBManager
from dotenv import load_dotenv

# Load environment variables to get the database URL
load_dotenv()

app = Flask(__name__)

# This is our simple HTML template with some basic styling
HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Metamorph Dashboard</title>
    <style>
      body { font-family: sans-serif; background-color: #f4f4f9; color: #333; margin: 2em; }
      h1 { color: #444; }
      table { width: 100%; border-collapse: collapse; box-shadow: 0 2px 3px rgba(0,0,0,0.1); }
      th, td { padding: 12px; border: 1px solid #ddd; text-align: left; }
      th { background-color: #6c7ae0; color: white; }
      tr:nth-child(even) { background-color: #f2f2f2; }
      .status-completed { color: green; font-weight: bold; }
      .status-failed { color: red; font-weight: bold; }
      .status-pending { color: orange; font-weight: bold; }
    </style>
  </head>
  <body>
    <h1>Metamorph Agent - Task Dashboard</h1>
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>Type</th>
          <th>Description</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        {% for task in tasks %}
        <tr>
          <td>{{ task.id }}</td>
          <td>{{ task.task_type }}</td>
          <td>{{ task.description }}</td>
          <td class="status-{{ task.status.lower() }}">{{ task.status }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </body>
</html>
"""

@app.route('/')
def index():
    db = DBManager()
    # Fetch the 15 most recent tasks, ordered by most recent first
    tasks = db.query_all("SELECT id, task_type, description, status FROM tasks ORDER BY id DESC LIMIT 15")
    return render_template_string(HTML_TEMPLATE, tasks=tasks)

if __name__ == '__main__':
    # Run the app, making it accessible from your VM's public IP
    app.run(host='0.0.0.0', port=8080)
