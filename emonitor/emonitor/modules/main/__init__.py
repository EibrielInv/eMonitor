from flask import Flask
from flask import Blueprint
from flask import render_template

main = Blueprint('main', __name__)

@main.route('/')
@main.route('/<job_id>')
def index(job_id=None):
    return render_template('index.html', job_id=job_id)


@main.route('/movie/')
@main.route('/movie/<job_id>')
def movie(job_id=None):
    return render_template('movie.html')
