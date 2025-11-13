#!/usr/bin/env python3
"""Test Faceit API and AI"""
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from src.server.integrations.faceit_client import FaceitAPIClient
from src.server.services.ai_service import AIService

async def test_faceit():
    """Test Faceit API"""
    print("🔍 Testing Faceit API...")
    client = FaceitAPIClient()
    
    # Test player lookup
    player = await client.get_player_by_nickname("s1mple")
    if player:
        print(f"✅ Found player: {player.get('nickname')}")
        return player.get('player_id')
    else:
        print("❌ Player not found")
        return None

async def test_ai():
    """Test AI service"""
    print("🤖 Testing AI service...")
    ai = AIService()
    
    test_stats = {"kd_ratio": 1.5, "win_rate": 65}
    analysis = await ai.analyze_player_with_ai("test", test_stats, [])
    
    if analysis:
        print("✅ AI analysis working")
        print(f"Analysis: {analysis[:100]}...")
    else:
        print("❌ AI analysis failed")

async def main():
    """Run tests"""
    print("🚀 Starting integration tests...\n")
    
    # Test Faceit
    player_id = await test_faceit()
    
    # Test AI
    await test_ai()
    
    print("\n✅ Tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
