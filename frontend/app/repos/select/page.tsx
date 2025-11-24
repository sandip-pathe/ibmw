"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Skeleton } from "@/components/ui/skeleton";
import { apiClient, type GitHubRepo } from "@/lib/api-client";
import { Github, Loader2, Search, Lock, Globe, ArrowLeft } from "lucide-react";

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
        router.push("/handler/sign-in");
        return;
      }

      try {
        setIsLoading(true);
        const result = await apiClient.listUserRepos(token);
        setRepos(result.repos);
      } catch (err) {
        console.error("Failed to load repos:", err);
        setError("Failed to load repositories. Please try again.");
      } finally {
        setIsLoading(false);
      }
    };

    loadRepos();
  }, [router]);

  const handleToggleRepo = (repoId: number) => {
    const newSelected = new Set(selectedRepoIds);
    if (newSelected.has(repoId)) {
      newSelected.delete(repoId);
    } else {
      newSelected.add(repoId);
    }
    setSelectedRepoIds(newSelected);
  };

  const handleSelectAll = () => {
    const filteredRepos = repos.filter((repo) =>
      repo.full_name.toLowerCase().includes(searchQuery.toLowerCase())
    );
    if (selectedRepoIds.size === filteredRepos.length) {
      setSelectedRepoIds(new Set());
    } else {
      setSelectedRepoIds(new Set(filteredRepos.map((r) => r.id)));
    }
  };

  const handleIndexRepos = async () => {
    if (selectedRepoIds.size === 0) return;

    const token = localStorage.getItem("github_access_token");
    if (!token) return;

    try {
      setIsIndexing(true);
      await apiClient.indexRepositories(token, Array.from(selectedRepoIds));
      router.push("/repos/status");
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
    <div className="min-h-screen bg-black">
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
            <div className="flex items-center gap-3">
              <div className="w-6 h-6 flex items-center">
                <svg viewBox="0 0 76 65" fill="white">
                  <path d="M37.5274 0L75.0548 65H0L37.5274 0Z" />
                </svg>
              </div>
              <span className="text-white font-semibold text-lg">
                Select Repositories
              </span>
            </div>
          </div>
          <Button
            onClick={handleIndexRepos}
            disabled={selectedRepoIds.size === 0 || isIndexing}
            className="bg-white text-black hover:bg-gray-200 h-10 px-5 font-medium gap-2"
          >
            {isIndexing ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Indexing...
              </>
            ) : (
              <>
                Index {selectedRepoIds.size}{" "}
                {selectedRepoIds.size === 1 ? "Repository" : "Repositories"}
              </>
            )}
          </Button>
        </div>
      </nav>

      <main className="container mx-auto px-4 py-8">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-md mb-6">
            {error}
          </div>
        )}

        {/* Search and Select All */}
        <div className="bg-[#111] border border-[#333] rounded-lg p-6 mb-6">
          <div className="flex items-center gap-4 mb-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-500" />
              <input
                type="text"
                placeholder="Search repositories..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-black border border-[#333] rounded-md text-white placeholder-gray-500 focus:outline-none focus:border-white"
              />
            </div>
            <Button
              variant="outline"
              onClick={handleSelectAll}
              disabled={isLoading || filteredRepos.length === 0}
              className="border-[#333] text-white hover:bg-[#1a1a1a] hover:text-white"
            >
              {selectedRepoIds.size === filteredRepos.length
                ? "Deselect All"
                : "Select All"}
            </Button>
          </div>
          <p className="text-sm text-gray-400">
            Found {filteredRepos.length}{" "}
            {filteredRepos.length === 1 ? "repository" : "repositories"}
            {selectedRepoIds.size > 0 && ` • ${selectedRepoIds.size} selected`}
          </p>
        </div>

        {/* Repository List */}
        <div className="space-y-3">
          {isLoading ? (
            Array.from({ length: 5 }).map((_, i) => (
              <div
                key={i}
                className="bg-[#0b0b0b] border border-[#1a1a1a] rounded-lg p-6"
              >
                <div className="flex items-start gap-4">
                  <Skeleton className="h-5 w-5 rounded" />
                  <div className="flex-1 space-y-2">
                    <Skeleton className="h-5 w-2/3" />
                    <Skeleton className="h-4 w-full" />
                  </div>
                </div>
              </div>
            ))
          ) : filteredRepos.length === 0 ? (
            <div className="bg-[#0b0b0b] border border-[#1a1a1a] rounded-lg p-12 text-center">
              <Github className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-white mb-2">
                No repositories found
              </h3>
              <p className="text-gray-400">
                {searchQuery
                  ? "Try a different search term"
                  : "No repositories available"}
              </p>
            </div>
          ) : (
            filteredRepos.map((repo) => (
              <div
                key={repo.id}
                className={`bg-white rounded-lg shadow-sm p-6 border-2 transition-colors cursor-pointer hover:border-blue-200 ${
                  selectedRepoIds.has(repo.id)
                    ? "border-blue-500"
                    : "border-transparent"
                }`}
                onClick={() => handleToggleRepo(repo.id)}
              >
                <div className="flex items-start gap-4">
                  <Checkbox
                    checked={selectedRepoIds.has(repo.id)}
                    onCheckedChange={() => handleToggleRepo(repo.id)}
                    className="mt-1"
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <h3 className="font-semibold text-lg truncate text-white">
                        {repo.full_name}
                      </h3>
                      {repo.private ? (
                        <span className="inline-flex items-center gap-1 px-2 py-1 bg-yellow-500/10 text-yellow-500 text-xs rounded-full border border-yellow-500/20">
                          <Lock className="h-3 w-3" />
                          Private
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-500/10 text-green-500 text-xs rounded-full border border-green-500/20">
                          <Globe className="h-3 w-3" />
                          Public
                        </span>
                      )}
                      {repo.language && (
                        <span className="px-2 py-1 bg-[#1a1a1a] text-gray-400 text-xs rounded-full border border-[#333]">
                          {repo.language}
                        </span>
                      )}
                    </div>
                    {repo.description && (
                      <p className="text-gray-400 text-sm mb-2">
                        {repo.description}
                      </p>
                    )}
                    <div className="flex items-center gap-4 text-xs text-gray-500">
                      <span>
                        Updated {new Date(repo.updated_at).toLocaleDateString()}
                      </span>
                      <span>•</span>
                      <span>Branch: {repo.default_branch}</span>
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </main>
    </div>
  );
}

export default SelectReposPage;
