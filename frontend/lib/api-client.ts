const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface User {
  email: string;
  user_id?: string;
}

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

// New Interfaces for Regulation Engine
export interface RegulationDoc {
  document_id: string;
  title: string;
  regulator: "RBI" | "SEBI";
  doc_type: string;
  publish_date: string;
  status: "active" | "draft" | "archived";
  source_url?: string;
}

export interface ScrapeResult {
  new: number;
  errors: number;
  duplicates: number;
}

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
    const response = await fetch(
      `${API_URL}/auth/github/callback?code=${encodeURIComponent(
        code
      )}&redirect_uri=${encodeURIComponent(redirectUri)}`,
      {
        method: "GET",
        headers: { "Content-Type": "application/json" },
      }
    );
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

  async getMe(token: string) {
    const res = await fetch(`${API_URL}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to fetch user");
    return res.json() as Promise<User>;
  },

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

  // List user's GitHub repositories
  async listUserRepos(stackAuthToken: string) {
    const response = await fetch(`${API_URL}/user/repos`, {
      headers: { Authorization: `Bearer ${stackAuthToken}` },
    });
    if (!response.ok) throw new Error("Failed to list repos");
    return response.json() as Promise<{ repos: GitHubRepo[]; total: number }>;
  },

  // Index selected repositories
  async indexRepositories(accessToken: string, repoIds: number[]) {
    const response = await fetch(`${API_URL}/user/repos/index`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify({ repo_ids: repoIds, access_token: accessToken }),
    });
    if (!response.ok) throw new Error("Failed to index repos");
    return response.json() as Promise<{
      success: boolean;
      message: string;
      repos: Array<{ id: number; full_name: string; status: string }>;
    }>;
  },

  // Get repository indexing status
  async getRepoStatus(repoId: number, stackAuthToken: string) {
    const response = await fetch(`${API_URL}/user/repos/${repoId}/status`, {
      headers: { Authorization: `Bearer ${stackAuthToken}` },
    });
    if (!response.ok) throw new Error("Failed to get repo status");
    return response.json() as Promise<IndexingStatus>;
  },

  // --- Regulation Engine Endpoints ---

  // Manual Upload
  async uploadRegulation(formData: FormData, adminKey: string) {
    const response = await fetch(`${API_URL}/regulations/upload`, {
      method: "POST",
      headers: {
        "X-API-Key": adminKey, // Using Admin Key for now as per backend
      },
      body: formData,
    });
    if (!response.ok) throw new Error("Upload failed");
    return response.json() as Promise<{
      message: string;
      data: { id: string };
    }>;
  },

  // Trigger RSS Scraper
  async triggerRSS(adminKey: string) {
    const response = await fetch(`${API_URL}/regulations/rss/trigger`, {
      method: "POST",
      headers: { "X-API-Key": adminKey },
    });
    if (!response.ok) throw new Error("RSS trigger failed");
    return response.json() as Promise<{ message: string; data: ScrapeResult }>;
  },

  // Get Review Queue (Drafts)
  // Note: using the admin regulations endpoint or a specific one if created
  async getReviewQueue(adminKey: string) {
    // For now, we might need to filter the list if the backend doesn't have a specific /review-queue endpoint yet
    // Or we assume /regulations returns all and we filter on client if needed
    // But based on previous context, we added /regulations/review-queue
    const response = await fetch(`${API_URL}/regulations/review-queue`, {
      headers: { "X-API-Key": adminKey },
    });
    if (!response.ok) return []; // Return empty if endpoint not ready
    return response.json() as Promise<RegulationDoc[]>;
  },
};
