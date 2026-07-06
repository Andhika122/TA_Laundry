import os
import pytest

os.environ.setdefault('FLASK_ENV', 'testing')

import app as app_module


@pytest.fixture()
def app():
    application = app_module.create_app('testing')
    with application.app_context():
        from app import db

        db.drop_all()
        db.create_all()

    yield application

    with application.app_context():
        from app import db

        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()
