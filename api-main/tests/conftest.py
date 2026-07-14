import os

import allure
import pytest
from core_service import create_app, db

os.environ["FLASK_CONFIG"] = "testing"


@pytest.fixture(scope="session")
@allure.title("Initializing a Test Flask Application (Session)")
def app():

    with allure.step("Creating Flask application for testing"):
        app = create_app(config_name="testing")
        app.config["REDIS_URL"] = os.environ.get(
            "REDIS_URL", "redis://localhost:6379/1"
        )

    with allure.step("Setting up the application context"):
        with app.app_context():
            yield app


@pytest.fixture(scope="session")
@allure.title("Creating a Test Client")
def client(app):
    with allure.step("Creating a test client for the Flask application"):
        return app.test_client()
