import os
from datetime import datetime, timezone
from flask import Flask, jsonify, render_template, request

# In-memory storage for tasks
class TaskStore:
    def __init__(self):
        self._tasks = []
        self._counter = 1

    def get_all(self):
        return list(self._tasks)

    def get_by_id(self, task_id):
        for task in self._tasks:
            if task["id"] == task_id:
                return task
        return None

    def add(self, title, description="", category="General", priority="Medium"):
        task = {
            "id": self._counter,
            "title": title.strip(),
            "description": description.strip(),
            "category": category.strip() or "General",
            "priority": priority.strip() or "Medium",
            "completed": False,
            "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        }
        self._tasks.append(task)
        self._counter += 1
        return task

    def toggle_complete(self, task_id):
        task = self.get_by_id(task_id)
        if task:
            task["completed"] = not task["completed"]
            return task
        return None

    def set_completed(self, task_id, completed=True):
        task = self.get_by_id(task_id)
        if task:
            task["completed"] = completed
            return task
        return None

    def delete(self, task_id):
        initial_len = len(self._tasks)
        self._tasks = [t for t in self._tasks if t["id"] != task_id]
        return len(self._tasks) < initial_len

    def get_stats(self):
        total = len(self._tasks)
        completed = sum(1 for t in self._tasks if t["completed"])
        pending = total - completed
        return {
            "total": total,
            "completed": completed,
            "pending": pending
        }

    def clear(self):
        self._tasks = []
        self._counter = 1

    def seed_defaults(self):
        self.clear()
        self.add("Complete Jenkins CI/CD Setup", "Configure pipeline and credentials in Jenkins", "DevOps", "High")
        self.add("Build Docker Image", "Containerize Flask application with Gunicorn", "Docker", "Medium")
        self.add("Deploy to Minikube Kubernetes", "Apply deployment and service manifests", "Kubernetes", "High")


# Global store instance
task_store = TaskStore()


def create_app(test_config=None):
    app = Flask(__name__)

    # Default configuration
    app.config["APP_VERSION"] = os.getenv("APP_VERSION", "local")

    if test_config:
        app.config.update(test_config)

    # UI Dashboard Route
    @app.route("/", methods=["GET"])
    def index():
        app_version = os.getenv("APP_VERSION", app.config.get("APP_VERSION", "local"))
        stats = task_store.get_stats()
        return render_template(
            "index.html",
            app_version=app_version,
            stats=stats,
            tasks=task_store.get_all()
        )

    # Health Check Endpoint
    @app.route("/health", methods=["GET"])
    def health():
        app_version = os.getenv("APP_VERSION", app.config.get("APP_VERSION", "local"))
        return jsonify({
            "status": "healthy",
            "version": app_version,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 200

    # Version Endpoint
    @app.route("/version", methods=["GET"])
    def version():
        app_version = os.getenv("APP_VERSION", app.config.get("APP_VERSION", "local"))
        return jsonify({
            "version": app_version
        }), 200

    # API Endpoints
    @app.route("/api/tasks", methods=["GET"])
    def get_tasks():
        return jsonify({
            "tasks": task_store.get_all(),
            "stats": task_store.get_stats()
        }), 200

    @app.route("/api/tasks", methods=["POST"])
    def add_task():
        data = request.get_json(silent=True) or request.form
        title = data.get("title")

        if not title or not str(title).strip():
            return jsonify({"error": "Task title is required"}), 400

        description = data.get("description", "")
        category = data.get("category", "General")
        priority = data.get("priority", "Medium")

        new_task = task_store.add(title, description, category, priority)
        return jsonify({
            "message": "Task created successfully",
            "task": new_task,
            "stats": task_store.get_stats()
        }), 201

    @app.route("/api/tasks/<int:task_id>/complete", methods=["PUT", "PATCH"])
    def complete_task(task_id):
        data = request.get_json(silent=True)
        completed = True
        if data and "completed" in data:
            completed = bool(data["completed"])
            task = task_store.set_completed(task_id, completed)
        else:
            task = task_store.set_completed(task_id, True)

        if not task:
            return jsonify({"error": f"Task with ID {task_id} not found"}), 404

        return jsonify({
            "message": "Task updated successfully",
            "task": task,
            "stats": task_store.get_stats()
        }), 200

    @app.route("/api/tasks/<int:task_id>/toggle", methods=["POST"])
    def toggle_task(task_id):
        task = task_store.toggle_complete(task_id)
        if not task:
            return jsonify({"error": f"Task with ID {task_id} not found"}), 404

        return jsonify({
            "message": "Task toggled successfully",
            "task": task,
            "stats": task_store.get_stats()
        }), 200

    @app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
    def delete_task(task_id):
        deleted = task_store.delete(task_id)
        if not deleted:
            return jsonify({"error": f"Task with ID {task_id} not found"}), 404

        return jsonify({
            "message": "Task deleted successfully",
            "stats": task_store.get_stats()
        }), 200

    # Error Handlers
    @app.errorhandler(404)
    def not_found_error(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Resource not found"}), 404
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Internal server error"}), 500
        return render_template("500.html"), 500

    return app


# Application entry point for Gunicorn / Flask CLI
app = create_app()

if __name__ == "__main__":
    # Seed sample tasks for local interactive testing
    task_store.seed_defaults()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
