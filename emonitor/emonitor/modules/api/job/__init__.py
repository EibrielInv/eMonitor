import os
import random

from pymongo import MongoClient
from bson import ObjectId
from flask import request
from flask import send_from_directory
from flask.ext.restful import Resource
from flask.ext.restful import reqparse

from emonitor import app
from emonitor.modules.eMongo import Document


oem_parser = reqparse.RequestParser()
oem_parser.add_argument('url', type=str, required=True)
oem_parser.add_argument('maxwidth', type=int, default=300)
oem_parser.add_argument('maxheight', type=int, default=200)
oem_parser.add_argument('format', type=str)


class MongoConnection():
    def connect():
        client = MongoClient()
        db = client.emonitor
        renderJobs = db.renderJobs
        return renderJobs

class JobListApi(Resource):
    def post(self):
        renderJobs = MongoConnection.connect()
        data = jobModel()
        data['name'] = request.form['name']
        data['status'] = request.form['status']
        token_simple = random.randint(0, 999999)
        data['token_simple'] = token_simple
        iid=renderJobs.insert(data.safe())

        return {'uuid':str(iid), 'token_simple':token_simple}, 200

class JobApi(Resource):
    def get(self, job_id=None):
        renderJobs = MongoConnection.connect()
        data_client=renderJobs.find_one({'_id':ObjectId(job_id)})

        emon_data = jobModel()
        emon_data['name'] = data_client['name']
        emon_data['status'] = data_client['status']
        emon_data['engine'] = data_client['engine']
        emon_data['freestyle'] = data_client['freestyle']
        emon_data['compositor'] = data_client['compositor']
        emon_data['sequencer'] = data_client['sequencer']
        emon_data['frame_start'] = data_client['frame_start']
        emon_data['frame_end'] = data_client['frame_end']
        emon_data['frame_current'] = data_client['frame_current']

        return emon_data.safe(), 200

    def allowed_file(self, filename):
        return '.' in filename and \
            filename.rsplit('.', 1)[1] in ['png']

    def patch(self, job_id=None):
        # from werkzeug import secure_filename

        renderJobs = MongoConnection.connect()
        emon_data = jobModel()
        emon_data['status'] = str(request.form['status'])
        emon_data['engine'] = str(request.form['engine'])
        emon_data['freestyle'] = request.form['freestyle']=="True"
        emon_data['compositor'] = request.form['compositor']=="True"
        emon_data['sequencer'] = request.form['sequencer']=="True"
        emon_data['frame_start'] = int(request.form['frame_start'])
        emon_data['frame_end'] = int(request.form['frame_end'])
        if 'frame_current' in request.form:
            emon_data['frame_current'] = int(request.form['frame_current'])

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

        key = {'_id': ObjectId(job_id),
            'token_simple': int(request.form['token_simple'])}
        renderJobs.update(key, {'$set':emon_data.safe()})

class JobThumbnailApi(Resource):
    def get(self, job_id, frame):
        """Given a job_id returns the output file
        """
        jobpath = os.path.join(app.config['THUMBNAIL_STORAGE'], job_id)
        imagename = "{0}_{1}.png".format(job_id, frame)
        return send_from_directory(jobpath, imagename)


class JobOembedApi(Resource):
    def get(self):
        """oEmbed support"""
        args = oem_parser.parse_args()
        uuid = args['url'].split('/')[-1]
        html = '<iframe style="margin:0px; padding:0px; border:0px;"\
src="http://monitor.eibriel.com/movie/{0}">\
</iframe>'.format(uuid)
        params = {
            'type': 'video',
            'version': '1.0',
            'title': 'eMonitor',
            'provider_name': 'eMonitor',
            'provider_url': 'http://monitor.eibriel.com',
            'html': html,
            'width': args['maxwidth'],
            'height': args['maxheight'],
        }

        return params

# Models

class cyclesModel(Document):
    structure = {
        'samples': int,
    }

    validators = {
        'samples': Document.min_val(0),
    }


class jobModel(Document):
    structure = {
        'name': str,
        'token_simple': int,
        'engine': str,
        'freestyle': bool,
        'compositor': bool,
        'sequencer': bool,
        'frame_start': int,
        'frame_end': int,
        'frame_current': int,
        'status': str,
        'data': Document,
    }

    validators = {
        'name': Document.max_length(128),
        'token_simple': Document.min_val(0),
        'engine': Document.in_list(['CYCLES', 'BLENDER_RENDER']),
        'freestyle': Document.any_val(),
        'compositor': Document.any_val(),
        'sequencer': Document.any_val(),
        'frame_start': Document.any_val(),
        'frame_end': Document.any_val(),
        'frame_current': Document.any_val(),
        'status': Document.in_list([
            'JOB_START',
            'RENDER_START',
            'RENDER_END',
            'JOB_CANCELLED',
            'RENDER_COMPLETE',
            ]),
        'data': Document.if_type_in([cyclesModel,]),
    }

    use_dot_notation = True

    def __repr__(self):
        return '<Job {0}>'.format(self.name)
