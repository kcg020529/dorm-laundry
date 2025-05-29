from flask import Flask, request
import subprocess

app = Flask(__name__)

@app.route("/github-webhook", methods=["POST"])
def webhook():
    # Git pull
    subprocess.run(["git", "-C", "/home/ec2-user/dorm-laundry", "pull"], capture_output=True, text=True)

    # (선택) Django 명령어 실행
    subprocess.run(["python3", "manage.py", "collectstatic", "--noinput"], cwd="/home/ec2-user/dorm-laundry")
    subprocess.run(["python3", "manage.py", "migrate"], cwd="/home/ec2-user/dorm-laundry")

    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
