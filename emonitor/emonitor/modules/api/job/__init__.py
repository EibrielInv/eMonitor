import os
from pymongo import MongoClient
from bson import ObjectId
from flask import request
from flask import send_from_directory
#from flask.ext.restful import Api
from flask.ext.restful import Resource

from emonitor import app
from emonitor.modules.emonitor_data import emonitor_data


#api = Api(app)

class MongoConnection():
    def connect():
        client = MongoClient()
        db = client.emonitor
        renderJobs = db.renderJobs
        return renderJobs

class JobListApi(Resource):
    def post(self):
        renderJobs = MongoConnection.connect()
        data = emonitor_data()
        data.name = request.form['name']
        data.status = request.form['status']
        iid=renderJobs.insert(data.array())

        return {'uuid':str(iid)}, 200

class JobApi(Resource):
    def get(self, job_id=None):
        renderJobs = MongoConnection.connect()
        data_client=renderJobs.find_one({'_id':ObjectId(job_id)})
        emon_data = emonitor_data()
        emon_data.name = data_client['name']
        emon_data.status = data_client['status']
        emon_data.engine = data_client['engine']
        emon_data.freestyle = data_client['freestyle']
        emon_data.compositor = data_client['compositor']
        emon_data.sequencer = data_client['sequencer']
        emon_data.frame_start = data_client['frame_start']
        emon_data.frame_end = data_client['frame_end']
        emon_data.frame_current = data_client['frame_current']

        return emon_data.array(), 200

    def allowed_file(self, filename):
        return '.' in filename and \
            filename.rsplit('.', 1)[1] in ['png']

    def patch(self, job_id=None):
        # from werkzeug import secure_filename

        renderJobs = MongoConnection.connect()
        emon_data = emonitor_data()
        emon_data.status = str(request.form['status'])
        emon_data.engine = str(request.form['engine'])
        emon_data.freestyle = request.form['freestyle']=="True"
        emon_data.compositor = request.form['compositor']=="True"
        emon_data.sequencer = request.form['sequencer']=="True"
        emon_data.frame_start = int(request.form['frame_start'])
        emon_data.frame_end = int(request.form['frame_end'])
        if 'frame_current' in request.form:
            emon_data.frame_current = int(request.form['frame_current'])

        jobpath = os.path.join(app.config['THUMBNAIL_STORAGE'], job_id)
        if not os.path.exists(jobpath):
            os.mkdir(jobpath)
        try:
            file = request.files.get('images')
            if file and self.allowed_file(file.filename):
                filename = "{0}_{1}.png".format(
                    job_id, request.form['frame_current'])
                fullname = os.path.join(jobpath, filename)
                file.save(fullname)
        except:
            print ("Error reading file")

        key = {'_id':ObjectId(job_id)}
        renderJobs.update(key, {'$set':emon_data.array_update()})

class JobThumbnailApi(Resource):
    def get(self, job_id, frame):
        """Given a job_id returns the output file
        """
        jobpath = os.path.join(app.config['THUMBNAIL_STORAGE'], job_id)
        imagename = "{0}_{1}.png".format(job_id, frame)
        return send_from_directory(jobpath, imagename)
