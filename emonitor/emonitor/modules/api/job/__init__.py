import os
import json
import random
import requests

from pymongo import MongoClient
from bson import ObjectId
from flask import request
from flask import send_from_directory
from flask import make_response
from flask.ext.restful import Resource
from flask.ext.restful import reqparse

from requests.exceptions import ConnectionError
from requests.exceptions import Timeout

import time
from datetime import datetime
from datetime import timedelta

from emonitor import app
from emonitor.modules.eMongo import Document


oem_parser = reqparse.RequestParser()
oem_parser.add_argument('url', type=str, required=True)
oem_parser.add_argument('maxwidth', type=int, default=300)
oem_parser.add_argument('maxheight', type=int, default=200)
oem_parser.add_argument('format', type=str)

bit_parser = reqparse.RequestParser()
bit_parser.add_argument('transaction_hash', type=str, required=True)
bit_parser.add_argument('input_transaction_hash', type=str, required=True)
bit_parser.add_argument('input_address', type=str, required=True)
bit_parser.add_argument('address', type=str, required=True)
bit_parser.add_argument('value', type=int, required=True)
bit_parser.add_argument('confirmations', type=int, required=True)


class MongoConnection():
    def connect():
        client = MongoClient()
        db = client.emonitor
        renderJobs = db.renderJobs
        return renderJobs

class JobListApi(Resource):
    def post(self):
        dnow = datetime.now()
        renderJobs = MongoConnection.connect()
        data = jobModel()
        data['name'] = request.form['name']
        data['status'] = request.form['status']
        data['time_init'] = dnow
        data['last_access'] = dnow
        token_simple = random.randint(0, 999999)
        data['token_simple'] = token_simple
        iid=renderJobs.insert(data.safe())

        return {'uuid':str(iid), 'token_simple':token_simple}, 200

