"use client";

import { useRouter } from "next/navigation";
import { withAuth } from "@/lib/withAuth";
import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Github, Loader2, ArrowRight, Shield } from "lucide-react";
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
    router.push("/");
  };

  if (!githubUser) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
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
      <main className="container mx-auto px-6 py-16">
        <div className="max-w-3xl mx-auto">
          <h1 className="text-white text-4xl font-bold mb-3">
            Welcome
            {githubUser ? `, ${githubUser.name || githubUser.login}` : ""}!
          </h1>
          <p className="text-gray-400 text-lg mb-12">
            Connect your GitHub account to start analyzing your repositories for
            compliance.
          </p>

          {!githubUser ? (
            <div className="bg-[#111] border border-[#333] rounded-lg p-12">
              <div className="text-center max-w-md mx-auto">
                <div className="w-16 h-16 bg-[#1a1a1a] border border-[#333] rounded-full flex items-center justify-center mx-auto mb-6">
                  <Github className="h-8 w-8 text-gray-400" />
                </div>
                <h2 className="text-white text-2xl font-semibold mb-3">
                  Connect GitHub
                </h2>
                <p className="text-gray-400 mb-8">
                  Install the GitHub application for the accounts you wish to
                  import from to continue
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
                      Install
                    </>
                  )}
                </Button>
              </div>
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
                      Your GitHub account is linked
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

              <div className="bg-[#0a0a0a] border border-[#1a1a1a] rounded-lg p-6">
                <h3 className="text-white font-semibold mb-4">Next Steps</h3>
                <ul className="space-y-3 text-sm text-gray-400">
                  <li className="flex items-start gap-3">
                    <span className="text-blue-400 mt-0.5">•</span>
                    <span>Select repositories you want to analyze</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-blue-400 mt-0.5">•</span>
                    <span>
                      We&apos;ll index your code and analyze for compliance
                      issues
                    </span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-blue-400 mt-0.5">•</span>
                    <span>Get real-time alerts for new violations</span>
                  </li>
                </ul>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default withAuth(DashboardPage);
