"use client";

import { useEffect, useRef, useState } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import {
  FileText,
  Zap,
  CheckCircle2,
  Loader2,
  Clock,
  FileCode,
  Package,
  AlertCircle,
} from "lucide-react";

interface IndexingLog {
  timestamp: string;
  level: string;
  message: string;
  context?: {
    file?: string;
    chunks?: number;
    total?: number;
    progress?: number;
  };
}

interface IndexingLogsProps {
  jobId?: string;
  className?: string;
}

export function IndexingLogs({ jobId, className }: IndexingLogsProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [logs, setLogs] = useState<IndexingLog[]>([]);
  const [stats, setStats] = useState({
    totalFiles: 0,
    processedFiles: 0,
    totalChunks: 0,
    status: "running" as "running" | "completed" | "failed",
  });

  // Auto-scroll to bottom on new logs
  useEffect(() => {
    if (scrollRef.current) {
      const scrollContainer = scrollRef.current.querySelector(
        "[data-radix-scroll-area-viewport]"
      );
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
      }
    }
  }, [logs]);

  // Poll for logs (simulated - replace with actual API call)
  useEffect(() => {
    if (!jobId) return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`http://localhost:8000/jobs/${jobId}/logs`);
        if (res.ok) {
          const data = await res.json();
          setLogs(data.logs || []);
          setStats(data.stats || stats);
        }
      } catch (e) {
        console.error("Failed to fetch logs:", e);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [jobId]);

  const parseLogMessage = (message: string) => {
    // Parse chunker messages
    if (message.includes("Chunked")) {
      const match = message.match(/Chunked (.+?): (\d+) chunks/);
      if (match) {
        return {
          type: "chunk",
          file: match[1],
          chunks: parseInt(match[2]),
          icon: FileText,
          color: "text-blue-400",
        };
      }
    }

    // Parse processing messages
    if (message.includes("Processed")) {
      const match = message.match(/Processed (\d+)\/(\d+) chunks/);
      if (match) {
        return {
          type: "progress",
          current: parseInt(match[1]),
          total: parseInt(match[2]),
          icon: Zap,
          color: "text-purple-400",
        };
      }
    }

    // Parse completion messages
    if (message.includes("Chunked 32 files into 54 chunks")) {
      return {
        type: "complete",
        icon: CheckCircle2,
        color: "text-green-400",
      };
    }

    // Default
    return {
      type: "info",
      icon: FileCode,
      color: "text-gray-400",
    };
  };

  const formatLogMessage = (message: string) => {
    // Highlight file paths
    const highlighted = message.replace(
      /(src\\[^\s:]+)/g,
      '<span class="text-cyan-400 font-mono">$1</span>'
    );

    // Highlight numbers
    return highlighted.replace(
      /(\d+)\s+(chunks?|files?)/g,
      '<span class="text-amber-400 font-semibold">$1</span> $2'
    );
  };

  const getLogIcon = (message: string) => {
    const parsed = parseLogMessage(message);
    const Icon = parsed.icon;
    return <Icon className={cn("w-4 h-4 shrink-0", parsed.color)} />;
  };

  const calculateProgress = () => {
    if (stats.totalFiles === 0) return 0;
    return Math.round((stats.processedFiles / stats.totalFiles) * 100);
  };

  return (
    <div className={cn("flex flex-col", className)}>
      {/* Header with Stats */}
      <div className="bg-[#111] border-b border-[#222] px-6 py-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
              <Package className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-white text-lg">
                Repository Indexing
              </h3>
              <p className="text-xs text-gray-500">
                Processing codebase for compliance analysis
              </p>
            </div>
          </div>
          <Badge
            variant="outline"
            className={cn(
              "text-xs px-3 py-1",
              stats.status === "running" &&
                "bg-blue-500/10 text-blue-400 border-blue-500/30",
              stats.status === "completed" &&
                "bg-green-500/10 text-green-400 border-green-500/30",
              stats.status === "failed" &&
                "bg-red-500/10 text-red-400 border-red-500/30"
            )}
          >
            {stats.status === "running" && (
              <Loader2 className="w-3 h-3 mr-1.5 animate-spin" />
            )}
            {stats.status === "completed" && (
              <CheckCircle2 className="w-3 h-3 mr-1.5" />
            )}
            {stats.status === "failed" && (
              <AlertCircle className="w-3 h-3 mr-1.5" />
            )}
            {stats.status.toUpperCase()}
          </Badge>
        </div>

        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-4 text-gray-400">
              <span>
                <FileCode className="inline w-3 h-3 mr-1" />
                {stats.processedFiles}/{stats.totalFiles} files
              </span>
              <span>
                <FileText className="inline w-3 h-3 mr-1" />
                {stats.totalChunks} chunks
              </span>
            </div>
            <span className="font-mono text-gray-400">
              {calculateProgress()}%
            </span>
          </div>
          <div className="h-1.5 bg-[#222] rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-blue-500 to-purple-600 transition-all duration-500 ease-out"
              style={{ width: `${calculateProgress()}%` }}
            />
          </div>
        </div>
      </div>

      {/* Logs Terminal */}
      <div className="bg-[#0a0a0a] flex-1">
        <div className="flex items-center justify-between px-4 py-2 bg-[#0d0d0d] border-b border-[#222]">
          <div className="flex items-center gap-2">
            <div className="flex gap-1.5">
              <div className="w-2.5 h-2.5 rounded-full bg-red-500/30 border border-red-500/50" />
              <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/30 border border-yellow-500/50" />
              <div className="w-2.5 h-2.5 rounded-full bg-green-500/30 border border-green-500/50" />
            </div>
            <span className="ml-2 text-xs text-gray-600 font-mono">
              indexing_worker.log
            </span>
          </div>
          <div className="flex items-center gap-2 text-xs text-gray-600">
            <div
              className={cn(
                "w-2 h-2 rounded-full",
                stats.status === "running" && "bg-green-500 animate-pulse",
                stats.status === "completed" && "bg-gray-500",
                stats.status === "failed" && "bg-red-500"
              )}
            />
            {stats.status === "running" ? "Live" : "Stopped"}
          </div>
        </div>

        <ScrollArea ref={scrollRef} className="h-[500px]">
          <div className="p-4 space-y-1 font-mono text-xs">
            {logs.length === 0 && (
              <div className="text-gray-600 italic">
                <Clock className="inline w-3 h-3 mr-2 animate-pulse" />
                Waiting for indexing to start...
              </div>
            )}
            {logs.map((log, i) => {
              const parsed = parseLogMessage(log.message);

              return (
                <div
                  key={i}
                  className="group flex gap-3 items-start py-1 hover:bg-[#111] -mx-2 px-2 rounded transition-colors animate-in fade-in slide-in-from-left-1 duration-200"
                >
                  <span className="text-gray-600 shrink-0 w-20 text-[10px] leading-5">
                    {new Date(log.timestamp).toLocaleTimeString([], {
                      hour12: false,
                      hour: "2-digit",
                      minute: "2-digit",
                      second: "2-digit",
                      fractionalSecondDigits: 3,
                    })}
                  </span>

                  <Badge
                    variant="outline"
                    className={cn(
                      "shrink-0 text-[9px] px-1.5 py-0 h-5 font-medium opacity-70 group-hover:opacity-100 transition-opacity",
                      log.level === "INFO" &&
                        "bg-blue-500/10 text-blue-400 border-blue-500/30",
                      log.level === "DEBUG" &&
                        "bg-gray-500/10 text-gray-400 border-gray-500/30",
                      log.level === "ERROR" &&
                        "bg-red-500/10 text-red-400 border-red-500/30"
                    )}
                  >
                    {log.level}
                  </Badge>

                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    {getLogIcon(log.message)}
                    <span
                      className="text-gray-300 leading-5"
                      dangerouslySetInnerHTML={{
                        __html: formatLogMessage(log.message),
                      }}
                    />
                  </div>

                  {/* Progress indicator for chunk processing */}
                  {parsed.type === "progress" && parsed.total && (
                    <div className="shrink-0 text-[10px] text-gray-500">
                      {Math.round(((parsed.current || 0) / parsed.total) * 100)}
                      %
                    </div>
                  )}
                </div>
              );
            })}

            {/* Live Cursor */}
            {stats.status === "running" && (
              <div className="flex items-center gap-2 mt-2">
                <div className="w-1.5 h-4 bg-blue-500/60 animate-pulse" />
                <span className="text-gray-600 text-[10px] italic">
                  Processing...
                </span>
              </div>
            )}
          </div>
        </ScrollArea>
      </div>

      {/* Footer Summary */}
      {stats.status === "completed" && (
        <div className="bg-green-500/5 border-t border-green-500/20 px-6 py-3">
          <div className="flex items-center gap-2 text-green-400 text-sm">
            <CheckCircle2 className="w-4 h-4" />
            <span className="font-medium">
              Indexing completed successfully!
            </span>
            <span className="text-gray-500 text-xs ml-auto">
              {stats.totalFiles} files • {stats.totalChunks} chunks indexed
            </span>
          </div>
        </div>
      )}

      {stats.status === "failed" && (
        <div className="bg-red-500/5 border-t border-red-500/20 px-6 py-3">
          <div className="flex items-center gap-2 text-red-400 text-sm">
            <AlertCircle className="w-4 h-4" />
            <span className="font-medium">Indexing failed</span>
          </div>
        </div>
      )}
    </div>
  );
}
