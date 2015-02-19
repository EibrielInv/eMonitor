import os
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from bson import ObjectId
from flask import request
from flask import session
from flask.ext.restful import Resource

# from emonitor.modules.emonitor_data import emonitor_data


class MongoConnection():
    def connect():
        client = MongoClient()
        db = client.emonitor
        renderUsers = db.renderUsers
        renderUsers.create_index("username", name="unique_username", unique=True)
        return renderUsers


class UserLogoutApi(Resource):
    def get(self):
        session.pop('username', None)


class UserListApi(Resource):
    def post(self):
        if 'username' in session:
            return {'rmsg':'Already loged in'}, 500

        renderUsers = MongoConnection.connect()

        # renderUsers.find_one({'username':})

        user_data = {
            'username':request.form['username'],
            'email':request.form['email'],
            'pass':request.form['pass'],
        }

        uid = None
        try:
            uid=renderUsers.insert(user_data)
        except DuplicateKeyError:
            return {'rmsg':'Duplicate Username'}, 500

        if uid:
            session['username'] =  user_data['username']
            return {'uuid':str(uid)}, 200
        else:
            return {'rmsg':'Database error'}, 500

    def get(self):
        renderUsers = MongoConnection.connect()
        data_user = None
        username = request.args.get('username', 0, type=str)
        pass_ = request.args.get('pass', 0, type=str)
        if 'username' in session:
            data_user=renderUsers.find_one({'username':session['username']})
        elif username and pass_:
            data_user=renderUsers.find_one({'username':username, 'pass':pass_})
        if data_user:
            if not 'username' in session:
                session['username'] = username
            data_array = {
                'username':data_user['username'],
                'email':data_user['email'],
            }
            return data_array, 200

        return {'rmsg':'Auth error'}, 500

class UserApi(Resource):
    def get(self, user_name=None):
        renderUsers = MongoConnection.connect()

        if 'username' in session:
            if session['username']!=user_name:
                return {'rmsg':'Auth Error'}, 500
            data_user=renderUsers.find_one({'username':ObjectId(session['username'])})

        data_array = {
            'username':data_user['username'],
            'email':data_username['email'],
        }

        return data_array, 200

    def allowed_file(self, filename):
        return '.' in filename and \
            filename.rsplit('.', 1)[1] in ['png']

    def patch(self, job_id=None):
        from werkzeug import secure_filename

        renderJobs = MongoConnection.connect()
        emon_data = emonitor_data()
        emon_data.status = request.form['status']
        emon_data.engine = request.form['engine']
        emon_data.freestyle = request.form['freestyle']
        emon_data.compositor = request.form['compositor']
        emon_data.sequencer = request.form['sequencer']
        emon_data.frame_start = request.form['frame_start']
        emon_data.frame_end = request.form['frame_end']
        emon_data.frame_current = request.form['frame_current']

        try:
            file = request.files.get('images')
            if file and self.allowed_file(file.filename):
                filename = "{0}.png".format(job_id)
                file.save(os.path.join('/home/gabriel/dev/emonitor/eMonitor/emonitor/emonitor/static/thumbnails/', filename))
        except:
            print ("Error reading file")

        key = {'_id':ObjectId(job_id)}
        renderJobs.update(key, {'$set':emon_data.array_update()})
