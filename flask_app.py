import os
from flask import (
    Flask,
    jsonify,
    render_template,
)
from get_data import get_result

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")


@app.route("/get_data")
def get_data():
    response = jsonify(get_result())
    response.headers["Content-Type"] = "application/json"
    return response


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run()
