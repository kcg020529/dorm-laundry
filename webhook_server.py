from flask import Flask, request
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route("/github-webhook", methods=["POST"])
def webhook():
    logger.info("✅ Webhook received")

    project_path = "/home/ec2-user/dorm-laundry"
    python_path = "/home/ec2-user/dorm-laundry/venv/bin/python"

    # git pull
    pull = subprocess.run(["git", "-C", project_path, "pull"], capture_output=True, text=True)
    logger.info("📦 git pull stdout: %s", pull.stdout)
    logger.error("❌ git pull stderr: %s", pull.stderr)

    # collectstatic
    static = subprocess.run(
        [python_path, "manage.py", "collectstatic", "--noinput"],
        cwd=project_path,
        capture_output=True,
        text=True
    )
    logger.info("🧼 collectstatic: %s", static.stdout or static.stderr)

    # migrate
    migrate = subprocess.run(
        [python_path, "manage.py", "migrate"],
        cwd=project_path,
        capture_output=True,
        text=True
    )
    logger.info("📂 migrate: %s", migrate.stdout or migrate.stderr)

    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)