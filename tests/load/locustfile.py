"""Load testing with Locust"""

from locust import HttpUser, task, between
import json


class FaceitBotUser(HttpUser):
    """Simulates user behavior on Faceit AI Bot"""

    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks

    @task(3)  # 30% of requests
    def health_check(self):
        """Test health endpoint"""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")

    @task(2)  # 20% of requests
    def get_root(self):
        """Test root endpoint"""
        with self.client.get("/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Root endpoint failed: {response.status_code}")

    @task(1)  # 10% of requests
    def get_metrics(self):
        """Test metrics endpoint"""
        with self.client.get("/metrics", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Metrics endpoint failed: {response.status_code}")

    @task(4)  # 40% of requests - most common
    def simulate_player_analysis(self):
        """Simulate player analysis request"""
        # This would normally require authentication
        # For load testing, we'll just test the endpoint availability
        with self.client.get("/api/players/s1mple/stats", catch_response=True) as response:
            # We expect 401 or 404 since no auth, but endpoint should exist
            if response.status_code in [401, 404, 200]:
                response.success()
            else:
                response.failure(f"Player stats endpoint failed: {response.status_code}")


class AuthenticatedUser(FaceitBotUser):
    """User with authentication"""

    def on_start(self):
        """Login before starting tasks"""
        # This would normally authenticate the user
        # For demo purposes, we'll skip actual authentication
        pass

    @task(5)
    def get_user_profile(self):
        """Test authenticated user endpoints"""
        # This would require valid authentication
        with self.client.get("/api/auth/me", catch_response=True) as response:
            # Expect 401 since we're not actually authenticated
            if response.status_code == 401:
                response.success()
            else:
                response.failure(f"Auth endpoint unexpected response: {response.status_code}")

    @task(3)
    def create_analysis_request(self):
        """Test analysis creation"""
        payload = {"player_id": "test-player-123", "analysis_type": "quick"}

        with self.client.post("/api/analysis", json=payload, catch_response=True) as response:
            # Expect 401 since we're not authenticated
            if response.status_code == 401:
                response.success()
            else:
                response.failure(f"Analysis creation failed: {response.status_code}")
