"use client";

import { useEffect, useState } from "react";
import { apiClient, type Violation } from "@/lib/api-client";
import { FindingCard } from "@/components/compliance/FindingCard";
import { Button } from "@/components/ui/button";
import { Loader2, Check, Filter } from "lucide-react";
import { useStackApp } from "@stackframe/stack";

export default function FindingsPage() {
  const [findings, setFindings] = useState<Violation[]>([]);
  const [loading, setLoading] = useState(true);
  const [processingId, setProcessingId] = useState<string | null>(null);
  const app = useStackApp();

  useEffect(() => {
    loadFindings();
  }, []);

  const loadFindings = async () => {
    const token = localStorage.getItem("github_access_token"); // Or stack token
    if (!token) return;

    try {
      setLoading(true);
      const data = await apiClient.getPendingViolations(token);
      setFindings(data);
    } catch (error) {
      console.error("Failed to load findings:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleAction = async (id: string, status: "approved" | "rejected") => {
    const token = localStorage.getItem("github_access_token");
    if (!token) return;

    setProcessingId(id);
    try {
      // 1. Update Status
      await apiClient.updateViolationStatus(
        id,
        status,
        "Reviewed via Dashboard",
        token
      );

      // 2. If approved, maybe create Jira ticket (optional auto-trigger)
      if (status === "approved") {
        try {
          await apiClient.createJiraTicket(id, token);
          // toast.success("Jira ticket created")
        } catch (e) {
          console.error("Jira creation failed", e);
        }
      }

      // 3. Optimistic UI update
      setFindings((prev) => prev.filter((f) => f.violation_id !== id));
    } catch (error) {
      console.error("Action failed", error);
    } finally {
      setProcessingId(null);
    }
  };

  if (loading) {
    return (
      <div className="h-[80vh] flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-gray-500" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white">Review Queue</h1>
          <p className="text-gray-400 mt-1">
            {findings.length} violations require human verification.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" className="border-[#333] text-gray-400">
            <Filter className="h-4 w-4 mr-2" /> Filter
          </Button>
        </div>
      </div>

      {findings.length === 0 ? (
        <div className="text-center py-20 border border-dashed border-[#333] rounded-xl bg-[#0a0a0a]">
          <div className="h-16 w-16 bg-[#111] rounded-full flex items-center justify-center mx-auto mb-4">
            <Check className="h-8 w-8 text-green-500" />
          </div>
          <h3 className="text-xl font-medium text-white">All Clean</h3>
          <p className="text-gray-500 mt-2">
            No pending violations found. Great job!
          </p>
          <Button
            variant="outline"
            className="mt-6"
            onClick={() => window.location.reload()}
          >
            Refresh
          </Button>
        </div>
      ) : (
        <div className="space-y-6">
          {findings.map((finding) => (
            <FindingCard
              key={finding.violation_id}
              violation={finding}
              isProcessing={processingId === finding.violation_id}
              onApprove={(id) => handleAction(id, "approved")}
              onReject={(id) => handleAction(id, "rejected")}
            />
          ))}
        </div>
      )}
    </div>
  );
}
