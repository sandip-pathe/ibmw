"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { IndexingLogs } from "@/components/IndexingLogs";
import {
  Loader2,
  CheckCircle,
  Clock,
  AlertCircle,
  ArrowLeft,
  Shield,
} from "lucide-react";

interface IndexedRepo {
  id: number;
  full_name: string;
  status: "queued" | "indexing" | "completed" | "failed";
}

interface AgentLog {
  agent: string;
  message: string;
  timestamp: string;
  ts_epoch: number;
}

interface JobStatus {
  job_id: string;
  job_type: string;
  status: "queued" | "running" | "completed" | "failed";
  result?: any;
  error?: string;
  created_at?: string;
  started_at?: string;
  completed_at?: string;
}

export default function ReposStatusPage() {
  const router = useRouter();
  const [repos, setRepos] = useState<IndexedRepo[]>([]);
  const [scanLogs, setScanLogs] = useState<AgentLog[]>([]);
  const [scanId, setScanId] = useState<string>("");
  const [jobId, setJobId] = useState<string>("");
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("github_access_token");
    if (!token) {
      router.push("/handler/sign-in");
      return;
    }
    // Fetch actual repo status from backend
    const fetchRepos = async () => {
      try {
        const res = await fetch("http://localhost:8000/user/repos", {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const data = await res.json();
          // Map backend response to IndexedRepo[]
          const repoList = (data.repos || []).map((repo: any) => ({
            id: repo.id,
            full_name: repo.full_name,
            status: repo.status || "queued", // Use actual status if available
          }));
          setRepos(repoList);
        }
      } catch (e) {
        // Optionally log error
      }
    };
    fetchRepos();

    const storedScanId = localStorage.getItem("current_scan_id");
    if (storedScanId) setScanId(storedScanId);

    const storedJobId = localStorage.getItem("current_job_id");
    if (storedJobId) setJobId(storedJobId);
  }, [router]);

  useEffect(() => {
    if (!scanId) return;
    const interval = setInterval(async () => {
      try {
        const res = await fetch(
          `http://localhost:8000/analyze/scan/${scanId}/logs`
        );
        if (res.ok) {
          const data = await res.json();
          setScanLogs(data.logs || []);
        }
      } catch (e) {
        // Optionally log error
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [scanId]);

  useEffect(() => {
    if (!jobId) return;
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`http://localhost:8000/jobs/${jobId}/status`);
        if (res.ok) {
          const data = await res.json();
          setJobStatus(data);
        }
      } catch (e) {
        // Optionally log error
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [jobId]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case "indexing":
        return <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />;
      case "queued":
        return <Clock className="h-5 w-5 text-gray-400" />;
      case "failed":
        return <AlertCircle className="h-5 w-5 text-red-600" />;
      default:
        return <Clock className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "completed":
        return "Indexed";
      case "indexing":
        return "Indexing...";
      case "queued":
        return "Queued";
      case "failed":
        return "Failed";
      default:
        return "Unknown";
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-green-50 text-green-700 border-green-200";
      case "indexing":
        return "bg-blue-50 text-blue-700 border-blue-200";
      case "queued":
        return "bg-gray-50 text-gray-700 border-gray-200";
      case "failed":
        return "bg-red-50 text-red-700 border-red-200";
      default:
        return "bg-gray-50 text-gray-700 border-gray-200";
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white border-b">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => router.push("/dashboard")}
            >
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div className="flex items-center gap-2">
              <Shield className="h-6 w-6 text-blue-600" />
              <span className="font-bold text-xl">Indexing Status</span>
            </div>
          </div>
        </div>
      </nav>

      <main className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6">
          <h2 className="font-semibold text-blue-900 mb-2">
            Indexing in Progress
          </h2>
          <p className="text-sm text-blue-800">
            Your repositories are being analyzed. This may take a few minutes
            depending on the size of your codebase. You&apos;ll receive a
            notification when the analysis is complete.
          </p>
        </div>

        <div className="space-y-4">
          {repos.map((repo) => (
            <div
              key={repo.id}
              className={`rounded-lg p-6 border ${getStatusColor(repo.status)}`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  {getStatusIcon(repo.status)}
                  <div>
                    <h3 className="font-semibold">{repo.full_name}</h3>
                    <p className="text-sm opacity-75">
                      {getStatusText(repo.status)}
                    </p>
                  </div>
                </div>
                {repo.status === "completed" && (
                  <Button variant="outline" size="sm">
                    View Results
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Agent Logs Section */}
        <div className="mt-8">
          <IndexingLogs
            jobId={jobId}
            className="bg-white border rounded-xl overflow-hidden shadow-lg"
          />
        </div>

        {/* Job Status Section */}
        {jobStatus && (
          <div className="mt-8 bg-white border rounded-lg p-6">
            <h3 className="font-semibold text-blue-900 mb-4">Job Status</h3>
            <div className="flex items-center gap-4">
              <span className="font-mono text-xs text-blue-600">
                {jobStatus.status}
              </span>
              {jobStatus.error && (
                <span className="text-xs text-red-600">
                  Error: {jobStatus.error}
                </span>
              )}
            </div>
            {jobStatus.completed_at && (
              <div className="text-xs text-gray-500 mt-2">
                Completed at:{" "}
                {new Date(jobStatus.completed_at).toLocaleString()}
              </div>
            )}
          </div>
        )}

        <div className="mt-8 text-center">
          <Button variant="outline" onClick={() => router.push("/dashboard")}>
            Back to Dashboard
          </Button>
        </div>
      </main>
    </div>
  );
}
