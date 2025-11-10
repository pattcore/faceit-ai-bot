/**
 * Example of fetching player data via API
 */

const API_URL = process.env.API_URL || 'http://localhost:8000';
const API_KEY = process.env.FACEIT_API_KEY;

async function getPlayerStats(nickname) {
  const response = await fetch(`${API_URL}/api/players/${nickname}/stats`, {
    headers: {
      'X-API-Key': API_KEY,
    },
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return await response.json();
}

async function analyzePlayer(nickname) {
  const response = await fetch(`${API_URL}/api/players/${nickname}/analyze`, {
    method: 'POST',
    headers: {
      'X-API-Key': API_KEY,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return await response.json();
}

// Usage example
(async () => {
  try {
    const nickname = 's1mple';

    console.log(`Getting stats for ${nickname}...`);
    const stats = await getPlayerStats(nickname);
    console.log(`Level: ${stats.level}`);
    console.log(`ELO: ${stats.elo}`);

    console.log(`\nAnalyzing player ${nickname}...`);
    const analysis = await analyzePlayer(nickname);
    console.log(`Recommendation: ${analysis.recommendation}`);
  } catch (error) {
    console.error('Error:', error.message);
  }
})();
