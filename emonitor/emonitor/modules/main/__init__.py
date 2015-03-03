from flask import Flask
from flask import Blueprint
from flask import render_template

from bson import ObjectId
from pymongo import MongoClient

from emonitor import app

main = Blueprint('main', __name__)


class MongoConnection():
    def connect():
        client = MongoClient()
        db = client.emonitor
        renderJobs = db.renderJobs
        return renderJobs


def getJobData(job_id):
    if not ObjectId.is_valid(job_id):
        return False

    renderJobs = MongoConnection.connect()
    data_job = renderJobs.find_one({'_id': ObjectId(job_id)})
    if not data_job:
        return False
    return data_job


@main.route('/')
@main.route('/<job_id>')
def index(job_id=None):
    data_job = getJobData(job_id)
    if not data_job:
        job_id = ''
    return render_template('index.html', job_id=job_id)


@main.route('/movie/')
@main.route('/movie/<job_id>')
def movie(job_id=None):
    data_job = getJobData(job_id)
    if not data_job:
        job_id = '54f563487ff6a931e54d7f12'
    return render_template('movie.html', job_id=job_id)


@app.errorhandler(404)
def page_not_found(e):
    job_id = ''
    return render_template('index.html', job_id=job_id), 404
