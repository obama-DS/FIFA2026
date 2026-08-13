import axios, { AxiosInstance } from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class APIService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('API Error:', error.response?.data || error.message);
        return Promise.reject(error);
      }
    );
  }

  // Health check
  async healthCheck() {
    try {
      const response = await this.client.get('/health');
      return response.data;
    } catch (error) {
      console.error('Health check failed:', error);
      throw error;
    }
  }

  // Model information
  async getModelInfo() {
    try {
      const response = await this.client.get('/model-info');
      return response.data;
    } catch (error) {
      console.error('Failed to get model info:', error);
      throw error;
    }
  }

  // Single match prediction
  async predictMatch(matchData: MatchFeatures) {
    try {
      const response = await this.client.post('/predict', matchData);
      return response.data;
    } catch (error) {
      console.error('Prediction failed:', error);
      throw error;
    }
  }

  // Bulk match predictions
  async predictBulkMatches(matches: MatchFeatures[]) {
    try {
      const response = await this.client.post('/predict/bulk', { matches });
      return response.data;
    } catch (error) {
      console.error('Bulk prediction failed:', error);
      throw error;
    }
  }

  // Gameweek data
  async getCurrentGameweek() {
    try {
      // Fetch from backend gameweek engine
      const response = await this.client.get('/gameweek/current');
      return response.data;
    } catch (error) {
      console.warn('Current gameweek endpoint not available:', error);
      // Return default structure if endpoint not available
      return {
        gameweek: 1,
        fixtures: [],
        deadline: new Date().toISOString(),
      };
    }
  }

  async getGameweekFixtures(gameweek: number) {
    try {
      const response = await this.client.get(`/gameweek/${gameweek}`);
      return response.data;
    } catch (error) {
      console.warn(`Failed to fetch gameweek ${gameweek}:`, error);
      return {
        gameweek,
        fixtures: [],
        deadline: new Date().toISOString(),
      };
    }
  }

  // Season simulation data
  async getSeasonProjections() {
    try {
      const response = await this.client.get('/oracle/projections');
      return response.data;
    } catch (error) {
      console.warn('Season projections endpoint not available:', error);
      return {
        timestamp: new Date().toISOString(),
        simulations: 0,
        season: '2026/27',
        teams: {},
        most_likely_table: [],
      };
    }
  }

  // Teams data
  async getTeams() {
    try {
      const response = await this.client.get('/teams');
      return response.data;
    } catch (error) {
      console.warn('Teams endpoint not available:', error);
      return [];
    }
  }

  async getTeam(teamId: string | number) {
    try {
      const response = await this.client.get(`/teams/${teamId}`);
      return response.data;
    } catch (error) {
      console.warn(`Failed to fetch team ${teamId}:`, error);
      return null;
    }
  }

  async searchTeams(query: string) {
    try {
      const response = await this.client.get('/teams/search', {
        params: { q: query },
      });
      return response.data;
    } catch (error) {
      console.warn('Team search failed:', error);
      return [];
    }
  }

  // Players data
  async getPlayers() {
    try {
      const response = await this.client.get('/players');
      return response.data;
    } catch (error) {
      console.warn('Players endpoint not available:', error);
      return [];
    }
  }

  async getPlayer(playerId: string | number) {
    try {
      const response = await this.client.get(`/players/${playerId}`);
      return response.data;
    } catch (error) {
      console.warn(`Failed to fetch player ${playerId}:`, error);
      return null;
    }
  }

  async searchPlayers(query: string) {
    try {
      const response = await this.client.get('/players/search', {
        params: { q: query },
      });
      return response.data;
    } catch (error) {
      console.warn('Player search failed:', error);
      return [];
    }
  }

  // Beat the AI - Predictions submission
  async submitBeatTheAIPredictions(predictions: any) {
    try {
      const response = await this.client.post('/beat-ai/submit', predictions);
      return response.data;
    } catch (error) {
      console.error('Failed to submit predictions:', error);
      throw error;
    }
  }

  async getBeatTheAILeaderboard(limit: number = 100) {
    try {
      const response = await this.client.get('/beat-ai/leaderboard', {
        params: { limit },
      });
      return response.data;
    } catch (error) {
      console.warn('Leaderboard not available:', error);
      return [];
    }
  }
}

// Types matching backend schemas
export interface MatchFeatures {
  home_team_name: string;
  away_team_name: string;
  home_goals_last3: number;
  home_conceded_last3: number;
  away_goals_last3: number;
  away_conceded_last3: number;
  home_goals_last5: number;
  home_conceded_last5: number;
  away_goals_last5: number;
  away_conceded_last5: number;
  home_goals_last10: number;
  home_conceded_last10: number;
  away_goals_last10: number;
  away_conceded_last10: number;
  home_season_goals: number;
  home_season_conceded: number;
  away_season_goals: number;
  away_season_conceded: number;
  h2h_home_wins?: number;
  h2h_away_wins?: number;
  h2h_draws?: number;
}

export interface PredictionResponse {
  home_team: string;
  away_team: string;
  predicted_home_goals: number;
  predicted_away_goals: number;
  predicted_result: 'H' | 'D' | 'A';
  confidence: {
    home_win: number;
    draw: number;
    away_win: number;
  };
}

export interface ModelInfo {
  model_version: string;
  model_type: string;
  training_date: string;
  metrics: {
    val_mae_avg: number;
    val_r2_avg: number;
    val_mae_home: number;
    val_mae_away: number;
  };
  feature_count: number;
  description: string;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  version: string;
}

// Export singleton instance
const apiService = new APIService();
export default apiService;
