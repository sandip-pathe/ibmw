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
                AI-Powered Compliance for Fintech
              </h2>
              <p className="text-xl text-gray-600">
                Analyze your code repositories against regulatory requirements
                automatically.
              </p>
            </div>

            <div className="space-y-4">
              <div className="flex items-start gap-4">
                <div className="shrink-0 w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                  <Code className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 mb-1">
                    Deep Code Analysis
                  </h3>
                  <p className="text-gray-600 text-sm">
                    AST-aware parsing understands your code structure
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="shrink-0 w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                  <Zap className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 mb-1">
                    Real-time Monitoring
                  </h3>
                  <p className="text-gray-600 text-sm">
                    Get instant alerts on compliance violations via webhooks
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="shrink-0 w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                  <AlertTriangle className="h-5 w-5 text-orange-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 mb-1">
                    Actionable Insights
                  </h3>
                  <p className="text-gray-600 text-sm">
                    Detailed remediation guidance for each violation
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-blue-50 rounded-xl p-6 border border-blue-100">
              <div className="flex items-center gap-2 mb-3">
                <Check className="h-5 w-5 text-blue-600" />
                <span className="font-semibold text-blue-900">
                  Free for public repositories
                </span>
              </div>
              <p className="text-sm text-blue-700">
                Start analyzing your code in under 2 minutes
              </p>
            </div>
          </div>

          {/* Right: Sign up form */}
          <div className="w-full">
            <div className="lg:hidden text-center mb-8">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-linear-to-br from-blue-600 to-indigo-600 rounded-2xl mb-4 shadow-lg">
                <Shield className="h-8 w-8 text-white" />
              </div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Create your account
              </h1>
              <p className="text-gray-600">Start analyzing in minutes</p>
            </div>

            <div className="hidden lg:block mb-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
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
