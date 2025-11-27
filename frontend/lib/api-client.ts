import {
  GitHubRepo,
  IndexingStatus,
  RegulationDoc,
  ScanStatus,
  ScrapeResult,
  User,
  Violation,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const apiClient = {
  // Get GitHub OAuth authorization URL
  async getGitHubAuthUrl(redirectUri: string, state?: string) {
    const response = await fetch(`${API_URL}/auth/github/authorize`, {
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
    console.log("[FRONTEND] Fetching /user/repos...");
    const response = await fetch(`${API_URL}/user/repos`, {
      headers: { Authorization: `Bearer ${stackAuthToken}` },
    });
    console.log("[FRONTEND] Response status:", response.status);
    const data = await response.json();
    console.log("[FRONTEND] Repositories data:", data);
    if (!response.ok) throw new Error("Failed to list repos");
    return data as { repos: GitHubRepo[]; total: number };
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

  // DEMO MODE: Preload Regulation
  async preloadDemoRegulation() {
    const response = await fetch(`${API_URL}/regulations/preload-demo`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    if (!response.ok) throw new Error("Failed to preload demo regulation");
    return response.json() as Promise<{
      message: string;
      data: {
        rule_id: string;
        title: string;
        chunk_count: number;
        status: "already_loaded" | "newly_loaded";
      };
    }>;
  },

  // DEMO MODE: Get Regulation Metadata
  async getDemoRegulationMetadata() {
    const response = await fetch(
      `${API_URL}/regulations/preload-demo/metadata`
    );
    if (!response.ok) throw new Error("Failed to get demo regulation metadata");
    return response.json() as Promise<{
      message: string;
      data: {
        rule_id: string;
        title: string;
        category: string;
        severity: string;
        chunk_count: number;
        regulatory_body: string;
      };
    }>;
  },

  // Manual Upload (DISABLED FOR DEMO)
  async uploadRegulation(formData: FormData, adminKey: string) {
    // ⚠️ This endpoint is disabled in demo mode
    const response = await fetch(`${API_URL}/regulations/upload`, {
      method: "POST",
      headers: {
        "X-API-Key": adminKey,
      },
      body: formData,
    });
    if (!response.ok) throw new Error("Upload disabled for demo");
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

  // --- Scans & Agents ---

  async getScanStatus(scanId: string, token: string) {
    // In a real app, we'd have a specific endpoint for logs,
    // but for now we might fetch scan details or generic status
    const res = await fetch(`${API_URL}/analyze/scan/${scanId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to fetch scan status");
    return res.json() as Promise<ScanStatus>;
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

  // --- Violations (Review Queue) ---

  async getPendingViolations(token: string) {
    const res = await fetch(`${API_URL}/violations/pending`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to fetch violations");
    return res.json() as Promise<Violation[]>;
  },

  async updateViolationStatus(
    violationId: string,
    status: "approved" | "rejected" | "ignored",
    note: string,
    token: string
  ) {
    const res = await fetch(`${API_URL}/violations/${violationId}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ status, note }),
    });
    if (!res.ok) throw new Error("Failed to update violation");
    return res.json() as Promise<Violation>;
  },

  async createJiraTicket(violationId: string, token: string) {
    const res = await fetch(`${API_URL}/integrations/jira/sync`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ violation_id: violationId }),
    });
    if (!res.ok) throw new Error("Failed to create Jira ticket");
    return res.json() as Promise<{ ticket_id: string; ticket_url: string }>;
  },
};