class JobApi(Resource):
    def get(self, job_id=None):
        if not ObjectId.is_valid(job_id):
            return '', 404
        renderJobs = MongoConnection.connect()
        data_client=renderJobs.find_one({'_id':ObjectId(job_id)})

        data = {}
        data['name'] = data_client['name']
        data['status'] = data_client['status']
        data['engine'] = data_client['engine']
        data['freestyle'] = data_client['freestyle']
        data['compositor'] = data_client['compositor']
        data['sequencer'] = data_client['sequencer']
        data['frame_start'] = data_client['frame_start']
        data['frame_end'] = data_client['frame_end']
        data['frame_current'] = data_client['frame_current']
        data['time_init'] = time.mktime(data_client['time_init'].timetuple())

        engine_data = data_client['engine_data']

        if data_client['engine']=='CYCLES':
            data['use_square_samples'] = engine_data['use_square_samples']
            data['feature_set'] = engine_data['feature_set']
            data['shading_system'] = engine_data['shading_system']
            data['progressive'] = engine_data['progressive']
            if engine_data['progressive'] == 'PATH':
                data['samples'] = engine_data['samples']
            else:
                data['aa_samples'] = engine_data['aa_samples']
                data['diffuse_samples'] = engine_data['diffuse_samples']
                data['glossy_samples'] = engine_data['glossy_samples']
                data['transmission_samples'] = engine_data['transmission_samples']
                data['ao_samples'] = engine_data['ao_samples']
                data['mesh_light_samples'] = engine_data['mesh_light_samples']
                data['subsurface_samples'] = engine_data['subsurface_samples']
                data['volume_samples'] = engine_data['volume_samples']
                data['sample_all_lights_direct'] = engine_data['sample_all_lights_direct']
                data['sample_all_lights_indirect'] = engine_data['sample_all_lights_indirect']
            data['volume_step_size'] = engine_data['volume_step_size']
            data['volume_max_steps'] = engine_data['volume_max_steps']
            data['transparent_max_bounces'] = engine_data['transparent_max_bounces']
            data['transparent_min_bounces'] = engine_data['transparent_min_bounces']
            data['max_bounces'] = engine_data['max_bounces']
            data['min_bounces'] = engine_data['min_bounces']
            data['diffuse_bounces'] = engine_data['diffuse_bounces']
            data['glossy_bounces'] = engine_data['glossy_bounces']
            data['transmission_bounces'] = engine_data['transmission_bounces']
            data['volume_bounces'] = engine_data['volume_bounces']
            data['use_transparent_shadows'] = engine_data['use_transparent_shadows']
            data['caustics_reflective'] = engine_data['caustics_reflective']
            data['caustics_refractive'] = engine_data['caustics_refractive']
            data['blur_glossy'] = engine_data['blur_glossy']
        elif data_client['engine']=='BLENDER_RENDER':
            data['use_ambient_occlusion'] = engine_data['use_ambient_occlusion']

        emon_data = jobModel()
        emon_data['last_access'] = datetime.now()
        key = {'_id': ObjectId(job_id)}
        renderJobs.update(key, {'$set':emon_data.safe()})

        return data, 200

    def allowed_file(self, filename):
        return '.' in filename and \
            filename.rsplit('.', 1)[1] in ['png']

    def patch(self, job_id=None):
        if not ObjectId.is_valid(job_id):
            return '', 404

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

        engine_data = json.loads(request.form['engine_data'])

        if request.form['engine'] == 'CYCLES':
            cycles_data = cyclesModel()
            cycles_data['use_square_samples'] = engine_data['use_square_samples']
            cycles_data['feature_set'] = engine_data['feature_set']
            cycles_data['shading_system'] = engine_data['shading_system']
            cycles_data['progressive'] = engine_data['progressive']
            if engine_data['progressive'] == 'PATH':
                cycles_data['samples'] = engine_data['samples']
            else:
                cycles_data['aa_samples'] = engine_data['aa_samples']
                cycles_data['diffuse_samples'] = engine_data['diffuse_samples']
                cycles_data['glossy_samples'] = engine_data['glossy_samples']
                cycles_data['transmission_samples'] = engine_data['transmission_samples']
                cycles_data['ao_samples'] = engine_data['ao_samples']
                cycles_data['mesh_light_samples'] = engine_data['mesh_light_samples']
                cycles_data['subsurface_samples'] = engine_data['subsurface_samples']
                cycles_data['volume_samples'] = engine_data['volume_samples']
                cycles_data['sample_all_lights_direct'] = engine_data['sample_all_lights_direct']
                cycles_data['sample_all_lights_indirect'] = engine_data['sample_all_lights_indirect']
            cycles_data['volume_step_size'] = engine_data['volume_step_size']
            cycles_data['volume_max_steps'] = engine_data['volume_max_steps']
            cycles_data['transparent_max_bounces'] = engine_data['transparent_max_bounces']
            cycles_data['transparent_min_bounces'] = engine_data['transparent_min_bounces']
            cycles_data['max_bounces'] = engine_data['max_bounces']
            cycles_data['min_bounces'] = engine_data['min_bounces']
            cycles_data['diffuse_bounces'] = engine_data['diffuse_bounces']
            cycles_data['glossy_bounces'] = engine_data['glossy_bounces']
            cycles_data['transmission_bounces'] = engine_data['transmission_bounces']
            cycles_data['volume_bounces'] = engine_data['volume_bounces']
            cycles_data['use_transparent_shadows'] = engine_data['use_transparent_shadows']
            cycles_data['caustics_reflective'] = engine_data['caustics_reflective']
            cycles_data['caustics_refractive'] = engine_data['caustics_refractive']
            cycles_data['blur_glossy'] = engine_data['blur_glossy']
            emon_data['engine_data'] = cycles_data
        elif request.form['engine'] == 'BLENDER_RENDER':
            bi_data = blenderInternalModel()
            bi_data['use_ambient_occlusion'] = engine_data['use_ambient_occlusion']
            emon_data['engine_data'] = bi_data

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
        if not ObjectId.is_valid(job_id):
            return '', 404
        renderJobs = MongoConnection.connect()
        emon_data = jobModel()
        emon_data['last_access'] = datetime.now()
        key = {'_id': ObjectId(job_id)}
        renderJobs.update(key, {'$set':emon_data.safe()})

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

