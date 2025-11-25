// frontend/app/auth/github/callback/page.tsx
"use client";
import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { apiClient } from "@/lib/api-client";
import { Loader2 } from "lucide-react";

export default function GitHubCallback() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const code = searchParams.get("code");

  useEffect(() => {
    if (code) {
      const redirectUri = process.env.NEXT_PUBLIC_GITHUB_REDIRECT_URI;
      console.log("Using redirect URI:", redirectUri);
      apiClient
        .exchangeGitHubCode(code, redirectUri as string)
        .then((data) => {
          // Store the GitHub specific token separately or merge with auth context if backend unifies it
          localStorage.setItem("github_access_token", data.access_token);
          localStorage.setItem("github_user", JSON.stringify(data.user));
          router.push("/repos/select");
        })
        .catch((err) => {
          console.error(err);
          router.push("/dashboard?error=github_auth_failed");
        });
    }
  }, [code, router]);

  return (
    <div className="min-h-screen bg-black flex items-center justify-center flex-col gap-4">
      <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      <p className="text-gray-400">Connecting to GitHub...</p>
    </div>
  );
}
