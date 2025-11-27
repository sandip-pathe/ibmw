import { ArrowDown, ArrowUp, ShieldCheck } from "lucide-react";

interface ComplianceScoreProps {
  score: number;
  trend: number; // positive means improved (score went up), negative means regressed
}

export function ComplianceScore({ score, trend }: ComplianceScoreProps) {
  const getColor = (s: number) => {
    if (s >= 90) return "text-green-500";
    if (s >= 70) return "text-yellow-500";
    return "text-red-500";
  };

  const getBgColor = (s: number) => {
    if (s >= 90) return "bg-green-500";
    if (s >= 70) return "bg-yellow-500";
    return "bg-red-500";
  };

  return (
    <div className="bg-[#111] border border-[#333] rounded-xl p-6 relative overflow-hidden">
      <div className="flex justify-between items-start mb-4">
        <div>
          <p className="text-sm text-gray-400 font-medium">Compliance Score</p>
          <h3 className={`text-4xl font-bold mt-1 ${getColor(score)}`}>
            {score}%
          </h3>
        </div>
        <div
          className={`h-12 w-12 rounded-full ${getBgColor(
            score
          )}/20 flex items-center justify-center`}
        >
          <ShieldCheck className={`h-6 w-6 ${getColor(score)}`} />
        </div>
      </div>

      <div className="flex items-center gap-2">
        {trend >= 0 ? (
          <div className="flex items-center text-green-400 text-sm bg-green-950/30 px-2 py-0.5 rounded">
            <ArrowUp className="h-3 w-3 mr-1" />
            {trend}%
          </div>
        ) : (
          <div className="flex items-center text-red-400 text-sm bg-red-950/30 px-2 py-0.5 rounded">
            <ArrowDown className="h-3 w-3 mr-1" />
            {Math.abs(trend)}%
          </div>
        )}
        <span className="text-xs text-gray-500">vs last scan</span>
      </div>

      {/* Progress Bar Visual */}
      <div className="w-full h-1.5 bg-[#222] rounded-full mt-4 overflow-hidden">
        <div
          className={`h-full rounded-full ${getBgColor(
            score
          )} transition-all duration-1000 ease-out`}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  );
}
