"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Loader2, CheckCircle, Link as LinkIcon } from "lucide-react";

export function JiraIntegration() {
  const [isConnected, setIsConnected] = useState(false);
  const [loading, setLoading] = useState(false);
  const [config, setConfig] = useState({
    domain: "",
    email: "",
    apiToken: "",
    projectKey: "COMP",
  });

  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    // Simulate API call
    setTimeout(() => {
      setIsConnected(true);
      setLoading(false);
    }, 1500);
  };

  if (isConnected) {
    return (
      <div className="bg-[#111] border border-green-900/30 rounded-xl p-6 flex items-center justify-between animate-in fade-in">
        <div className="flex items-center gap-4">
          <div className="h-12 w-12 bg-green-900/20 rounded-lg flex items-center justify-center">
            <CheckCircle className="h-6 w-6 text-green-500" />
          </div>
          <div>
            <h3 className="text-white font-semibold">Jira Connected</h3>
            <p className="text-sm text-gray-400">
              Syncing with project {config.projectKey}
            </p>
          </div>
        </div>
        <Button
          variant="outline"
          onClick={() => setIsConnected(false)}
          className="border-red-900/30 text-red-400 hover:bg-red-950/30 hover:text-red-300"
        >
          Disconnect
        </Button>
      </div>
    );
  }

  return (
    <div className="bg-[#111] border border-[#333] rounded-xl p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="h-10 w-10 bg-blue-900/20 rounded-lg flex items-center justify-center">
          <LinkIcon className="h-5 w-5 text-blue-500" />
        </div>
        <div>
          <h3 className="text-white font-semibold">Connect Jira</h3>
          <p className="text-sm text-gray-400">
            Automate ticket creation for compliance violations.
          </p>
        </div>
      </div>

      <form onSubmit={handleConnect} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-300">
              Jira Domain
            </label>
            <input
              placeholder="company.atlassian.net"
              value={config.domain}
              onChange={(e) => setConfig({ ...config, domain: e.target.value })}
              className="w-full h-10 px-3 bg-[#0a0a0a] border border-[#333] rounded-md text-white focus:outline-none focus:border-blue-600"
              required
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-300">
              Project Key
            </label>
            <input
              placeholder="COMP"
              value={config.projectKey}
              onChange={(e) =>
                setConfig({ ...config, projectKey: e.target.value })
              }
              className="w-full h-10 px-3 bg-[#0a0a0a] border border-[#333] rounded-md text-white focus:outline-none focus:border-blue-600"
              required
            />
          </div>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-gray-300">Email</label>
          <input
            type="email"
            placeholder="admin@company.com"
            value={config.email}
            onChange={(e) => setConfig({ ...config, email: e.target.value })}
            className="w-full h-10 px-3 bg-[#0a0a0a] border border-[#333] rounded-md text-white focus:outline-none focus:border-blue-600"
            required
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-gray-300">API Token</label>
          <input
            type="password"
            placeholder="••••••••••••••••"
            value={config.apiToken}
            onChange={(e) => setConfig({ ...config, apiToken: e.target.value })}
            className="w-full h-10 px-3 bg-[#0a0a0a] border border-[#333] rounded-md text-white focus:outline-none focus:border-blue-600"
            required
          />
        </div>

        <div className="pt-2">
          <Button
            type="submit"
            className="w-full bg-white text-black hover:bg-gray-200"
            disabled={loading}
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Connecting...
              </>
            ) : (
              "Connect Integration"
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}
