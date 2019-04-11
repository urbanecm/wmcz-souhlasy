#!/usr/bin/env python
#-*- coding: utf-8 -*-

import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
import yaml

app = Flask(__name__)

# Load configuration from YAML file
__dir__ = os.path.dirname(__file__)
app.config.update(
    yaml.safe_load(open(os.path.join(__dir__, os.environ.get(
        'FLASK_CONFIG_FILE', 'config.yaml')))))

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)


@app.route('/')
def index():
	return render_template('index.html')

if __name__ == "__main__":
	app.run(debug=True, port=2000)
