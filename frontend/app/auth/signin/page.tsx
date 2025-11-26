"use client";
import { apiClient } from "@/lib/api-client";

export default function SignInPage() {
  // Handler for GitHub login
  const handleGitHubLogin = async () => {
    const redirectUri = `${window.location.origin}/auth/github/callback`;
    const { authorization_url } = await apiClient.getGitHubAuthUrl(redirectUri);
    window.location.href = authorization_url;
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen">
      <h1 className="text-2xl font-bold mb-6">Sign In</h1>
      {/* Stack Auth login button (redirects to hosted flow) */}
      <a
        href={
          process.env.NEXT_PUBLIC_STACK_AUTH_URL ||
          "https://stackauth.com/login"
        }
        className="mb-4 px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
      >
        Sign in with Email
      </a>
      {/* Custom GitHub login button */}
      <button
        onClick={handleGitHubLogin}
        className="px-6 py-2 bg-gray-800 text-white rounded hover:bg-gray-900"
      >
        Sign in with GitHub
      </button>
    </div>
  );
}
