from flask import Flask
from flask.ext.restful import Api

app = Flask(__name__)

api = Api(app)

app.secret_key = 'A0Zr98j/3yX oakw8sd76as214/("/adsa*-+2123f.,;..saocww2.0]LWX/,?RT'

# from modules.api import RenderApi
# from modules.api import RenderListApi
# api.add_resource(RenderListApi, '/api')
# api.add_resource(RenderApi, '/api/<render_uuid>')

from emonitor.modules.api.job import JobListApi
from emonitor.modules.api.job import JobApi
api.add_resource(JobListApi, '/api/job')
api.add_resource(JobApi, '/api/job/<job_id>')

from emonitor.modules.api.user import UserListApi
from emonitor.modules.api.user import UserApi
from emonitor.modules.api.user import UserLogoutApi
api.add_resource(UserListApi, '/api/user')
api.add_resource(UserApi, '/api/user/<job_id>')
api.add_resource(UserLogoutApi, '/api/user/logout')

from emonitor.modules.main import main
app.register_blueprint(main)
