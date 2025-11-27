"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  CheckCircle2,
  XCircle,
  Edit2,
  Save,
  Trash2,
  AlertCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface RemediationIssue {
  title: string;
  description: string;
  file: string;
  priority: "high" | "medium" | "low";
}

interface RemediationPanelProps {
  issues: RemediationIssue[];
  verdict?: {
    final_verdict: string;
    confidence: number;
    reason: string;
  };
  onApprove: (editedIssues: RemediationIssue[]) => void;
  onDecline: (reason?: string) => void;
  isLoading?: boolean;
  className?: string;
}

export function RemediationPanel({
  issues: initialIssues,
  verdict,
  onApprove,
  onDecline,
  isLoading = false,
  className,
}: RemediationPanelProps) {
  const [issues, setIssues] = useState<RemediationIssue[]>(initialIssues);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [declineReason, setDeclineReason] = useState("");
  const [showDeclineInput, setShowDeclineInput] = useState(false);

  const handleEdit = (index: number) => {
    setEditingIndex(index);
  };

  const handleSave = (index: number) => {
    setEditingIndex(null);
  };

  const handleDelete = (index: number) => {
    setIssues(issues.filter((_, i) => i !== index));
  };

  const handleFieldChange = (
    index: number,
    field: keyof RemediationIssue,
    value: string
  ) => {
    const updated = [...issues];
    updated[index] = { ...updated[index], [field]: value };
    setIssues(updated);
  };

  const getPriorityStyle = (priority: string) => {
    switch (priority) {
      case "high":
        return "bg-red-500/10 text-red-400 border-red-500/30";
      case "medium":
        return "bg-amber-500/10 text-amber-400 border-amber-500/30";
      case "low":
        return "bg-blue-500/10 text-blue-400 border-blue-500/30";
      default:
        return "bg-gray-500/10 text-gray-400 border-gray-500/30";
    }
  };

  const getVerdictStyle = (verdict: string) => {
    switch (verdict) {
      case "compliant":
        return "bg-green-500/10 text-green-400 border-green-500/30";
      case "non_compliant":
        return "bg-red-500/10 text-red-400 border-red-500/30";
      case "partial":
        return "bg-amber-500/10 text-amber-400 border-amber-500/30";
      default:
        return "bg-gray-500/10 text-gray-400 border-gray-500/30";
    }
  };

  return (
    <div className={cn("space-y-4", className)}>
      {/* Verdict Summary */}
      {verdict && (
        <Card className="border-[#222] bg-[#0a0a0a]">
          <CardHeader>
            <div className="flex items-start justify-between">
              <div className="space-y-1">
                <CardTitle className="text-lg">Compliance Verdict</CardTitle>
                <CardDescription>AI-generated assessment</CardDescription>
              </div>
              <Badge
                variant="outline"
                className={cn(
                  "text-xs",
                  getVerdictStyle(verdict.final_verdict)
                )}
              >
                {verdict.final_verdict.replace("_", " ").toUpperCase()}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-500">Confidence:</span>
              <div className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500 transition-all"
                  style={{ width: `${verdict.confidence * 100}%` }}
                />
              </div>
              <span className="text-sm font-mono text-gray-400">
                {Math.round(verdict.confidence * 100)}%
              </span>
            </div>
            <div className="text-sm text-gray-300">
              <AlertCircle className="inline w-4 h-4 mr-1 text-amber-500" />
              {verdict.reason}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Remediation Tasks */}
      <Card className="border-[#222] bg-[#0a0a0a]">
        <CardHeader>
          <CardTitle className="text-lg">Remediation Tasks</CardTitle>
          <CardDescription>
            Review and edit the proposed Jira tickets before approval
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {issues.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <CheckCircle2 className="w-12 h-12 mx-auto mb-3 text-green-500/50" />
              <p>No remediation tasks required</p>
            </div>
          ) : (
            issues.map((issue, index) => (
              <Card key={index} className="border-[#333] bg-[#111]">
                <CardContent className="pt-4 space-y-3">
                  <div className="flex items-start justify-between gap-2">
                    <Badge
                      variant="outline"
                      className={cn(
                        "text-xs",
                        getPriorityStyle(issue.priority)
                      )}
                    >
                      {issue.priority.toUpperCase()}
                    </Badge>
                    <div className="flex gap-1">
                      {editingIndex === index ? (
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleSave(index)}
                          className="h-8 w-8 p-0"
                        >
                          <Save className="w-4 h-4" />
                        </Button>
                      ) : (
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleEdit(index)}
                          className="h-8 w-8 p-0"
                        >
                          <Edit2 className="w-4 h-4" />
                        </Button>
                      )}
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleDelete(index)}
                        className="h-8 w-8 p-0 text-red-400 hover:text-red-300"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>

                  {editingIndex === index ? (
                    <div className="space-y-3">
                      <div>
                        <Label className="text-xs text-gray-500">Title</Label>
                        <Input
                          value={issue.title}
                          onChange={(e) =>
                            handleFieldChange(index, "title", e.target.value)
                          }
                          className="mt-1 bg-[#0a0a0a] border-[#333]"
                        />
                      </div>
                      <div>
                        <Label className="text-xs text-gray-500">
                          Description
                        </Label>
                        <Textarea
                          value={issue.description}
                          onChange={(e) =>
                            handleFieldChange(
                              index,
                              "description",
                              e.target.value
                            )
                          }
                          className="mt-1 bg-[#0a0a0a] border-[#333] min-h-[100px]"
                        />
                      </div>
                      <div>
                        <Label className="text-xs text-gray-500">
                          File Path
                        </Label>
                        <Input
                          value={issue.file}
                          onChange={(e) =>
                            handleFieldChange(index, "file", e.target.value)
                          }
                          className="mt-1 bg-[#0a0a0a] border-[#333] font-mono text-sm"
                        />
                      </div>
                      <div>
                        <Label className="text-xs text-gray-500">
                          Priority
                        </Label>
                        <select
                          value={issue.priority}
                          onChange={(e) =>
                            handleFieldChange(index, "priority", e.target.value)
                          }
                          className="mt-1 w-full rounded-md bg-[#0a0a0a] border border-[#333] px-3 py-2 text-sm"
                        >
                          <option value="high">High</option>
                          <option value="medium">Medium</option>
                          <option value="low">Low</option>
                        </select>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <h4 className="font-medium text-sm text-gray-200">
                        {issue.title}
                      </h4>
                      <p className="text-xs text-gray-400 whitespace-pre-wrap">
                        {issue.description}
                      </p>
                      {issue.file && (
                        <div className="text-xs text-gray-500 font-mono bg-[#0a0a0a] px-2 py-1 rounded border border-[#333]">
                          📁 {issue.file}
                        </div>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))
          )}
        </CardContent>
      </Card>

      {/* Action Buttons */}
      <div className="flex gap-3">
        {!showDeclineInput ? (
          <>
            <Button
              onClick={() => onApprove(issues)}
              disabled={isLoading || issues.length === 0}
              className="flex-1 bg-green-600 hover:bg-green-700"
            >
              <CheckCircle2 className="w-4 h-4 mr-2" />
              {isLoading
                ? "Creating Tickets..."
                : `Approve & Create ${issues.length} Ticket${
                    issues.length !== 1 ? "s" : ""
                  }`}
            </Button>
            <Button
              onClick={() => setShowDeclineInput(true)}
              disabled={isLoading}
              variant="outline"
              className="border-red-500/30 text-red-400 hover:bg-red-500/10"
            >
              <XCircle className="w-4 h-4 mr-2" />
              Decline
            </Button>
          </>
        ) : (
          <div className="flex-1 space-y-3">
            <Textarea
              placeholder="Optional: Provide a reason for declining..."
              value={declineReason}
              onChange={(e) => setDeclineReason(e.target.value)}
              className="bg-[#0a0a0a] border-[#333]"
            />
            <div className="flex gap-2">
              <Button
                onClick={() => onDecline(declineReason)}
                disabled={isLoading}
                className="flex-1 bg-red-600 hover:bg-red-700"
              >
                Confirm Decline
              </Button>
              <Button
                onClick={() => {
                  setShowDeclineInput(false);
                  setDeclineReason("");
                }}
                disabled={isLoading}
                variant="outline"
              >
                Cancel
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
