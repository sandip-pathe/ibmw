"use client";

import { useState } from "react";
import { apiClient } from "@/lib/api-client";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Github, Shield } from "lucide-react";
import Link from "next/link";

export default function SignInPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleEmailSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      const result = await apiClient.login(email, password);
      localStorage.setItem("access_token", result.access_token);
      localStorage.setItem("user_email", email);
      router.push("/dashboard");
    } catch (err) {
      setError("Invalid email or password");
    }
  };

  const handleGitHubSignIn = () => {
    // Simulate GitHub auth - in production, implement OAuth
    localStorage.setItem("user_email", "user@example.com");
    localStorage.setItem("github_connected", "true");
    router.push("/dashboard");
  };

  return (
    <div className="min-h-screen bg-black flex items-center justify-center px-4">
      {/* Vercel Triangle Logo */}
      <Link href="/" className="absolute top-6 left-6">
        <div className="w-8 h-8 flex items-center">
          <svg viewBox="0 0 76 65" fill="white">
            <path d="M37.5274 0L75.0548 65H0L37.5274 0Z" />
          </svg>
        </div>
      </Link>

      <div className="w-full max-w-[340px]">
        <h1 className="text-white text-[32px] font-semibold text-center mb-8">
          Log in to Vercel
        </h1>

        {/* Email Input */}
        <form onSubmit={handleEmailSubmit} className="mb-4">
          <input
            type="email"
            placeholder="Email Address"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full h-12 px-4 bg-transparent border border-[#333] rounded-md text-white placeholder-gray-500 focus:outline-none focus:border-white transition-colors"
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full h-12 px-4 mt-2 bg-transparent border border-[#333] rounded-md text-white placeholder-gray-500 focus:outline-none focus:border-white transition-colors"
          />
          <Button
            type="submit"
            className="w-full h-12 mt-4 bg-white text-black hover:bg-gray-200 font-medium rounded-md"
          >
            Continue with Email
          </Button>
          {error && <div className="text-red-500 text-sm mt-2">{error}</div>}
        </form>

        {/* GitHub Auth */}
        <Button
          onClick={handleGitHubSignIn}
          className="w-full h-12 mb-4 bg-transparent border border-[#333] hover:border-white text-white font-medium rounded-md flex items-center justify-center gap-3"
        >
          <Github className="w-5 h-5" />
          Continue with GitHub
        </Button>

        {/* Divider */}
        <div className="text-center text-gray-500 text-sm mt-6">
          Don&apos;t have an account?{" "}
          <Link href="/auth/signup" className="text-white hover:underline">
            Sign Up
          </Link>
        </div>
      </div>
    </div>
  );
}
