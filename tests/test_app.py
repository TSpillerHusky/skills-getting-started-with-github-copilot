"""
Tests for the Mergington High School API
"""

import sys
from pathlib import Path

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


class TestActivitiesEndpoint:
    """Test the /activities endpoint"""

    def test_get_activities_returns_200(self):
        """Test that GET /activities returns status code 200"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_dict(self):
        """Test that GET /activities returns a dictionary"""
        response = client.get("/activities")
        data = response.json()
        assert isinstance(data, dict)

    def test_get_activities_has_expected_keys(self):
        """Test that returned activities have expected structure"""
        response = client.get("/activities")
        data = response.json()
        
        # Check that we have activities
        assert len(data) > 0
        
        # Check that each activity has required fields
        for activity_name, activity_details in data.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)

    def test_get_activities_has_chess_club(self):
        """Test that Chess Club is in the activities"""
        response = client.get("/activities")
        data = response.json()
        assert "Chess Club" in data


class TestSignupEndpoint:
    """Test the /activities/{activity_name}/signup endpoint"""

    def test_signup_for_activity_success(self):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Basketball Team/signup?email=test@example.com"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "test@example.com" in data["message"]

    def test_signup_adds_participant(self):
        """Test that signup actually adds the participant"""
        email = "swimmer@mergington.edu"
        
        # Get initial participants count
        response = client.get("/activities")
        initial_count = len(response.json()["Swimming Club"]["participants"])
        
        # Signup
        response = client.post(f"/activities/Swimming Club/signup?email={email}")
        assert response.status_code == 200
        
        # Verify participant was added
        response = client.get("/activities")
        final_count = len(response.json()["Swimming Club"]["participants"])
        assert final_count == initial_count + 1
        assert email in response.json()["Swimming Club"]["participants"]

    def test_signup_duplicate_fails(self):
        """Test that signing up twice fails"""
        email = "duplicatetest@mergington.edu"
        
        # First signup
        response = client.post(
            f"/activities/Art Studio/signup?email={email}"
        )
        assert response.status_code == 200
        
        # Second signup should fail
        response = client.post(
            f"/activities/Art Studio/signup?email={email}"
        )
        assert response.status_code == 400
        data = response.json()
        assert "Already signed up" in data["detail"]

    def test_signup_nonexistent_activity_fails(self):
        """Test that signing up for nonexistent activity fails"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=test@example.com"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]


class TestUnregisterEndpoint:
    """Test the /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self):
        """Test successful unregister from an activity"""
        email = "unregister-test@mergington.edu"
        activity = "Programming Class"
        
        # First, signup
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
        
        # Then unregister
        response = client.post(f"/activities/{activity}/unregister?email={email}")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Unregistered" in data["message"]

    def test_unregister_removes_participant(self):
        """Test that unregister actually removes the participant"""
        email = "remove-test@mergington.edu"
        activity = "Gym Class"
        
        # Signup
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Get count before unregister
        response = client.get("/activities")
        before_count = len(response.json()[activity]["participants"])
        assert email in response.json()[activity]["participants"]
        
        # Unregister
        response = client.post(f"/activities/{activity}/unregister?email={email}")
        assert response.status_code == 200
        
        # Verify participant was removed
        response = client.get("/activities")
        after_count = len(response.json()[activity]["participants"])
        assert after_count == before_count - 1
        assert email not in response.json()[activity]["participants"]

    def test_unregister_not_registered_fails(self):
        """Test that unregistering a non-registered user fails"""
        email = "never-registered@mergington.edu"
        response = client.post(
            f"/activities/Debate Team/unregister?email={email}"
        )
        assert response.status_code == 400
        data = response.json()
        assert "Not signed up" in data["detail"]

    def test_unregister_nonexistent_activity_fails(self):
        """Test that unregistering from nonexistent activity fails"""
        response = client.post(
            "/activities/Fake Activity/unregister?email=test@example.com"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]


class TestRootEndpoint:
    """Test the root endpoint"""

    def test_root_redirects_to_static(self):
        """Test that root endpoint redirects to static files"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"
