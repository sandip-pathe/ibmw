"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { apiClient, type ScrapeResult } from "@/lib/api-client";
import { Activity, RefreshCw, ArrowLeft, Radio } from "lucide-react";

function LiveFeedPage() {
  const router = useRouter();
  const [isScraping, setIsScraping] = useState(false);
  const [lastScrapeResult, setLastScrapeResult] = useState<ScrapeResult | null>(
    null
  );
  const [logs, setLogs] = useState<string[]>([]);

  // Mock logs for demo effect since we can't stream logs easily yet
  useEffect(() => {
    const interval = setInterval(() => {
      const now = new Date().toLocaleTimeString();
      // Randomly add "heartbeat" logs
      if (Math.random() > 0.7) {
        setLogs((prev) => [
          `[${now}] Polling RBI RSS feed... OK`,
          ...prev.slice(0, 9),
        ]);
      }
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleTriggerScrape = async () => {
    setIsScraping(true);
    const adminKey = "demo-admin-key-change-in-production"; // In real app, get from user profile/env

    try {
      setLogs((prev) => [
        `[${new Date().toLocaleTimeString()}] Manual scrape triggered...`,
        ...prev,
      ]);
      const result = await apiClient.triggerRSS(adminKey);
      setLastScrapeResult(result.data);
      setLogs((prev) => [
        `[${new Date().toLocaleTimeString()}] Scrape complete. New: ${
          result.data.new
        }, Errors: ${result.data.errors}`,
        ...prev,
      ]);
    } catch (err) {
      setLogs((prev) => [`[ERROR] Scrape failed: ${err}`, ...prev]);
    } finally {
      setIsScraping(false);
    }
  };

  return (
    <div className="min-h-screen bg-black text-gray-100">
      <nav className="border-b border-[#333] bg-black/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="container mx-auto px-6 py-4 flex justify-between items-center">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => router.push("/dashboard")}
            >
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div className="flex items-center gap-2">
              <Radio className="h-5 w-5 text-red-500 animate-pulse" />
              <span className="font-bold text-xl text-white">
                Live Regulatory Feed
              </span>
            </div>
          </div>
        </div>
      </nav>

      <main className="container mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Status Panel */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-[#111] border border-[#333] rounded-xl p-6">
              <div className="flex justify-between items-center mb-6">
                <div>
                  <h2 className="text-xl font-semibold text-white">
                    Scraper Status
                  </h2>
                  <p className="text-sm text-gray-500">
                    Agent: Active (5m interval)
                  </p>
                </div>
                <Button
                  onClick={handleTriggerScrape}
                  disabled={isScraping}
                  className={`gap-2 ${
                    isScraping
                      ? "bg-blue-900/20 text-blue-400"
                      : "bg-white text-black hover:bg-gray-200"
                  }`}
                >
                  <RefreshCw
                    className={`h-4 w-4 ${isScraping ? "animate-spin" : ""}`}
                  />
                  {isScraping ? "Scanning..." : "Trigger Now"}
                </Button>
              </div>

              <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="bg-[#0a0a0a] p-4 rounded-lg border border-[#222]">
                  <div className="text-gray-500 text-xs uppercase mb-1">
                    New Detected
                  </div>
                  <div className="text-2xl font-mono text-green-500">
                    {lastScrapeResult ? `+${lastScrapeResult.new}` : "--"}
                  </div>
                </div>
                <div className="bg-[#0a0a0a] p-4 rounded-lg border border-[#222]">
                  <div className="text-gray-500 text-xs uppercase mb-1">
                    Duplicates
                  </div>
                  <div className="text-2xl font-mono text-gray-400">
                    {lastScrapeResult ? lastScrapeResult.duplicates || 0 : "--"}
                  </div>
                </div>
                <div className="bg-[#0a0a0a] p-4 rounded-lg border border-[#222]">
                  <div className="text-gray-500 text-xs uppercase mb-1">
                    Errors
                  </div>
                  <div className="text-2xl font-mono text-red-500">
                    {lastScrapeResult ? lastScrapeResult.errors : "--"}
                  </div>
                </div>
              </div>

              <div className="bg-black rounded-lg p-4 font-mono text-sm h-64 overflow-y-auto border border-[#222]">
                {logs.map((log, i) => (
                  <div
                    key={i}
                    className="mb-1.5 text-gray-400 border-b border-[#1a1a1a] pb-1 last:border-0"
                  >
                    {log}
                  </div>
                ))}
                {logs.length === 0 && (
                  <span className="text-gray-600">Waiting for logs...</span>
                )}
              </div>
            </div>

            {/* Sources */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-[#111] border border-[#333] rounded-xl p-4 flex items-center gap-4">
                <div className="h-10 w-10 rounded-full bg-blue-900/30 flex items-center justify-center text-blue-500 font-bold">
                  R
                </div>
                <div>
                  <div className="text-white font-medium">
                    RBI Press Releases
                  </div>
                  <div className="text-xs text-green-500 flex items-center gap-1">
                    <div className="h-1.5 w-1.5 rounded-full bg-green-500"></div>{" "}
                    Online
                  </div>
                </div>
              </div>
              <div className="bg-[#111] border border-[#333] rounded-xl p-4 flex items-center gap-4">
                <div className="h-10 w-10 rounded-full bg-emerald-900/30 flex items-center justify-center text-emerald-500 font-bold">
                  S
                </div>
                <div>
                  <div className="text-white font-medium">SEBI Circulars</div>
                  <div className="text-xs text-green-500 flex items-center gap-1">
                    <div className="h-1.5 w-1.5 rounded-full bg-green-500"></div>{" "}
                    Online
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Incoming Stream (Visual Only) */}
          <div className="bg-[#111] border border-[#333] rounded-xl p-6 h-full">
            <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
              <Activity className="h-4 w-4 text-blue-500" />
              Incoming Stream
            </h3>
            <div className="space-y-4">
              {/* Mock items to make the page look alive if empty */}
              <div className="p-3 rounded border border-blue-900/30 bg-blue-900/10">
                <div className="flex justify-between text-xs text-blue-400 mb-1">
                  <span>RBI</span>
                  <span>Just now</span>
                </div>
                <p className="text-sm text-gray-300 line-clamp-2">
                  Master Direction on Information Technology Governance, Risk,
                  Controls and Assurance Practices...
                </p>
              </div>
              <div className="p-3 rounded border border-[#222] bg-[#161616] opacity-60">
                <div className="flex justify-between text-xs text-gray-500 mb-1">
                  <span>SEBI</span>
                  <span>10m ago</span>
                </div>
                <p className="text-sm text-gray-400 line-clamp-2">
                  Circular regarding framework for adoption of Cloud Services by
                  SEBI Regulated Entities...
                </p>
              </div>
            </div>
            <div className="mt-6 text-center">
              <Button
                variant="outline"
                className="w-full border-[#333] text-gray-400 hover:text-white"
                onClick={() => router.push("/regulations/review")}
              >
                Go to Review Queue
              </Button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default LiveFeedPage;
