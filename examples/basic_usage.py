"""
Basic usage example for Faceit AI Bot API
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000")
FACEIT_API_KEY = os.getenv("FACEIT_API_KEY")


def get_player_stats(nickname: str):
    """Get player statistics"""
    response = requests.get(
        f"{API_URL}/api/players/{nickname}/stats",
        headers={"X-API-Key": FACEIT_API_KEY}
    )
    response.raise_for_status()
    return response.json()


def analyze_player(nickname: str):
    """Analyze player"""
    response = requests.post(
        f"{API_URL}/api/players/{nickname}/analyze",
        headers={"X-API-Key": FACEIT_API_KEY}
    )
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    # Usage example
    nickname = "s1mple"
    
    print(f"Getting stats for {nickname}...")
    stats = get_player_stats(nickname)
    print(f"Level: {stats.get('level')}")
    print(f"ELO: {stats.get('elo')}")
    
    print(f"\nAnalyzing player {nickname}...")
    analysis = analyze_player(nickname)
    print(f"Recommendation: {analysis.get('recommendation')}")
