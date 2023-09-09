import os
from flask import (
    Flask,
    jsonify,
    render_template,
)
from get_data import get_result
from flask_caching import Cache

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

app.config.from_mapping({"CACHE_TYPE": "SimpleCache", "CACHE_DEFAULT_TIMEOUT": 60})
cache = Cache(app)


@app.route("/get_data")
@cache.cached(timeout=59)
def get_data():
    response = jsonify(get_result())
    response.headers["Content-Type"] = "application/json"
    return response


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run()
