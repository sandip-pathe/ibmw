  // Email/password signup
  signup: async (email: string, password: string) => {
    const response = await fetch(`${API_URL}/auth/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!response.ok) throw new Error("Signup failed");
    return response.json() as Promise<{ access_token: string }>;
  },

  login: async (email: string, password: string) => {
    const response = await fetch(`${API_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!response.ok) throw new Error("Login failed");
    return response.json() as Promise<{ access_token: string }>;
  },
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface GitHubRepo {
  id: number;
  name: string;
  full_name: string;
  private: boolean;
  owner: {
    login: string;
    avatar_url: string;
  };
  description: string | null;
  html_url: string;
  default_branch: string;
  language: string | null;
  updated_at: string;
}

export interface IndexingStatus {
  repo_id: number;
  full_name: string;
  status: "pending" | "indexed";
  chunks_count: number;
  last_indexed: string | null;
}

export const apiClient = {
  // Get GitHub OAuth authorization URL
  async getGitHubAuthUrl(redirectUri: string, state?: string) {
    const response = await fetch(`${API_URL}/user/auth/github/authorize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ redirect_uri: redirectUri, state }),
    });
    if (!response.ok) throw new Error("Failed to get auth URL");
    return response.json() as Promise<{ authorization_url: string }>;
  },

  // Exchange GitHub OAuth code for token
  async exchangeGitHubCode(code: string, redirectUri: string) {
    const response = await fetch(`${API_URL}/user/auth/github/callback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code, redirect_uri: redirectUri }),
    });
    if (!response.ok) throw new Error("Failed to exchange code");
    return response.json() as Promise<{
      access_token: string;
      user: {
        id: number;
        login: string;
        name: string | null;
        email: string | null;
        avatar_url: string;
      };
    }>;
  },

  // List user's GitHub repositories
  async listUserRepos(accessToken: string) {
    const response = await fetch(`${API_URL}/user/repos`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    if (!response.ok) throw new Error("Failed to list repos");
    return response.json() as Promise<{ repos: GitHubRepo[]; total: number }>;
  },

  // Index selected repositories
  async indexRepositories(accessToken: string, repoIds: number[]) {
    const response = await fetch(`${API_URL}/user/repos/index`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ access_token: accessToken, repo_ids: repoIds }),
    });
    if (!response.ok) throw new Error("Failed to index repos");
    return response.json() as Promise<{
      success: boolean;
      message: string;
      repos: Array<{ id: number; full_name: string; status: string }>;
    }>;
  },

  // Get repository indexing status
  async getRepoStatus(repoId: number, accessToken: string) {
    const response = await fetch(`${API_URL}/user/repos/${repoId}/status`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    if (!response.ok) throw new Error("Failed to get repo status");
    return response.json() as Promise<IndexingStatus>;
  },
};
