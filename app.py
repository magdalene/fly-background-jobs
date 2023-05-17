from flask import Flask, render_template, redirect, request, url_for

from worker_lib import clean_up, run_task, get_results

app = Flask(__name__)

with open("static/index.html", "rt") as f:
    index_contents = f.read()


def render_index():
    return index_contents


def send_email():
    address = request.form["address"]
    subject = request.form["subject"]
    body = request.form["body"]
    send_id = run_task("tasks", "dummy_send_email", [address, subject, body])["task_id"]
    return redirect(url_for("status", send_id=send_id))


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_index()

    elif request.method == "POST":
        return send_email()


@app.route("/status/<send_id>", methods=["GET"])
def status(send_id):
    results = get_results(send_id)
    try:
        status = "SENT" if results["status"] == "SUCCESS" else results["status"]
    except KeyError:
        import json
        raise Exception(json.dumps(results))
    if status != "PENDING":
        clean_up(send_id)
    return render_template("status.html", status=status, details=results.get("result"))