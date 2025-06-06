from flask import Flask, request
import subprocess
import logging
import os

# 로그 설정
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route("/github-webhook", methods=["POST"])
def webhook():
    logger.info("Webhook received")

    project_path = "/home/ec2-user/dorm_laundry"
    python_path = os.path.join(project_path, "venv/bin/python")

    # 공통 환경 설정
    env = os.environ.copy()
    env["DJANGO_SETTINGS_MODULE"] = "config.settings"

    # 1. git pull
    pull = subprocess.run(
        ["git", "-C", project_path, "pull"],
        capture_output=True,
        text=True,
        env=env
    )
    logger.info("git pull stdout:\n%s", pull.stdout)
    if pull.stderr:
        logger.error("git pull stderr:\n%s", pull.stderr)

    # 2. collectstatic
    static = subprocess.run(
        [python_path, "manage.py", "collectstatic", "--noinput"],
        cwd=project_path,
        capture_output=True,
        text=True,
        env=env
    )
    logger.info("collectstatic output:\n%s", static.stdout or static.stderr)
    if static.stderr:
        logger.error("collectstatic stderr:\n%s", static.stderr)

    # 3. migrate
    migrate = subprocess.run(
        [python_path, "manage.py", "migrate"],
        cwd=project_path,
        capture_output=True,
        text=True,
        env=env
    )
    logger.info("migrate output:\n%s", migrate.stdout or migrate.stderr)
    if migrate.stderr:
        logger.error("migrate stderr:\n%s", migrate.stderr)

    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)