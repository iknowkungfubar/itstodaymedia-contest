import {
  AlertTriangle,
  Bell,
  Info,
  Lightbulb,
  TrendingUp,
} from "lucide-react";
import Link from "next/link";
import type { Insight } from "@/lib/types";
import { formatDate, getSeverityColor } from "@/lib/utils";

const typeIcons: Record<string, React.ReactNode> = {
  anomaly: <AlertTriangle className="h-4 w-4" />,
  recommendation: <TrendingUp className="h-4 w-4" />,
  insight: <Lightbulb className="h-4 w-4" />,
  alert: <Bell className="h-4 w-4" />,
};

export function RecentInsights({ insights }: { insights: Insight[] }) {
  if (insights.length === 0) {
    return (
      <div className="py-8 text-center">
        <Info className="mx-auto h-8 w-8 text-gray-400" />
        <p className="mt-2 text-sm text-gray-500">No insights yet</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {insights.slice(0, 5).map((insight) => (
        <div
          key={insight.id}
          className={`rounded-lg border p-3 ${getSeverityColor(insight.severity)}`}
        >
          <div className="flex items-start gap-2">
            <div className="mt-0.5 shrink-0">
              {typeIcons[insight.type] || <Info className="h-4 w-4" />}
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium leading-tight">
                {insight.title}
              </p>
              <p className="mt-1 text-xs opacity-80 line-clamp-2">
                {insight.description}
              </p>
              <p className="mt-1 text-[10px] opacity-60">
                {formatDate(insight.created_at)}
                {insight.platform && ` · ${insight.platform}`}
              </p>
            </div>
          </div>
        </div>
      ))}
      <Link
        href="/insights"
        className="block text-center text-sm font-medium text-blue-600 hover:text-blue-700"
      >
        View all insights →
      </Link>
    </div>
  );
}
