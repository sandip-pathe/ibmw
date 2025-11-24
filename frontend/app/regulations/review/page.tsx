"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { apiClient, type RegulationDoc } from "@/lib/api-client";
import { ArrowLeft, Check, X, ExternalLink, Loader2 } from "lucide-react";

function ReviewQueuePage() {
  const router = useRouter();
  const [items, setItems] = useState<RegulationDoc[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadQueue = async () => {
      try {
        const adminKey = "demo-admin-key-change-in-production";
        const data = await apiClient.getReviewQueue(adminKey);
        // If backend returns message object instead of array (stub), handle it
        if (Array.isArray(data)) {
          setItems(data);
        } else {
          setItems([]);
        }
      } catch (e) {
        console.error(e);
      } finally {
        setIsLoading(false);
      }
    };
    loadQueue();
  }, []);

  const handleApprove = (id: string) => {
    // In a real app, call API to change status draft -> active
    setItems((prev) => prev.filter((i) => i.document_id !== id));
    // toast.success("Regulation approved and indexed")
  };

  const handleReject = (id: string) => {
    // Call API to delete or archive
    setItems((prev) => prev.filter((i) => i.document_id !== id));
  };

  return (
    <div className="min-h-screen bg-black text-gray-100">
      <nav className="border-b border-[#333]">
        <div className="container mx-auto px-6 py-4 flex justify-between items-center">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push("/dashboard")}
            className="text-gray-400 hover:text-white pl-0 gap-2"
          >
            <ArrowLeft className="h-4 w-4" /> Back
          </Button>
          <div className="text-sm font-medium text-yellow-500 bg-yellow-900/20 px-3 py-1 rounded-full border border-yellow-900/50">
            {items.length} Pending Review
          </div>
        </div>
      </nav>

      <main className="container mx-auto px-6 py-8">
        <h1 className="text-3xl font-bold text-white mb-8">
          Compliance Review Queue
        </h1>

        {isLoading ? (
          <div className="flex justify-center py-20">
            <Loader2 className="h-8 w-8 animate-spin text-gray-500" />
          </div>
        ) : items.length === 0 ? (
          <div className="text-center py-20 border border-dashed border-[#333] rounded-xl">
            <div className="h-16 w-16 bg-[#111] rounded-full flex items-center justify-center mx-auto mb-4">
              <Check className="h-8 w-8 text-green-500" />
            </div>
            <h3 className="text-xl font-medium text-white">All Caught Up</h3>
            <p className="text-gray-500 mt-2">
              No draft regulations pending approval.
            </p>
            <Button
              variant="outline"
              className="mt-6"
              onClick={() => router.push("/regulations/live")}
            >
              Check Live Feed
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            {items.map((doc) => (
              <div
                key={doc.document_id}
                className="bg-[#111] border border-[#333] rounded-xl p-6 flex flex-col lg:flex-row gap-6"
              >
                <div className="flex-1">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-3">
                      <span
                        className={`px-2 py-1 rounded text-xs font-bold ${
                          doc.regulator === "RBI"
                            ? "bg-blue-900/50 text-blue-400"
                            : "bg-emerald-900/50 text-emerald-400"
                        }`}
                      >
                        {doc.regulator}
                      </span>
                      <span className="text-xs text-gray-500 border border-[#333] px-2 py-1 rounded">
                        {doc.doc_type}
                      </span>
                      <span className="text-xs text-gray-500">
                        {doc.publish_date}
                      </span>
                    </div>
                  </div>
                  <h3 className="text-lg font-medium text-white mb-2">
                    {doc.title}
                  </h3>
                  {doc.source_url && (
                    <a
                      href={doc.source_url}
                      target="_blank"
                      className="text-sm text-blue-500 hover:underline flex items-center gap-1 mb-4"
                    >
                      View Source PDF <ExternalLink className="h-3 w-3" />
                    </a>
                  )}

                  <div className="bg-[#050505] p-4 rounded border border-[#222]">
                    <div className="text-xs text-gray-500 uppercase mb-2 font-bold">
                      AI Summary
                    </div>
                    <p className="text-sm text-gray-300 leading-relaxed">
                      This circular mandates changes to... [Simulated AI Summary
                      would go here based on extracted rules]
                    </p>
                  </div>
                </div>

                <div className="flex lg:flex-col gap-3 justify-center lg:border-l border-[#333] lg:pl-6 min-w-[140px]">
                  <Button
                    onClick={() => handleApprove(doc.document_id)}
                    className="bg-green-600 hover:bg-green-700 text-white w-full"
                  >
                    <Check className="h-4 w-4 mr-2" /> Approve
                  </Button>
                  <Button
                    onClick={() => handleReject(doc.document_id)}
                    variant="outline"
                    className="border-red-900/50 text-red-500 hover:bg-red-900/20 hover:text-red-400 w-full"
                  >
                    <X className="h-4 w-4 mr-2" /> Reject
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

export default ReviewQueuePage;
