"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Github, Shield, Code, Zap } from "lucide-react";
import { useStackApp } from "@stackframe/stack";

export default function Home() {
  const app = useStackApp();
  const user = app.useUser();
  const isAuthenticated = !!user;

  return (
    <div className="min-h-screen bg-black">
      {/* Navigation */}
      <nav className="border-b bg-black/80 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <Shield className="h-6 w-6 text-blue-600" />
            <span className="font-bold text-xl">Compliance Engine</span>
          </div>
          <div className="flex gap-3">
            {isAuthenticated ? (
              <>
                <Link href="/dashboard">
                  <Button variant="default">Go to Dashboard</Button>
                </Link>
                <Link href="/handler/sign-out">
                  <Button variant="ghost">Sign Out</Button>
                </Link>
              </>
            ) : (
              <>
                <Link href="/auth/signin">
                  <Button variant="ghost">Sign In</Button>
                </Link>
                <Link href="/auth/signin">
                  <Button>Get Started</Button>
                </Link>
              </>
            )}
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="container mx-auto px-4 py-20">
        <div className="text-center max-w-4xl mx-auto">
          <h1 className="text-5xl font-bold tracking-tight mb-6 text-white">
            AI-Powered Compliance
            <br />
            <span className="text-blue-400">For Fintech Code</span>
          </h1>
          <p className="text-xl text-gray-300 mb-8 max-w-2xl mx-auto">
            Automatically analyze your repositories for compliance violations.
            Connect your GitHub account and get instant insights.
          </p>
          <div className="flex gap-4 justify-center">
            {isAuthenticated ? (
              <>
                <Link href="/dashboard">
                  <Button size="lg" className="gap-2">
                    Go to Dashboard
                  </Button>
                </Link>
                <Link href="/handler/sign-out">
                  <Button size="lg" variant="outline">
                    Sign Out
                  </Button>
                </Link>
              </>
            ) : (
              <>
                <Link href="/auth/signin">
                  <Button size="lg" className="gap-2">
                    <Github className="h-5 w-5" />
                    Start with GitHub
                  </Button>
                </Link>
                <Link href="/auth/signin">
                  <Button size="lg" variant="outline">
                    Sign In
                  </Button>
                </Link>
              </>
            )}
          </div>
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-3 gap-8 mt-20">
          <div className="p-6 bg-neutral-900 rounded-lg shadow-sm border border-neutral-800">
            <div className="bg-blue-900/30 w-12 h-12 rounded-lg flex items-center justify-center mb-4">
              <Code className="h-6 w-6 text-blue-400" />
            </div>
            <h3 className="font-semibold text-lg mb-2 text-white">
              Code Analysis
            </h3>
            <p className="text-gray-400">
              Deep AST parsing and semantic understanding of your codebase
            </p>
          </div>
          <div className="p-6 bg-neutral-900 rounded-lg shadow-sm border border-neutral-800">
            <div className="bg-blue-900/30 w-12 h-12 rounded-lg flex items-center justify-center mb-4">
              <Shield className="h-6 w-6 text-blue-400" />
            </div>
            <h3 className="font-semibold text-lg mb-2 text-white">
              Compliance Checks
            </h3>
            <p className="text-gray-400">
              Automated detection of regulatory violations and best practices
            </p>
          </div>
          <div className="p-6 bg-neutral-900 rounded-lg shadow-sm border border-neutral-800">
            <div className="bg-blue-900/30 w-12 h-12 rounded-lg flex items-center justify-center mb-4">
              <Zap className="h-6 w-6 text-blue-400" />
            </div>
            <h3 className="font-semibold text-lg mb-2 text-white">
              Real-time Sync
            </h3>
            <p className="text-gray-400">
              Continuous monitoring through GitHub webhooks for instant alerts
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
