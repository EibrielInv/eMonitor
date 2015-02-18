from flask import Flask
from flask import Blueprint
from flask import render_template

main = Blueprint('main', __name__)

@main.route('/')
@main.route('/<job_id>')
def index(job_id=None):
    return render_template('index.html')


