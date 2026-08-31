"""
Test suite for the Mergington High School Activities API.
Tests cover all endpoints and error cases.
"""

import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that GET /activities returns all available activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        # Should have at least 3 activities
        assert len(data) >= 3
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data

    def test_get_activities_returns_correct_structure(self, client, reset_activities):
        """Test that activity data has correct structure."""
        response = client.get("/activities")
        data = response.json()
        
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)

    def test_get_activities_includes_participants(self, client, reset_activities):
        """Test that activities include correct participant list."""
        response = client.get("/activities")
        data = response.json()
        
        chess_club = data["Chess Club"]
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_success(self, client, reset_activities):
        """Test successful signup for an activity."""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]

    def test_signup_adds_participant(self, client, reset_activities):
        """Test that signup adds the student to participants."""
        # Sign up
        client.post("/activities/Chess Club/signup?email=test@mergington.edu")
        
        # Verify participant was added
        response = client.get("/activities")
        data = response.json()
        assert "test@mergington.edu" in data["Chess Club"]["participants"]

    def test_signup_increases_participant_count(self, client, reset_activities):
        """Test that signup increases the participant count."""
        # Get initial count
        response = client.get("/activities")
        initial_count = len(response.json()["Chess Club"]["participants"])
        
        # Sign up
        client.post("/activities/Chess Club/signup?email=test@mergington.edu")
        
        # Get new count
        response = client.get("/activities")
        new_count = len(response.json()["Chess Club"]["participants"])
        
        assert new_count == initial_count + 1

    def test_signup_activity_not_found(self, client, reset_activities):
        """Test signup returns 404 when activity doesn't exist."""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_duplicate_student(self, client, reset_activities):
        """Test that duplicate signup returns 400 error."""
        # First signup succeeds
        response = client.post(
            "/activities/Chess Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
        
        # Second signup with same email should fail
        response = client.post(
            "/activities/Chess Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_existing_participant_not_duplicated(self, client, reset_activities):
        """Test that existing participants cannot signup again."""
        # Try to signup with existing participant
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_special_characters_in_email(self, client, reset_activities):
        """Test signup with email containing special characters."""
        response = client.post(
            "/activities/Chess Club/signup?email=student%2Btest@mergington.edu"
        )
        assert response.status_code == 200
        
        # Verify participant was added
        response = client.get("/activities")
        data = response.json()
        assert "student+test@mergington.edu" in data["Chess Club"]["participants"]


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/participant/{email} endpoint."""

    def test_unregister_success(self, client, reset_activities):
        """Test successful unregistration from an activity."""
        response = client.delete(
            "/activities/Chess Club/participant/michael@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]

    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregister removes student from participants."""
        # Verify participant exists
        response = client.get("/activities")
        assert "michael@mergington.edu" in response.json()["Chess Club"]["participants"]
        
        # Unregister
        client.delete("/activities/Chess Club/participant/michael@mergington.edu")
        
        # Verify participant was removed
        response = client.get("/activities")
        assert "michael@mergington.edu" not in response.json()["Chess Club"]["participants"]

    def test_unregister_decreases_participant_count(self, client, reset_activities):
        """Test that unregister decreases the participant count."""
        # Get initial count
        response = client.get("/activities")
        initial_count = len(response.json()["Chess Club"]["participants"])
        
        # Unregister
        client.delete("/activities/Chess Club/participant/michael@mergington.edu")
        
        # Get new count
        response = client.get("/activities")
        new_count = len(response.json()["Chess Club"]["participants"])
        
        assert new_count == initial_count - 1

    def test_unregister_activity_not_found(self, client, reset_activities):
        """Test unregister returns 404 when activity doesn't exist."""
        response = client.delete(
            "/activities/Nonexistent Activity/participant/test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_student_not_registered(self, client, reset_activities):
        """Test unregister returns 400 when student is not registered."""
        response = client.delete(
            "/activities/Chess Club/participant/notregistered@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"]

    def test_unregister_special_characters_in_email(self, client, reset_activities):
        """Test unregister with email containing special characters."""
        # First signup with special character email
        client.post("/activities/Chess Club/signup?email=test%2Bspecial@mergington.edu")
        
        # Then unregister
        response = client.delete(
            "/activities/Chess Club/participant/test%2Bspecial@mergington.edu"
        )
        assert response.status_code == 200
        
        # Verify participant was removed
        response = client.get("/activities")
        assert "test+special@mergington.edu" not in response.json()["Chess Club"]["participants"]


class TestIntegrationScenarios:
    """Integration tests for complete workflows."""

    def test_signup_then_unregister_workflow(self, client, reset_activities):
        """Test complete workflow: signup then unregister."""
        email = "integration@mergington.edu"
        activity = "Programming Class"
        
        # Signup
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
        
        # Verify in participants
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]
        
        # Unregister
        response = client.delete(f"/activities/{activity}/participant/{email}")
        assert response.status_code == 200
        
        # Verify removed from participants
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]

    def test_multiple_students_signup_same_activity(self, client, reset_activities):
        """Test multiple students can sign up for the same activity."""
        activity = "Drama Club"
        students = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu"
        ]
        
        # Sign up multiple students
        for email in students:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            assert response.status_code == 200
        
        # Verify all students are in participants
        response = client.get("/activities")
        participants = response.json()[activity]["participants"]
        for email in students:
            assert email in participants

    def test_signup_unregister_signup_workflow(self, client, reset_activities):
        """Test student can unregister and then re-signup."""
        email = "flexible@mergington.edu"
        activity = "Tennis Club"
        
        # First signup
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
        
        # Unregister
        response = client.delete(f"/activities/{activity}/participant/{email}")
        assert response.status_code == 200
        
        # Re-signup (should succeed now)
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
        
        # Verify in participants
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]
