import { CheckCircle2, XCircle, AlertTriangle, Clock } from "lucide-react";

export interface ActivityItem {
  type: string;
  status: string;
  source: string;
  time: string;
  details: string | number;
}

interface RecentActivityProps {
  activities: ActivityItem[];
}

export function RecentActivity({ activities }: RecentActivityProps) {
  const getIcon = (type: string, status: string) => {
    if (status === "failed")
      return <XCircle className="h-5 w-5 text-red-500" />;
    if (status === "completed" || status === "success")
      return <CheckCircle2 className="h-5 w-5 text-green-500" />;
    if (status === "running" || status === "pending")
      return <Clock className="h-5 w-5 text-blue-500 animate-pulse" />;
    return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
  };

  const formatTime = (isoString: string) => {
    try {
      const date = new Date(isoString);
      const now = new Date();
      const diff = (now.getTime() - date.getTime()) / 1000; // seconds

      if (diff < 60) return "Just now";
      if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
      if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
      return date.toLocaleDateString();
    } catch {
      return isoString;
    }
  };

  if (!activities || activities.length === 0) {
    return (
      <div className="bg-[#111] border border-[#333] rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-6">
          Recent Activity
        </h3>
        <div className="text-gray-500 text-sm italic">
          No recent activity found.
        </div>
      </div>
    );
  }

  return (
    <div className="bg-[#111] border border-[#333] rounded-xl p-6">
      <h3 className="text-lg font-semibold text-white mb-6">Recent Activity</h3>
      <div className="space-y-6 relative before:absolute before:left-[19px] before:top-2 before:bottom-2 before:w-px before:bg-[#222]">
        {activities.map((item, i) => (
          <div key={i} className="relative flex gap-4 pl-2 group">
            <div className="bg-[#111] z-10 ring-4 ring-[#111] rounded-full">
              {getIcon(item.type, item.status)}
            </div>
            <div className="flex-1 pt-0.5">
              <div className="flex justify-between items-start">
                <h4 className="text-sm font-medium text-white group-hover:text-blue-400 transition-colors">
                  {item.source}
                </h4>
                <span className="text-xs text-gray-500 whitespace-nowrap ml-2">
                  {formatTime(item.time)}
                </span>
              </div>
              <p className="text-sm text-gray-400 mt-0.5">
                {item.type === "scan"
                  ? `${item.details || 0} violations detected`
                  : item.status}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
