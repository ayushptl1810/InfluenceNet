from flask import Flask

app = Flask(__name__, instance_path='/tmp')

import config
import models
import routes
import api

app.instance_path = '/tmp'

if __name__ == '__main__':
    app.run()