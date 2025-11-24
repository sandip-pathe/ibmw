"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { apiClient } from "@/lib/api-client";
import { Loader2 } from "lucide-react";

export default function GitHubCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const code = searchParams.get("code");

    const exchangeCode = async () => {
      if (!code) {
        setError("No authorization code received");
        return;
      }

      try {
        const redirectUri = `${window.location.origin}/auth/github/callback`;
        const result = await apiClient.exchangeGitHubCode(code, redirectUri);

        // Store GitHub access token in localStorage
        localStorage.setItem("github_access_token", result.access_token);
        localStorage.setItem("github_user", JSON.stringify(result.user));

        // Redirect to repository selection
        router.push("/dashboard");
      } catch (err) {
        console.error("Failed to exchange code:", err);
        setError("Failed to connect GitHub account. Please try again.");
      }
    };

    exchangeCode();
  }, [searchParams, router]);

  if (error) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="text-red-600 text-xl font-semibold mb-4">Error</div>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={() => router.push("/dashboard")}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50">
      <Loader2 className="h-12 w-12 animate-spin text-blue-600 mb-4" />
      <p className="text-gray-600">Connecting your GitHub account...</p>
    </div>
  );
}
