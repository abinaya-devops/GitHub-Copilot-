"""
Comprehensive tests for the Mergington High School Activity Registration API.
"""

import pytest
from fastapi.testclient import TestClient


class TestGetActivities:
    """Test suite for GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that GET /activities returns all registered activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        
        activities = response.json()
        assert isinstance(activities, dict)
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert "Gym Class" in activities

    def test_get_activities_includes_activity_details(self, client, reset_activities):
        """Test that each activity includes required fields."""
        response = client.get("/activities")
        activities = response.json()
        
        chess_club = activities["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club

    def test_get_activities_includes_participants(self, client, reset_activities):
        """Test that activities include list of current participants."""
        response = client.get("/activities")
        activities = response.json()
        
        chess_club = activities["Chess Club"]
        assert isinstance(chess_club["participants"], list)
        assert len(chess_club["participants"]) > 0
        assert "michael@mergington.edu" in chess_club["participants"]


class TestRootRedirect:
    """Test suite for GET / endpoint."""

    def test_root_redirects_to_static_index(self, client, reset_activities):
        """Test that GET / redirects to /static/index.html."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestSignupForActivity:
    """Test suite for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_success(self, client, reset_activities):
        """Test successful student signup for an activity."""
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]

    def test_signup_adds_participant_to_activity(self, client, reset_activities):
        """Test that signup actually adds the student to participants list."""
        email = "testuser@mergington.edu"
        client.post(
            "/activities/Programming%20Class/signup",
            params={"email": email}
        )
        
        # Verify participant was added
        response = client.get("/activities")
        activities = response.json()
        assert email in activities["Programming Class"]["participants"]

    def test_signup_activity_not_found(self, client, reset_activities):
        """Test signup fails when activity doesn't exist."""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_duplicate_student_rejected(self, client, reset_activities):
        """Test that a student cannot signup twice for the same activity."""
        email = "michael@mergington.edu"  # Already in Chess Club
        
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": email}
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_multiple_students_same_activity(self, client, reset_activities):
        """Test that multiple different students can signup for the same activity."""
        email1 = "student1@mergington.edu"
        email2 = "student2@mergington.edu"
        
        response1 = client.post(
            "/activities/Art%20Studio/signup",
            params={"email": email1}
        )
        response2 = client.post(
            "/activities/Art%20Studio/signup",
            params={"email": email2}
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify both are in participants
        response = client.get("/activities")
        activities = response.json()
        assert email1 in activities["Art Studio"]["participants"]
        assert email2 in activities["Art Studio"]["participants"]

    def test_signup_same_student_different_activities(self, client, reset_activities):
        """Test that a student can signup for multiple different activities."""
        email = "multisport@mergington.edu"
        
        response1 = client.post(
            "/activities/Soccer%20Team/signup",
            params={"email": email}
        )
        response2 = client.post(
            "/activities/Swimming%20Club/signup",
            params={"email": email}
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify student is in both activities
        response = client.get("/activities")
        activities = response.json()
        assert email in activities["Soccer Team"]["participants"]
        assert email in activities["Swimming Club"]["participants"]


class TestUnregisterFromActivity:
    """Test suite for POST /activities/{activity_name}/unregister endpoint."""

    def test_unregister_success(self, client, reset_activities):
        """Test successful student unregistration from an activity."""
        email = "michael@mergington.edu"
        response = client.post(
            "/activities/Chess%20Club/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]

    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregister actually removes the student from participants."""
        email = "michael@mergington.edu"
        client.post(
            "/activities/Chess%20Club/unregister",
            params={"email": email}
        )
        
        # Verify participant was removed
        response = client.get("/activities")
        activities = response.json()
        assert email not in activities["Chess Club"]["participants"]

    def test_unregister_activity_not_found(self, client, reset_activities):
        """Test unregister fails when activity doesn't exist."""
        response = client.post(
            "/activities/Nonexistent%20Activity/unregister",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_unregister_student_not_in_activity(self, client, reset_activities):
        """Test unregister fails when student is not signed up."""
        response = client.post(
            "/activities/Chess%20Club/unregister",
            params={"email": "notstudent@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "not signed up" in data["detail"]

    def test_unregister_then_signup_again(self, client, reset_activities):
        """Test that a student can sign up again after unregistering."""
        email = "michael@mergington.edu"
        
        # Unregister
        response1 = client.post(
            "/activities/Chess%20Club/unregister",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Sign up again
        response2 = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": email}
        )
        assert response2.status_code == 200
        
        # Verify student is back in activity
        response = client.get("/activities")
        activities = response.json()
        assert email in activities["Chess Club"]["participants"]

    def test_unregister_multiple_times_fails_second_time(self, client, reset_activities):
        """Test that unregistering twice for same activity fails on second attempt."""
        email = "michael@mergington.edu"
        
        response1 = client.post(
            "/activities/Chess%20Club/unregister",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Try to unregister again
        response2 = client.post(
            "/activities/Chess%20Club/unregister",
            params={"email": email}
        )
        assert response2.status_code == 404
