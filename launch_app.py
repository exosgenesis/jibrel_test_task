from api import app, GRABBER_WORKER
from grabber_worker import GrabberWorker
from waitress import serve

from init_db import init_db

if __name__ == '__main__':
    init_db()

    grabber_worker = GrabberWorker(app.config)
    app.config[GRABBER_WORKER] = grabber_worker

    if not (app.config['DEBUG'] and app.config['NO_BACKGROUND']):
        grabber_worker.start()

    # app.run(port=5002)
    serve(app, listen='*:5002')
    grabber_worker.stop()
