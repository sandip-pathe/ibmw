"use client";

import { useState } from "react";
import Link from "next/link";
import { useStackApp } from "@stackframe/stack";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api-client";
import {
  Upload,
  ArrowLeft,
  FileText,
  CheckCircle,
  AlertCircle,
} from "lucide-react";

function UploadRegulationPage() {
  // ...existing code...
  const router = useRouter();
  const app = useStackApp();
  const user = app.useUser();
  const isAuthenticated = !!user;
  const [isUploading, setIsUploading] = useState(false);
  const [status, setStatus] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsUploading(true);
    setStatus(null);

    const formData = new FormData(e.currentTarget);
    const adminKey = "demo-admin-key-change-in-production"; // Should be env var or user context

    try {
      const result = await apiClient.uploadRegulation(formData, adminKey);
      setStatus({
        type: "success",
        message: `Document ingested successfully! ID: ${result.data.id}`,
      });
      // Optional: Redirect to library
      // setTimeout(() => router.push('/regulations/library'), 2000);
    } catch (err: unknown) {
      setStatus({
        type: "error",
        message: (err as Error).message || "Upload failed",
      });
    } finally {
      setIsUploading(false);
    }
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
            <ArrowLeft className="h-4 w-4" /> Back to Dashboard
          </Button>
          {isAuthenticated && (
            <Link href="/handler/sign-out">
              <Button variant="ghost" className="ml-4">
                Sign Out
              </Button>
            </Link>
          )}
        </div>
      </nav>

      <main className="container mx-auto px-6 py-12">
        <div className="max-w-2xl mx-auto">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-white mb-2">
              Ingest Regulation
            </h1>
            <p className="text-gray-400">
              Upload Master Directions or Circulars (PDF) to index them into the
              knowledge base.
            </p>
          </div>

          <div className="bg-[#111] border border-[#333] rounded-xl p-8">
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-300">
                    Regulator
                  </label>
                  <select
                    name="regulator"
                    className="w-full bg-black border border-[#333] rounded-md h-10 px-3 text-white focus:ring-2 focus:ring-blue-600 outline-none"
                  >
                    <option value="RBI">RBI</option>
                    <option value="SEBI">SEBI</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-300">
                    Document Type
                  </label>
                  <select
                    name="doc_type"
                    className="w-full bg-black border border-[#333] rounded-md h-10 px-3 text-white focus:ring-2 focus:ring-blue-600 outline-none"
                  >
                    <option value="master_direction">Master Direction</option>
                    <option value="circular">Circular</option>
                    <option value="notification">Notification</option>
                    <option value="act">Act</option>
                  </select>
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-300">
                  Title
                </label>
                <input
                  name="title"
                  required
                  placeholder="e.g. Master Direction on KYC"
                  className="w-full bg-black border border-[#333] rounded-md h-10 px-3 text-white focus:ring-2 focus:ring-blue-600 outline-none placeholder-gray-600"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-300">
                  Publish Date
                </label>
                <input
                  name="publish_date"
                  type="date"
                  required
                  className="w-full bg-black border border-[#333] rounded-md h-10 px-3 text-white focus:ring-2 focus:ring-blue-600 outline-none [scheme:dark]"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-300">
                  Document (PDF)
                </label>
                <div className="border-2 border-dashed border-[#333] rounded-lg p-8 text-center hover:bg-[#161616] transition-colors relative group">
                  <input
                    name="file"
                    type="file"
                    accept=".pdf"
                    required
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                  />
                  <FileText className="h-10 w-10 text-gray-500 mx-auto mb-3 group-hover:text-blue-500 transition-colors" />
                  <p className="text-sm text-gray-400 font-medium">
                    Click to upload or drag and drop
                  </p>
                  <p className="text-xs text-gray-600 mt-1">
                    PDF only (max 20MB)
                  </p>
                </div>
              </div>

              {status && (
                <div
                  className={`p-4 rounded-lg flex items-center gap-3 ${
                    status.type === "success"
                      ? "bg-green-900/20 text-green-400 border border-green-900/50"
                      : "bg-red-900/20 text-red-400 border border-red-900/50"
                  }`}
                >
                  {status.type === "success" ? (
                    <CheckCircle className="h-5 w-5" />
                  ) : (
                    <AlertCircle className="h-5 w-5" />
                  )}
                  <span>{status.message}</span>
                </div>
              )}

              <div className="pt-2">
                <Button
                  type="submit"
                  disabled={isUploading}
                  className="w-full bg-white text-black hover:bg-gray-200 h-11 font-medium"
                >
                  {isUploading ? (
                    <>Processing via LLM...</>
                  ) : (
                    <>
                      <Upload className="mr-2 h-4 w-4" /> Start Ingestion
                      Pipeline
                    </>
                  )}
                </Button>
              </div>

              <div className="text-xs text-center text-gray-600">
                This will trigger OCR, Chunking, Embedding and Vector Storage.
              </div>
            </form>
          </div>
        </div>
      </main>
    </div>
  );
}

export default UploadRegulationPage;
