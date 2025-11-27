"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Trash2, Save } from "lucide-react";
import { JiraIntegration } from "@/components/JiraComponent";

export default function SettingsPage() {
  const router = useRouter();
  const [saving, setSaving] = useState(false);

  const handleSave = () => {
    setSaving(true);
    setTimeout(() => setSaving(false), 1000);
  };

  return (
    <div className="min-h-screen bg-black text-gray-100">
      {/* Nav */}
      <nav className="border-b border-[#333]">
        <div className="container mx-auto px-6 py-4 flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => router.push("/dashboard")}
            className="text-gray-400 hover:text-white"
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <h1 className="text-xl font-semibold text-white">
            Workspace Settings
          </h1>
        </div>
      </nav>

      <main className="container mx-auto px-6 py-10 max-w-3xl space-y-12">
        {/* Integrations Section */}
        <section className="space-y-6">
          <div>
            <h2 className="text-xl font-semibold text-white">Integrations</h2>
            <p className="text-gray-400 text-sm mt-1">
              Manage connections to external tools.
            </p>
          </div>
          <JiraIntegration />
        </section>

        {/* Agent Config Section */}
        <section className="space-y-6">
          <div>
            <h2 className="text-xl font-semibold text-white">
              Compliance Agent
            </h2>
            <p className="text-gray-400 text-sm mt-1">
              Configure how the AI analyzes your code.
            </p>
          </div>

          <div className="bg-[#111] border border-[#333] rounded-xl p-6 space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-white font-medium">Auto-scan on Push</h3>
                <p className="text-sm text-gray-400">
                  Trigger analysis when code is pushed to default branch.
                </p>
              </div>
              <input
                type="checkbox"
                defaultChecked
                className="w-5 h-5 rounded border-gray-600 bg-[#222] text-blue-600 focus:ring-offset-0 accent-blue-600"
              />
            </div>

            <div className="pt-4 border-t border-[#222] flex items-center justify-between">
              <div>
                <h3 className="text-white font-medium">
                  Regulation Drift Detection
                </h3>
                <p className="text-sm text-gray-400">
                  Re-scan repos when RBI/SEBI circulars are updated.
                </p>
              </div>
              <input
                type="checkbox"
                defaultChecked
                className="w-5 h-5 rounded border-gray-600 bg-[#222] text-blue-600 focus:ring-offset-0 accent-blue-600"
              />
            </div>

            <div className="pt-4 border-t border-[#222] flex items-center justify-between">
              <div>
                <h3 className="text-white font-medium">Strict Mode</h3>
                <p className="text-sm text-gray-400">
                  Fail CI/CD pipelines on Critical violations.
                </p>
              </div>
              <input
                type="checkbox"
                className="w-5 h-5 rounded border-gray-600 bg-[#222] text-blue-600 focus:ring-offset-0 accent-blue-600"
              />
            </div>
          </div>

          <div className="flex justify-end">
            <Button
              onClick={handleSave}
              disabled={saving}
              className="bg-white text-black hover:bg-gray-200"
            >
              {saving ? (
                "Saving..."
              ) : (
                <>
                  <Save className="h-4 w-4 mr-2" />
                  Save Changes
                </>
              )}
            </Button>
          </div>
        </section>

        {/* Danger Zone */}
        <section className="space-y-6 pt-6 border-t border-[#222]">
          <div>
            <h2 className="text-xl font-semibold text-red-500">Danger Zone</h2>
            <p className="text-gray-400 text-sm mt-1">Irreversible actions.</p>
          </div>

          <div className="bg-red-950/10 border border-red-900/30 rounded-xl p-6 flex items-center justify-between">
            <div>
              <h3 className="text-white font-medium">Delete Workspace</h3>
              <p className="text-sm text-gray-400">
                Permanently remove all repositories, scans, and reports.
              </p>
            </div>
            <Button
              variant="destructive"
              className="bg-red-600 hover:bg-red-700"
            >
              <Trash2 className="h-4 w-4 mr-2" /> Delete
            </Button>
          </div>
        </section>
      </main>
    </div>
  );
}
