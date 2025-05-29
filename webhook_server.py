from flask import Flask, request
import subprocess

app = Flask(__name__)

@app.route("/github-webhook", methods=["POST"])
def webhook():
    print("✅ Webhook received")

    project_path = "/home/ec2-user/dorm-laundry"
    python_path = "/home/ec2-user/dorm-laundry/venv/bin/python"

    # git pull
    pull = subprocess.run(["git", "-C", project_path, "pull"], capture_output=True, text=True)
    print("📦 git pull stdout:", pull.stdout)
    print("❌ git pull stderr:", pull.stderr)

    # collectstatic
    static = subprocess.run(
        [python_path, "manage.py", "collectstatic", "--noinput"],
        cwd=project_path,
        capture_output=True,
        text=True
    )
    print("🧼 collectstatic:", static.stdout or static.stderr)

    # migrate
    migrate = subprocess.run(
        [python_path, "manage.py", "migrate"],
        cwd=project_path,
        capture_output=True,
        text=True
    )
    print("📂 migrate:", migrate.stdout or migrate.stderr)

    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)