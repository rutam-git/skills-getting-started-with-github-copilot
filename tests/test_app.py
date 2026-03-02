import copy
import pytest
from fastapi.testclient import TestClient

from src import app as app_module
from src.app import app, activities

client = TestClient(app)

# keep a pristine copy for resetting between tests
def _initial_activities():
    return copy.deepcopy(activities)

@pytest.fixture(autouse=True)
def reset_activities():
    # clear and restore the global activities dict before each test
    activities.clear()
    activities.update(_initial_activities())
    yield


def test_root_redirect():
    response = client.get("/", allow_redirects=False)
    assert response.status_code == 307 or response.status_code == 302
    assert response.headers["location"].endswith("/static/index.html")


def test_get_activities():
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    # expect at least one known key
    assert "Chess Club" in data


def test_signup_success():
    response = client.post("/activities/Chess%20Club/signup?email=test@example.com")
    assert response.status_code == 200
    assert "Signed up test@example.com for Chess Club" in response.json()["message"]
    assert "test@example.com" in activities["Chess Club"]["participants"]


def test_signup_duplicate():
    email = activities["Chess Club"]["participants"][0]
    response = client.post(f"/activities/Chess%20Club/signup?email={email}")
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"]


def test_signup_not_found():
    response = client.post("/activities/Nonexistent/signup?email=foo@bar.com")
    assert response.status_code == 404


def test_signup_full():
    # fill activity to capacity
    act = activities["Chess Club"]
    act["participants"] = [f"u{i}@x.com" for i in range(act["max_participants"])]
    response = client.post("/activities/Chess%20Club/signup?email=new@user.com")
    assert response.status_code == 400
    assert "Activity is full" in response.json()["detail"]


def test_unregister_success():
    email = activities["Chess Club"]["participants"][0]
    response = client.delete(f"/activities/Chess%20Club/participants?email={email}")
    assert response.status_code == 200
    assert email not in activities["Chess Club"]["participants"]


def test_unregister_not_found_activity():
    response = client.delete("/activities/Foo/participants?email=ax@bz.com")
    assert response.status_code == 404


def test_unregister_not_subscribed():
    response = client.delete("/activities/Chess%20Club/participants?email=nobody@here.com")
    assert response.status_code == 404
