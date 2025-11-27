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
  Info,
} from "lucide-react";

/**
 * ⚠️ DEMO MODE: Upload Disabled
 *
 * This page is disabled for the hackathon demo.
 * The system uses a preloaded RBI Payment Aggregator regulation instead.
 *
 * To re-enable uploads:
 * 1. Remove the demo mode banner
 * 2. Enable the form (remove disabled attribute)
 * 3. Uncomment the upload endpoint in backend/app/api/regulations.py
 */

function UploadRegulationPage() {
  const router = useRouter();
  const app = useStackApp();
  const user = app.useUser();
  const isAuthenticated = !!user;

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
          {/* DEMO MODE BANNER */}
          <div className="mb-8 bg-blue-900/20 border border-blue-500/30 rounded-lg p-6">
            <div className="flex items-start gap-4">
              <Info className="h-6 w-6 text-blue-400 mt-0.5 shrink-0" />
              <div>
                <h2 className="text-lg font-semibold text-blue-400 mb-2">
                  Demo Mode Active
                </h2>
                <p className="text-gray-300 text-sm leading-relaxed">
                  For this hackathon demo, regulation upload is disabled. The
                  system uses a preloaded{" "}
                  <strong>RBI Payment Aggregator regulation</strong>.
                </p>
                <p className="text-gray-400 text-xs mt-3">
                  Simply select the Payment Aggregator category when scanning
                  repositories, and the regulation will be automatically loaded.
                </p>
              </div>
            </div>
          </div>

          <div className="mb-8">
            <h1 className="text-3xl font-bold text-white mb-2">
              Ingest Regulation
            </h1>
            <p className="text-gray-400">
              Upload Master Directions or Circulars (PDF) to index them into the
              knowledge base.
            </p>
          </div>

          {/* DISABLED FORM */}
          <div className="bg-[#111] border border-[#333] rounded-xl p-8 opacity-50 cursor-not-allowed">
            <form className="space-y-6 pointer-events-none">
              <div className="grid grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-300">
                    Regulator
                  </label>
                  <select
                    name="regulator"
                    disabled
                    className="w-full bg-black border border-[#333] rounded-md h-10 px-3 text-white outline-none"
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
                    disabled
                    className="w-full bg-black border border-[#333] rounded-md h-10 px-3 text-white outline-none"
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
                  disabled
                  placeholder="e.g. Master Direction on KYC"
                  className="w-full bg-black border border-[#333] rounded-md h-10 px-3 text-white outline-none placeholder-gray-600"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-300">
                  Publish Date
                </label>
                <input
                  name="publish_date"
                  type="date"
                  disabled
                  className="w-full bg-black border border-[#333] rounded-md h-10 px-3 text-white outline-none"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-300">
                  Document (PDF)
                </label>
                <div className="border-2 border-dashed border-[#333] rounded-lg p-8 text-center">
                  <FileText className="h-10 w-10 text-gray-500 mx-auto mb-3" />
                  <p className="text-sm text-gray-400 font-medium">
                    Upload disabled in demo mode
                  </p>
                  <p className="text-xs text-gray-600 mt-1">
                    Using preloaded regulation
                  </p>
                </div>
              </div>

              <div className="pt-2">
                <Button
                  type="button"
                  disabled
                  className="w-full bg-gray-800 text-gray-500 h-11 font-medium cursor-not-allowed"
                >
                  <Upload className="mr-2 h-4 w-4" /> Upload Disabled for Demo
                </Button>
              </div>

              <div className="text-xs text-center text-gray-600">
                Feature will be enabled in production version
              </div>
            </form>
          </div>
        </div>
      </main>
    </div>
  );
}

export default UploadRegulationPage;
