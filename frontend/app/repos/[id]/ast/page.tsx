// frontend/app/repos/[id]/ast/page.tsx
"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { ArrowLeft, FileCode, Folder, Box } from "lucide-react";

// Simple Tree Component
const FileNode = ({
  name,
  type,
  depth,
}: {
  name: string;
  type: "file" | "folder";
  depth: number;
}) => (
  <div
    className="flex items-center gap-2 py-1 text-sm text-gray-300 hover:bg-[#1a1a1a] rounded px-2"
    style={{ paddingLeft: `${depth * 20}px` }}
  >
    {type === "folder" ? (
      <Folder className="h-4 w-4 text-blue-500" />
    ) : (
      <FileCode className="h-4 w-4 text-gray-500" />
    )}
    <span>{name}</span>
    {type === "file" && (
      <span className="ml-auto text-xs text-gray-600 border border-[#333] px-1 rounded">
        AST Parsed
      </span>
    )}
  </div>
);

export default function ASTViewerPage() {
  const params = useParams();
  const router = useRouter();
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [files, setFiles] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Since we don't have a direct "Get AST" endpoint, we simulate the structure
    // or fetch the analysis result which contains file paths.
    // For now, we will simulate based on the "Scan" endpoint logic which triggers analysis.
    // In a real app, we'd hit an endpoint like `/repos/{id}/tree`

    setTimeout(() => {
      setFiles([
        { path: "src/main.py", type: "file" },
        { path: "src/utils", type: "folder" },
        { path: "src/utils/auth.py", type: "file" },
        { path: "tests/test_main.py", type: "file" },
        { path: "requirements.txt", type: "file" },
      ]);
      setLoading(false);
    }, 1000);
  }, [params.id]);

  return (
    <div className="min-h-screen bg-black text-gray-100">
      <nav className="border-b border-[#333] bg-black">
        <div className="container mx-auto px-6 py-4 flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router.back()}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div className="flex items-center gap-2">
            <Box className="h-6 w-6 text-purple-500" />
            <h1 className="font-bold text-lg">Repository AST Explorer</h1>
          </div>
        </div>
      </nav>

      <main className="container mx-auto px-6 py-8 grid grid-cols-3 gap-8">
        {/* File Tree */}
        <div className="col-span-1 bg-[#111] border border-[#333] rounded-xl p-4 h-[80vh] overflow-y-auto">
          <h3 className="text-xs font-bold text-gray-500 uppercase mb-4">
            Project Structure
          </h3>
          {loading ? (
            <div className="text-gray-600 text-sm">Loading AST map...</div>
          ) : (
            <div className="space-y-1">
              {files.map((f, i) => (
                <FileNode key={i} name={f.path} type={f.type} depth={0} />
              ))}
            </div>
          )}
        </div>

        {/* AST Detail View */}
        <div className="col-span-2 bg-[#111] border border-[#333] rounded-xl p-6 h-[80vh] overflow-y-auto">
          <div className="flex items-center gap-3 mb-6 border-b border-[#222] pb-4">
            <div className="h-10 w-10 bg-blue-900/20 rounded flex items-center justify-center text-blue-500 font-mono font-bold">
              PY
            </div>
            <div>
              <h2 className="text-lg font-semibold text-white">src/main.py</h2>
              <p className="text-sm text-gray-500">SHA: 8a9f...2b1</p>
            </div>
          </div>

          <div className="space-y-6">
            <div className="bg-black border border-[#222] rounded-lg p-4">
              <h4 className="text-sm font-medium text-blue-400 mb-2">
                Function Definition: `process_payment`
              </h4>
              <div className="pl-4 border-l-2 border-blue-900/50 space-y-2">
                <div className="text-sm text-gray-400 font-mono">
                  args: amount, currency
                </div>
                <div className="text-sm text-gray-400 font-mono">
                  returns: TransactionResult
                </div>
                <div className="mt-2 flex gap-2">
                  <span className="text-[10px] bg-green-900/30 text-green-400 px-2 py-0.5 rounded border border-green-900/50">
                    Compliance Check: Passed
                  </span>
                  <span className="text-[10px] bg-purple-900/30 text-purple-400 px-2 py-0.5 rounded border border-purple-900/50">
                    Tag: Payments
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-black border border-[#222] rounded-lg p-4">
              <h4 className="text-sm font-medium text-blue-400 mb-2">
                Import: `stripe`
              </h4>
              <div className="pl-4 border-l-2 border-blue-900/50">
                <div className="text-sm text-gray-400 font-mono">
                  module: external
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
