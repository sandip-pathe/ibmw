import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { CheckCircle, XCircle, FileCode } from "lucide-react";
import { Violation } from "@/lib/types";

interface FindingCardProps {
  violation: Violation;
  onApprove: (id: string) => void;
  onReject: (id: string) => void;
  isProcessing: boolean;
}

export function FindingCard({
  violation,
  onApprove,
  onReject,
  isProcessing,
}: FindingCardProps) {
  const severityColors = {
    critical: "bg-red-950/30 text-red-400 border-red-900/50",
    high: "bg-orange-950/30 text-orange-400 border-orange-900/50",
    medium: "bg-yellow-950/30 text-yellow-400 border-yellow-900/50",
    low: "bg-blue-950/30 text-blue-400 border-blue-900/50",
  };

  return (
    <div className="bg-[#111] border border-[#222] rounded-xl overflow-hidden">
      {/* Header */}
      <div className="p-6 border-b border-[#222] flex justify-between items-start">
        <div className="space-y-1">
          <div className="flex items-center gap-3">
            <Badge
              variant="outline"
              className={severityColors[violation.severity]}
            >
              {violation.severity.toUpperCase()}
            </Badge>
            <span className="text-sm text-gray-500 font-mono">
              {violation.rule_id}
            </span>
          </div>
          <h3 className="text-lg font-semibold text-white mt-2">
            {violation.explanation.split(".")[0]}.
          </h3>
        </div>
      </div>

      {/* Code Context */}
      <div className="bg-[#050505] border-b border-[#222] p-4 overflow-x-auto">
        <div className="flex items-center gap-2 text-xs text-gray-500 mb-2 font-mono">
          <FileCode className="h-3 w-3" />
          {violation.file_path}:{violation.start_line}
        </div>
        <pre className="font-mono text-sm text-gray-300 leading-relaxed">
          <code>
            {/* Mocking code context display if evidence is raw text */}
            {violation.evidence || "// No snippet available"}
          </code>
        </pre>
      </div>

      {/* Analysis & Actions */}
      <div className="p-6 grid md:grid-cols-2 gap-6">
        <div>
          <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">
            AI Reasoning
          </h4>
          <p className="text-sm text-gray-400 leading-relaxed">
            {violation.explanation}
          </p>

          {violation.remediation && (
            <div className="mt-4">
              <h4 className="text-xs font-semibold text-green-500/70 uppercase mb-2">
                Suggested Fix
              </h4>
              <p className="text-sm text-gray-400 bg-green-950/10 p-3 rounded border border-green-900/20">
                {violation.remediation}
              </p>
            </div>
          )}
        </div>

        <div className="flex flex-col justify-end gap-3">
          <div className="flex items-center gap-3">
            <Button
              onClick={() => onReject(violation.violation_id)}
              disabled={isProcessing}
              variant="outline"
              className="flex-1 border-[#333] hover:bg-red-950/20 hover:text-red-400 hover:border-red-900/50"
            >
              <XCircle className="mr-2 h-4 w-4" />
              False Positive
            </Button>
            <Button
              onClick={() => onApprove(violation.violation_id)}
              disabled={isProcessing}
              className="flex-1 bg-white text-black hover:bg-gray-200"
            >
              <CheckCircle className="mr-2 h-4 w-4" />
              Confirm Issue
            </Button>
          </div>
          <div className="text-center">
            <Button variant="link" className="text-xs text-gray-500 h-auto p-0">
              Ask Agent a question about this finding
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
