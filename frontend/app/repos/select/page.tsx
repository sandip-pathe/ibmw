"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api-client";
import { Loader2, Search, Lock, ArrowLeft, CheckCircle2 } from "lucide-react";
import { GitHubRepo } from "@/lib/types";

function SelectReposPage() {
  const router = useRouter();
  const [repos, setRepos] = useState<GitHubRepo[]>([]);
  const [selectedRepoIds, setSelectedRepoIds] = useState<Set<number>>(
    new Set()
  );
  const [isLoading, setIsLoading] = useState(true);
  const [isIndexing, setIsIndexing] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadRepos = async () => {
      const token = localStorage.getItem("github_access_token");
      if (!token) {
        router.push("/auth/signin"); // Fixed route
        return;
      }

      try {
        setIsLoading(true);
        const result = await apiClient.listUserRepos(token);
        setRepos(result.repos);
      } catch (err) {
        console.error("Failed to load repos:", err);
        setError(
          "Failed to load repositories. Please check your GitHub connection."
        );
      } finally {
        setIsLoading(false);
      }
    };

    loadRepos();
  }, [router]);

  // ... [Helper functions same as before] ...
  const handleToggleRepo = (repoId: number) => {
    const newSelected = new Set(selectedRepoIds);
    if (newSelected.has(repoId)) {
      newSelected.delete(repoId);
    } else {
      newSelected.add(repoId);
    }
    setSelectedRepoIds(newSelected);
  };

  const handleIndexRepos = async () => {
    if (selectedRepoIds.size === 0) return;

    const token = localStorage.getItem("github_access_token");
    if (!token) return;

    try {
      setIsIndexing(true);
      const result = await apiClient.indexRepositories(
        token,
        Array.from(selectedRepoIds)
      );
      // Type guard for job_ids
      if (
        "job_ids" in result &&
        Array.isArray(result.job_ids) &&
        result.job_ids.length > 0
      ) {
        localStorage.setItem("current_job_id", result.job_ids[0]);
        // Optionally store all job_ids if needed
        // localStorage.setItem("current_job_ids", JSON.stringify(result.job_ids));
        router.push("/repos/status");
      } else {
        setError("No job IDs returned from backend.");
      }
    } catch (err) {
      console.error("Failed to index repos:", err);
      setError("Failed to start indexing. Please try again.");
    } finally {
      setIsIndexing(false);
    }
  };

  const filteredRepos = repos.filter((repo) =>
    repo.full_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-black text-gray-100">
      {/* Navigation */}
      <nav className="border-b border-[#333]">
        <div className="container mx-auto px-6 py-4 flex justify-between items-center">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => router.push("/dashboard")}
              className="text-gray-400 hover:text-white"
            >
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <h1 className="text-xl font-semibold text-white">
              Import Repositories
            </h1>
          </div>
        </div>
      </nav>

      <main className="container mx-auto px-6 py-8 max-w-4xl">
        {/* Search Box */}
        <div className="mb-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-500" />
            <input
              type="text"
              placeholder="Search your repositories..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-3 bg-[#111] border border-[#333] rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-600/50 transition-all"
            />
          </div>
        </div>

        {/* List */}
        {error && (
          <div className="mb-4 p-3 bg-red-900 text-red-200 rounded-xl border border-red-700">
            {error}
          </div>
        )}
        <div className="bg-[#111] border border-[#333] rounded-xl overflow-hidden">
          <div className="p-4 border-b border-[#333] bg-[#161616] flex justify-between items-center">
            <span className="text-sm text-gray-400">
              {filteredRepos.length} Repositories
            </span>
            <span className="text-sm text-blue-400 font-medium">
              {selectedRepoIds.size} Selected
            </span>
          </div>

          <div className="divide-y divide-[#222] max-h-[60vh] overflow-y-auto">
            {isLoading ? (
              <div className="p-8 text-center text-gray-500">
                Loading repositories...
              </div>
            ) : filteredRepos.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                No repositories found.
              </div>
            ) : (
              filteredRepos.map((repo) => (
                <div
                  key={repo.id}
                  onClick={() => handleToggleRepo(repo.id)}
                  className={`p-4 flex items-center gap-4 hover:bg-[#1a1a1a] cursor-pointer transition-colors ${
                    selectedRepoIds.has(repo.id) ? "bg-blue-900/10" : ""
                  }`}
                >
                  <div
                    className={`h-5 w-5 rounded border flex items-center justify-center transition-colors ${
                      selectedRepoIds.has(repo.id)
                        ? "bg-blue-600 border-blue-600"
                        : "border-gray-600"
                    }`}
                  >
                    {selectedRepoIds.has(repo.id) && (
                      <CheckCircle2 className="h-3.5 w-3.5 text-white" />
                    )}
                  </div>

                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-white">
                        {repo.full_name}
                      </span>
                      {repo.private && (
                        <Lock className="h-3 w-3 text-yellow-500" />
                      )}
                    </div>
                    <div className="text-xs text-gray-500 mt-0.5 flex gap-3">
                      {repo.language && <span>{repo.language}</span>}
                      <span>
                        Last updated:{" "}
                        {new Date(repo.updated_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Footer Action */}
        <div className="fixed bottom-0 left-0 right-0 bg-[#0a0a0a] border-t border-[#222] p-4 flex justify-end container mx-auto max-w-4xl">
          <Button
            size="lg"
            onClick={handleIndexRepos}
            disabled={selectedRepoIds.size === 0 || isIndexing}
            className="bg-white text-black hover:bg-gray-200 min-w-[150px]"
          >
            {isIndexing ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                Indexing...
              </>
            ) : (
              `Import ${selectedRepoIds.size} Repositories`
            )}
          </Button>
        </div>
      </main>
    </div>
  );
}

export default SelectReposPage;
