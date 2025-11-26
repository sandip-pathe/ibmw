"use client";

import { useEffect, useRef } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { AgentLog } from "@/lib/types";

interface AgentTerminalProps {
  logs: AgentLog[];
  className?: string;
}

export function AgentTerminal({ logs, className }: AgentTerminalProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

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

  const getAgentStyle = (agent: string) => {
    switch (agent) {
      case "PLANNER":
        return "text-purple-400 border-purple-400/30 bg-purple-400/10";
      case "NAVIGATOR":
        return "text-blue-400 border-blue-400/30 bg-blue-400/10";
      case "INVESTIGATOR":
        return "text-amber-400 border-amber-400/30 bg-amber-400/10";
      case "JUDGE":
        return "text-red-400 border-red-400/30 bg-red-400/10";
      case "JIRA":
        return "text-green-400 border-green-400/30 bg-green-400/10";
      default:
        return "text-gray-400 border-gray-800";
    }
  };

  return (
    <div
      className={cn(
        "flex flex-col bg-[#0a0a0a] border border-[#222] rounded-xl overflow-hidden font-mono text-sm",
        className
      )}
    >
      {/* Terminal Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-[#111] border-b border-[#222]">
        <div className="flex items-center gap-2">
          <div className="flex gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full bg-red-500/20 border border-red-500/50" />
            <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/20 border border-yellow-500/50" />
            <div className="w-2.5 h-2.5 rounded-full bg-green-500/20 border border-green-500/50" />
          </div>
          <span className="ml-2 text-xs text-gray-500">agent_runtime.log</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-600">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          Live
        </div>
      </div>

      {/* Logs Area */}
      <ScrollArea ref={scrollRef} className="flex-1 p-4 h-[400px]">
        <div className="space-y-3">
          {logs.length === 0 && (
            <div className="text-gray-600 italic">
              Waiting for agent startup...
            </div>
          )}
          {logs.map((log, i) => (
            <div
              key={i}
              className="flex gap-3 items-start animate-in fade-in slide-in-from-left-2 duration-300"
            >
              <span className="text-gray-600 text-xs shrink-0 mt-1">
                {new Date(log.timestamp).toLocaleTimeString([], {
                  hour12: false,
                  hour: "2-digit",
                  minute: "2-digit",
                  second: "2-digit",
                })}
              </span>
              <Badge
                variant="outline"
                className={cn(
                  "shrink-0 text-[10px] px-1.5 py-0 h-5",
                  getAgentStyle(log.agent)
                )}
              >
                {log.agent}
              </Badge>
              <span className="text-gray-300 break-all">{log.message}</span>
            </div>
          ))}
          {/* Cursor */}
          <div className="w-2 h-4 bg-blue-500/50 animate-pulse mt-2" />
        </div>
      </ScrollArea>
    </div>
  );
}