# TODO move bitcoin Code
class BitcoinApi(Resource):
    def get(self):
        """Bitcoin support"""
        client = MongoClient()
        db = client.emonitor
        bitcoinDonations = db.bitcoinDonations
        data = bitcoinDonationModel()
        secret= random.randint(0, 999999)
        data['name'] = "Test"
        data['email'] = "test@test.com"
        data['timestamp'] = datetime.now()
        data['secret'] = secret
        data['status'] = 0
        data['input_address'] = ""
        data['transaction_hash'] = ""
        data['input_transaction_hash'] = ""
        data['value'] = 0
        bid=bitcoinDonations.insert(data.safe())

        faker = {
            #"callback_url":"http://monitor.eibriel.com/api/bitcoin/callback/54f515737ff6a90c47bdf5b4/796068",
            "input_address":"19Ft211qH3R5PywgoEPqJmTWCyTBYUiufu",
            #"destination":"1MD8wCtnx5zqGvkY1VYPNqckAyTWDhXKzY",
            #"fee_percent":0
            'transaction_id':str(bid),
        }

        return faker, 200

        apiurl =  "https://blockchain.info/es/api/receive"
        # bitcoin:1MD8wCtnx5zqGvkY1VYPNqckAyTWDhXKzY?label=Amorzorzores&amount=0.00001
        address = "1MD8wCtnx5zqGvkY1VYPNqckAyTWDhXKzY"
        callback = "http://monitor.eibriel.com/api/bitcoin/callback/{0}/{1}".format(bid, secret)
        params = {
            "method": "create",
            "address": address,
            "callback": callback,
        }
        try:
            r = requests.get(apiurl, params=params)
        except ConnectionError:
            return 'BlockChain Connection Error', 500
        except Timeout:
            return 'BlockChain Timeout', 500

        bc = request.get_json(force=False, silent=False)
        if not bc:
            return "No Json", 500
        try:
            rjson = bc.json()
        except:
            return "Error on Json", 500
        if not 'input_address' in rjson:
            return "No input_address", 500
        input_address = rjson['input_address']

        r = {
            'input_address':input_address,
            'transaction_id':str(did),
        }

        return r, 200


class BitcoinCheckApi(Resource):
    def get(self, bid):
        """Check for confirmation"""
        if not ObjectId.is_valid(bid):
            return '', 200
        client = MongoClient()
        db = client.emonitor
        bitcoinDonations = db.bitcoinDonations
        key = {'_id': ObjectId(bid)}
        data = bitcoinDonations.find_one(key)

        return {'status':data['status']}, 200


class BitcoinCallbackApi(Resource):
    def get(self, bid, secret):
        """Bitcoin Callback"""
        args = bit_parser.parse_args()
        r = ""
        if not ObjectId.is_valid(bid):
            resp = make_response('', 200)
            resp.mimetype = 'text/plain'
            return resp
        client = MongoClient()
        db = client.emonitor
        bitcoinDonations = db.bitcoinDonations
        data = bitcoinDonationModel()
        if args['confirmations']>0:
            data['status'] = 1
        if args['confirmations']>6:
            data['status'] = 2
            r = "*ok*"
        data['input_address'] = args['input_address']
        data['transaction_hash'] = args['transaction_hash']
        data['input_transaction_hash'] = args['input_transaction_hash']
        data['value'] = args['value']
        key = {'_id': ObjectId(bid),
               'secret': secret,
               'destination_address': args['address']}
        bitcoinDonations.update(key, {'$set':data.safe()})
        resp = make_response(r, 200)
        resp.mimetype = 'text/plain'
        return resp


# Models

