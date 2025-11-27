"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { AgentTerminal } from "@/components/AgentTerminal";
import { Badge } from "@/components/ui/badge";
import { Loader2, CheckCircle, AlertTriangle, Shield } from "lucide-react";
import { AgentLog } from "@/lib/types";

// Simple Progress Component if shadcn/ui one is missing
const SimpleProgress = ({ value }: { value: number }) => (
  <div className="h-1 w-full bg-[#222] rounded-full overflow-hidden">
    <div
      className="h-full bg-blue-600 transition-all duration-500"
      style={{ width: `${value}%` }}
    />
  </div>
);

export default function ScanRunPage() {
  const params = useParams();
  const scanId = params.id as string;
  const [status, setStatus] = useState<string>("pending");
  const [logs, setLogs] = useState<AgentLog[]>([]);
  const [progress, setProgress] = useState(0);
  const [stats, setStats] = useState({ total: 0, critical: 0 });

  // Simulate Agent Stream (since we don't have a real websocket/SSE setup in the prototype backend yet)
  useEffect(() => {
    if (status === "completed") return;

    const interval = setInterval(() => {
      // In a real app, fetch logs from: GET /api/scans/:id/logs
      // Here we simulate the agents thinking

      if (progress < 100) {
        const phases = [
          {
            p: 10,
            agent: "PLANNER",
            msg: "Loading regulation context: RBI-KYC-MD...",
          },
          {
            p: 20,
            agent: "PLANNER",
            msg: "Identified 14 constraints. Generating search strategy.",
          },
          { p: 30, agent: "NAVIGATOR", msg: "Indexing repo file structure..." },
          {
            p: 40,
            agent: "NAVIGATOR",
            msg: "Found 3 candidate files for 'Data Storage' rule.",
          },
          {
            p: 50,
            agent: "INVESTIGATOR",
            msg: "Analyzing src/db/storage.py for encryption compliance...",
          },
          {
            p: 70,
            agent: "INVESTIGATOR",
            msg: "Analyzing src/api/auth.py for MFA logic...",
          },
          {
            p: 80,
            agent: "JUDGE",
            msg: "Verifying evidence against rule constraints...",
          },
          { p: 90, agent: "JIRA", msg: "Preparing violation reports..." },
        ] as const;

        // Find current phase
        const current = phases.find(
          (ph) => ph.p > progress && ph.p <= progress + 10
        );

        if (current && Math.random() > 0.6) {
          const newLog: AgentLog = {
            agent: current.agent,
            message: current.msg,
            timestamp: new Date().toISOString(),
            ts_epoch: Date.now(),
          };
          setLogs((prev) => [...prev, newLog]);
        }

        setProgress((prev) => Math.min(prev + Math.random() * 5, 100));
      } else {
        setStatus("completed");
        setLogs((prev) => [
          ...prev,
          {
            agent: "PLANNER",
            message: "Scan completed. 2 Critical Violations found.",
            timestamp: new Date().toISOString(),
            ts_epoch: Date.now(),
          },
        ]);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [progress, status]);

  return (
    <div className="max-w-6xl mx-auto p-8 h-screen flex flex-col">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div className="flex items-center gap-4">
          <div className="h-12 w-12 bg-[#111] border border-[#333] rounded-lg flex items-center justify-center">
            <Shield
              className={`h-6 w-6 ${
                status === "running"
                  ? "text-blue-500 animate-pulse"
                  : "text-gray-400"
              }`}
            />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white flex items-center gap-3">
              Compliance Scan #
              {scanId ? (
                scanId.substring(0, 6)
              ) : (
                <span className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
                  N/A
                </span>
              )}
              {status === "completed" ? (
                <Badge className="bg-green-900/30 text-green-400 border-green-900/50">
                  Completed
                </Badge>
              ) : (
                <Badge className="bg-blue-900/30 text-blue-400 border-blue-900/50 animate-pulse">
                  Running
                </Badge>
              )}
            </h1>
            <div className="flex items-center gap-2 text-sm text-gray-400 mt-1">
              <span>Target: main branch</span>
              <span>•</span>
              <span>Started 2m ago</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-3 gap-8 flex-1 min-h-0">
        {/* Left: Agent Terminal */}
        <div className="col-span-2 flex flex-col gap-4">
          <div className="bg-[#111] border border-[#333] rounded-xl p-1">
            {/* Progress Bar */}
            <div className="px-4 pt-4 pb-2">
              <div className="flex justify-between text-xs text-gray-500 mb-2 uppercase font-semibold">
                <span>Overall Progress</span>
                <span>{Math.round(progress)}%</span>
              </div>
              <SimpleProgress value={progress} />
            </div>
          </div>

          {/* Terminal */}
          <AgentTerminal logs={logs} className="flex-1" />
        </div>

        {/* Right: Live Stats */}
        <div className="space-y-4">
          <div className="bg-[#111] border border-[#333] rounded-xl p-6">
            <h3 className="text-sm font-medium text-gray-400 mb-4">
              Findings Detected
            </h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-red-950/20 border border-red-900/30 rounded-lg">
                <div className="flex items-center gap-3">
                  <AlertTriangle className="h-5 w-5 text-red-500" />
                  <span className="text-red-200">Critical</span>
                </div>
                <span className="text-2xl font-bold text-white">2</span>
              </div>

              <div className="flex items-center justify-between p-3 bg-orange-950/20 border border-orange-900/30 rounded-lg">
                <div className="flex items-center gap-3">
                  <AlertTriangle className="h-5 w-5 text-orange-500" />
                  <span className="text-orange-200">High</span>
                </div>
                <span className="text-2xl font-bold text-white">0</span>
              </div>

              <div className="flex items-center justify-between p-3 bg-[#050505] border border-[#222] rounded-lg">
                <div className="flex items-center gap-3">
                  <CheckCircle className="h-5 w-5 text-gray-600" />
                  <span className="text-gray-400">Compliant Checks</span>
                </div>
                <span className="text-2xl font-bold text-gray-500">14</span>
              </div>
            </div>
          </div>

          <div className="bg-[#111] border border-[#333] rounded-xl p-6">
            <h3 className="text-sm font-medium text-gray-400 mb-4">
              Active Agents
            </h3>
            <div className="space-y-3">
              {["PLANNER", "NAVIGATOR", "INVESTIGATOR", "JUDGE"].map(
                (agent) => {
                  const isActive =
                    logs.length > 0 &&
                    logs[logs.length - 1].agent === agent &&
                    status !== "completed";
                  return (
                    <div
                      key={agent}
                      className="flex items-center justify-between"
                    >
                      <span
                        className={`text-sm ${
                          isActive ? "text-white font-medium" : "text-gray-600"
                        }`}
                      >
                        {agent}
                      </span>
                      {isActive && (
                        <Loader2 className="h-3 w-3 animate-spin text-blue-500" />
                      )}
                    </div>
                  );
                }
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
