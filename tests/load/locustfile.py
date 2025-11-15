"""Load testing configuration with Locust."""

from locust import HttpUser, task, between
import random


class APIUser(HttpUser):
    """Simulates API user behavior."""

    wait_time = between(1, 3)

    @task(3)
    def get_health(self):
        """Health check endpoint."""
        self.client.get("/health")

    @task(2)
    def get_user_profile(self):
        """Get user profile."""
        user_id = random.randint(1, 100)
        self.client.get(f"/api/users/{user_id}")

    @task(2)
    def get_player_stats(self):
        """Get player statistics."""
        player_id = f"player_{random.randint(1, 50)}"
        self.client.get(f"/api/players/{player_id}/stats")

    @task(1)
    def get_subscriptions(self):
        """Get user subscriptions."""
        user_id = random.randint(1, 100)
        self.client.get(f"/api/subscriptions/user/{user_id}")

    @task(1)
    def create_analysis(self):
        """Create analysis request."""
        self.client.post(
            "/api/analysis",
            json={
                "player_id": f"player_{random.randint(1, 50)}",
                "analysis_type": random.choice(["stats", "performance", "trends"]),
            },
        )


class AdminUser(HttpUser):
    """Simulates admin user behavior."""

    wait_time = between(2, 5)

    @task(1)
    def get_metrics(self):
        """Get application metrics."""
        self.client.get("/metrics")

    @task(1)
    def get_system_stats(self):
        """Get system statistics."""
        self.client.get("/api/admin/stats")