class bitcoinDonationModel(Document):
    structure = {
        'name': str,
        'email': str,
        'timestamp': datetime,
        'secret': int,
        'status': int,
        'input_address': str,
        'destination_address': str,
        'transaction_hash': str,
        'input_transaction_hash': str,
        'value': int,
    }

    validators = {
        'name': Document.any_val(),
        'email': Document.any_val(),
        'timestamp': Document.any_val(),
        'secret': Document.any_val(),
        'status': Document.min_max_val(0,2),
        'input_address': Document.any_val(),
        'destination_address': Document.any_val(),
        'transaction_hash': Document.any_val(),
        'input_transaction_hash': Document.any_val(),
        'value': Document.any_val(),
    }

    def __repr__(self):
        return '<BitDonation {0}>'.format(self.name)


class blenderInternalModel(Document):
    structure = {
        'use_ambient_occlusion': bool,
    }

    validators = {
        'use_ambient_occlusion': Document.any_val(),
    }

    def __repr__(self):
        return '<BlenderInternal {0}>'.format(self.name)

class cyclesModel(Document):
    structure = {
        'use_square_samples': bool,
        'feature_set': str,
        'shading_system': bool,
        'progressive': str,
        'samples': int,
        'aa_samples': int,
        'diffuse_samples': int,
        'glossy_samples': int,
        'transmission_samples': int,
        'ao_samples': int,
        'mesh_light_samples': int,
        'subsurface_samples': int,
        'volume_samples': int,
        'sample_all_lights_direct': bool,
        'sample_all_lights_indirect': bool,
        'volume_step_size': float,
        'volume_max_steps': int,
        'transparent_max_bounces': int,
        'transparent_min_bounces': int,
        'max_bounces': int,
        'min_bounces': int,
        'diffuse_bounces': int,
        'glossy_bounces': int,
        'transmission_bounces': int,
        'volume_bounces': int,
        'use_transparent_shadows': bool,
        'caustics_reflective': bool,
        'caustics_refractive': bool,
        'blur_glossy': float,
    }

    validators = {
        'use_square_samples': Document.any_val(),
        'feature_set': Document.in_list(['SUPPORTED', 'EXPERIMENTAL']),
        'shading_system': Document.any_val(),
        'progressive': Document.in_list(['PATH', 'BRANCHED_PATH']),
        'samples': Document.min_val(0),
        'aa_samples': Document.min_val(0),
        'diffuse_samples': Document.min_val(0),
        'glossy_samples': Document.min_val(0),
        'transmission_samples': Document.min_val(0),
        'ao_samples': Document.min_val(0),
        'mesh_light_samples': Document.min_val(0),
        'subsurface_samples': Document.min_val(0),
        'volume_samples': Document.min_val(0),
        'sample_all_lights_direct': Document.any_val(),
        'sample_all_lights_indirect': Document.any_val(),
        'volume_step_size': Document.min_val(0),
        'volume_max_steps': Document.min_val(2),
        'transparent_max_bounces': Document.min_val(0),
        'transparent_min_bounces': Document.min_val(0),
        'max_bounces': Document.min_val(0),
        'min_bounces': Document.min_val(0),
        'diffuse_bounces': Document.min_val(0),
        'glossy_bounces': Document.min_val(0),
        'transmission_bounces': Document.min_val(0),
        'volume_bounces': Document.min_val(0),
        'use_transparent_shadows': Document.any_val(),
        'caustics_reflective': Document.any_val(),
        'caustics_refractive': Document.any_val(),
        'blur_glossy': Document.min_val(0),
    }

    def __repr__(self):
        return '<Cycles {0}>'.format(self.name)


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
        'time_init': datetime,
        'last_access': datetime,
        'engine_data': None,
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
        'time_init': Document.any_val(),
        'last_access': Document.any_val(),
        'engine_data': Document.if_type_in([cyclesModel, blenderInternalModel]),
    }

    def __repr__(self):
        return '<Job {0}>'.format(self.name)
