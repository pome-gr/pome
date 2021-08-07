import os
from flask import Flask
from flask import render_template

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True  # not working


@app.route("/")
def hello_world():
    return render_template("index.html", pwd=os.getcwd())
