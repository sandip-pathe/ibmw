"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api-client";
import {
  Github,
  Shield,
  ArrowLeft,
  Check,
  Code,
  Zap,
  AlertTriangle,
} from "lucide-react";
import Link from "next/link";

export default function SignUpPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const handleGitHubSignUp = async () => {
    setIsLoading(true);
    try {
      const redirectUri = `${window.location.origin}/auth/github/callback`;
      const result = await apiClient.getGitHubAuthUrl(redirectUri);
      window.location.href = result.authorization_url;
    } catch (error) {
      console.error("Failed to start GitHub auth:", error);
      setIsLoading(false);
    }
  };

  const handleEmailSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    try {
      const result = await apiClient.signup(email, password);
      localStorage.setItem("access_token", result.access_token);
      localStorage.setItem("user_email", email);
      router.push("/dashboard");
    } catch (err) {
      setError("Signup failed. Email may already be registered.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-linear-to-br from-blue-50 via-white to-indigo-50">
      {/* Header */}
      <div className="absolute top-4 left-4">
        <Link href="/">
          <Button variant="ghost" className="gap-2">
            <ArrowLeft className="h-4 w-4" />
            Back
          </Button>
        </Link>
      </div>

      <div className="min-h-screen flex items-center justify-center px-4 py-12">
        <div className="max-w-6xl w-full grid lg:grid-cols-2 gap-12 items-center">
          {/* Left: Benefits */}
          <div className="hidden lg:block space-y-8">
            <div>
              <div className="inline-flex items-center justify-center w-16 h-16 bg-linear-to-br from-blue-600 to-indigo-600 rounded-2xl mb-6 shadow-lg">
                <Shield className="h-8 w-8 text-white" />
              </div>
              <h2 className="text-4xl font-bold text-gray-900 mb-4">
                "use client";

                import { Button } from "@/components/ui/button";
                import Link from "next/link";

                export default function SignUpPage() {
                  return (
                    <div className="min-h-screen bg-linear-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center px-4 py-12">
                      <div className="w-full max-w-[340px] mx-auto">
                        <h1 className="text-3xl font-bold text-gray-900 mb-8 text-center">
                          Create your account
                        </h1>
                        {/* Neon Auth (includes GitHub & Google) */}
                        <Link href="/handler/sign-up" passHref legacyBehavior>
                          <Button className="w-full h-12 mb-4 bg-[#00e599] hover:bg-[#00c47a] text-black font-medium rounded-md flex items-center justify-center gap-3">
                            {/* Neon logo SVG */}
                            <svg width="20" height="20" viewBox="0 0 32 32" fill="none">
                              <circle cx="16" cy="16" r="16" fill="#00e599"/>
                              <path d="M10 16c0-3.314 2.686-6 6-6s6 2.686 6 6-2.686 6-6 6-6-2.686-6-6z" fill="#fff"/>
                            </svg>
                            Sign up with Neon, GitHub, or Google
                          </Button>
                        </Link>
                        <div className="text-center text-gray-500 text-sm mt-6">
                          Already have an account?{" "}
                          <Link href="/auth/signin" className="text-blue-600 hover:underline font-semibold">
                            Sign in
                          </Link>
                        </div>
                      </div>
                    </div>
                  );
                }
                Get started today
              </h2>
              <p className="text-gray-600">Sign up with your GitHub account</p>
            </div>

            <div className="bg-white rounded-2xl shadow-2xl border border-gray-200 p-8">
              <form className="space-y-4 mb-6" onSubmit={handleEmailSignup}>
                <input
                  type="email"
                  placeholder="Email Address"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full h-12 px-4 bg-transparent border border-[#333] rounded-md text-black placeholder-gray-500 focus:outline-none focus:border-blue-600 transition-colors"
                />
                <input
                  type="password"
                  placeholder="Password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full h-12 px-4 bg-transparent border border-[#333] rounded-md text-black placeholder-gray-500 focus:outline-none focus:border-blue-600 transition-colors"
                />
                <Button
                  type="submit"
                  disabled={isLoading}
                  className="w-full h-12 bg-blue-600 text-white hover:bg-blue-700 font-medium rounded-md"
                >
                  {isLoading ? "Signing up..." : "Sign up with Email"}
                </Button>
                {error && (
                  <div className="text-red-500 text-sm mt-2">{error}</div>
                )}
              </form>
              <Button
                onClick={handleGitHubSignUp}
                disabled={isLoading}
                size="lg"
                className="w-full bg-[#24292e] hover:bg-[#1b1f23] text-white gap-3 h-12 shadow-md"
              >
                <Github className="h-5 w-5" />
                {isLoading ? "Connecting..." : "Sign up with GitHub"}
              </Button>
              <div className="mt-6 text-center text-xs text-gray-500">
                By signing up, you agree to our{" "}
                <a href="#" className="text-blue-600 hover:underline">
                  Terms
                </a>{" "}
                and{" "}
                <a href="#" className="text-blue-600 hover:underline">
                  Privacy Policy
                </a>
              </div>
            </div>

            <div className="mt-6 text-center">
              <p className="text-sm text-gray-600">
                Already have an account?{" "}
                <Link
                  href="/auth/signin"
                  className="text-blue-600 hover:underline font-semibold"
                >
                  Sign in
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
