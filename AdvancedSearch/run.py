
'''
keyword=input("Enter your keyword")
els.get_keyword_offset(keyword)
print("\n",els.get_keyword_highlighted(keyword))
'''
from flask import Flask
from flask_restful import Api
from app import api_bp
from apscheduler.schedulers.background import BackgroundScheduler
from resources_common.ElasticSearchIndex import ElasticSearchIndex


def create_app(config_filename):
    app = Flask(__name__)
    app.config.from_object(config_filename)

    app.register_blueprint(api_bp, url_prefix='/search')
    #app.register_blueprint(routes.mod, url_prefix='/')

    return app

sched = BackgroundScheduler(daemon=True)
obj=ElasticSearchIndex()
sched.add_job(obj.postCustom, 'interval', seconds = 10)
sched.start()




if __name__ == "__main__":
    app = create_app('config')
    app.run(debug=True)