"use client";

import { useRouter } from "next/navigation";
import { withAuth } from "@/lib/withAuth";
import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import {
  Github,
  Loader2,
  ArrowRight,
  Upload,
  Activity,
  FileText,
} from "lucide-react";
import { apiClient } from "@/lib/api-client";

interface GitHubUser {
  id: number;
  login: string;
  name?: string;
  email?: string;
  avatar_url: string;
}

function DashboardPage() {
  const router = useRouter();
  const [isConnectingGitHub, setIsConnectingGitHub] = useState(false);
  const [githubUser, setGithubUser] = useState<GitHubUser | null>(null);

  useEffect(() => {
    // Check if user is logged in
    const email = localStorage.getItem("user_email");
    if (!email) {
      router.push("/auth/signin");
      return;
    }

    // Check if GitHub is connected
    const token = localStorage.getItem("github_access_token");
    const userStr = localStorage.getItem("github_user");

    if (token && userStr) {
      try {
        const user = JSON.parse(userStr) as GitHubUser;
        setTimeout(() => setGithubUser(user), 0);
      } catch {
        // Invalid data, continue without GitHub
      }
    }
  }, [router]);
  const handleConnectGitHub = async () => {
    setIsConnectingGitHub(true);
    try {
      const redirectUri = `${window.location.origin}/auth/github/callback`;
      const result = await apiClient.getGitHubAuthUrl(redirectUri);
      window.location.href = result.authorization_url;
    } catch (error) {
      console.error("Failed to get GitHub auth URL:", error);
      setIsConnectingGitHub(false);
    }
  };

  const handleSignOut = () => {
    localStorage.removeItem("github_access_token");
    localStorage.removeItem("github_user");
    localStorage.removeItem("user_email");
    router.push("/");
  };

  if (!githubUser) {
    // Ideally show a state even if not connected to GitHub, but for now relying on this flow
    const email =
      typeof window !== "undefined" ? localStorage.getItem("user_email") : null;
    if (!email) return null;
    // If email exists but no github, render the connect github view (handled below)
  }

  const userEmail =
    typeof window !== "undefined" ? localStorage.getItem("user_email") : null;

  return (
    <div className="min-h-screen bg-black">
      {/* Navigation */}
      <nav className="border-b border-[#333]">
        <div className="container mx-auto px-6 py-4 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="w-6 h-6 flex items-center">
              <svg viewBox="0 0 76 65" fill="white">
                <path d="M37.5274 0L75.0548 65H0L37.5274 0Z" />
              </svg>
            </div>
            <span className="text-white font-semibold text-lg">
              Compliance Engine
            </span>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-gray-400 text-sm">
              {userEmail || githubUser?.login}
            </span>
            <Button
              variant="ghost"
              onClick={handleSignOut}
              className="text-gray-400 hover:text-white"
            >
              Sign Out
            </Button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-12">
        <div className="max-w-5xl mx-auto">
          <div className="mb-12">
            <h1 className="text-white text-3xl font-bold mb-2">
              Compliance Dashboard
            </h1>
            <p className="text-gray-400">
              Manage regulations and analyze repositories.
            </p>
          </div>

          {/* Regulation Tools Grid */}
          <div className="grid md:grid-cols-3 gap-6 mb-12">
            {/* Card 1: Live Feed */}
            <div
              className="bg-[#111] border border-[#333] p-6 rounded-xl hover:border-blue-800 transition-colors cursor-pointer group"
              onClick={() => router.push("/regulations/live")}
            >
              <div className="h-10 w-10 bg-blue-900/30 rounded-lg flex items-center justify-center mb-4 group-hover:bg-blue-600 group-hover:text-white transition-colors text-blue-500">
                <Activity className="h-5 w-5" />
              </div>
              <h3 className="text-white font-semibold mb-1">
                Live Regulatory Feed
              </h3>
              <p className="text-gray-400 text-sm">
                Monitor RBI & SEBI RSS feeds in real-time.
              </p>
            </div>

            {/* Card 2: Manual Upload */}
            <div
              className="bg-[#111] border border-[#333] p-6 rounded-xl hover:border-blue-800 transition-colors cursor-pointer group"
              onClick={() => router.push("/regulations/upload")}
            >
              <div className="h-10 w-10 bg-purple-900/30 rounded-lg flex items-center justify-center mb-4 group-hover:bg-purple-600 group-hover:text-white transition-colors text-purple-500">
                <Upload className="h-5 w-5" />
              </div>
              <h3 className="text-white font-semibold mb-1">
                Upload Regulation
              </h3>
              <p className="text-gray-400 text-sm">
                Ingest PDF Master Directions manually.
              </p>
            </div>

            {/* Card 3: Review Queue */}
            <div
              className="bg-[#111] border border-[#333] p-6 rounded-xl hover:border-blue-800 transition-colors cursor-pointer group"
              onClick={() => router.push("/regulations/review")}
            >
              <div className="h-10 w-10 bg-yellow-900/30 rounded-lg flex items-center justify-center mb-4 group-hover:bg-yellow-600 group-hover:text-white transition-colors text-yellow-500">
                <FileText className="h-5 w-5" />
              </div>
              <h3 className="text-white font-semibold mb-1">Review Queue</h3>
              <p className="text-gray-400 text-sm">
                Approve draft regulations detected by AI.
              </p>
            </div>
          </div>

          <h2 className="text-xl font-bold text-white mb-4">Repositories</h2>

          {!githubUser ? (
            <div className="bg-[#111] border border-[#333] rounded-lg p-12 text-center">
              <div className="w-16 h-16 bg-[#1a1a1a] border border-[#333] rounded-full flex items-center justify-center mx-auto mb-6">
                <Github className="h-8 w-8 text-gray-400" />
              </div>
              <h2 className="text-white text-2xl font-semibold mb-3">
                Connect GitHub
              </h2>
              <p className="text-gray-400 mb-8">
                Link your account to select repositories for analysis.
              </p>
              <Button
                onClick={handleConnectGitHub}
                disabled={isConnectingGitHub}
                className="bg-white text-black hover:bg-gray-200 h-11 px-6 font-medium gap-2"
              >
                {isConnectingGitHub ? (
                  <>
                    <Loader2 className="h-5 w-5 animate-spin" />
                    Connecting...
                  </>
                ) : (
                  <>
                    <Github className="h-5 w-5" />
                    Connect GitHub
                  </>
                )}
              </Button>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="bg-[#111] border border-[#2e2e2e] rounded-lg p-6 flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-green-500/10 border border-green-500/20 rounded-full flex items-center justify-center">
                    <Github className="h-6 w-6 text-green-500" />
                  </div>
                  <div>
                    <h3 className="text-white font-semibold">
                      GitHub Connected
                    </h3>
                    <p className="text-sm text-gray-400">
                      Ready to analyze code
                    </p>
                  </div>
                </div>
                <Button
                  onClick={() => router.push("/repos/select")}
                  className="bg-white text-black hover:bg-gray-200 h-10 px-5 font-medium gap-2"
                >
                  Select Repositories
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default withAuth(DashboardPage);
