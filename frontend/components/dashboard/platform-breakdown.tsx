import { Card } from "@/components/ui/card";
import type { PlatformBreakdown } from "@/lib/types";
import {
  formatCompactNumber,
  formatCurrency,
  getPlatformColor,
  getPlatformLabel,
} from "@/lib/utils";

const platformIcons: Record<string, string> = {
  meta: "M",
  google: "G",
  taboola: "T",
  tiktok: "TK",
};

export function PlatformBreakdownCard({
  platform,
  data,
}: {
  platform: string;
  data: PlatformBreakdown;
}) {
  const color = getPlatformColor(platform).replace("text-", "");
  const bgClass = `bg-${color.split("-")[0]}-50`;
  const textClass = `text-${color.split("-")[0]}-600`;

  return (
    <Card className="p-4">
      <div className="flex items-center gap-3">
        <div
          className={`flex h-10 w-10 items-center justify-center rounded-lg font-bold text-sm ${bgClass} ${textClass}`}
        >
          {platformIcons[platform] || platform.slice(0, 2).toUpperCase()}
        </div>
        <div>
          <p className="text-sm font-semibold text-gray-900">
            {getPlatformLabel(platform)}
          </p>
          <p className="text-xs text-gray-500">{data.count} campaigns</p>
        </div>
      </div>
      <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
        <div>
          <p className="text-xs text-gray-500">Impressions</p>
          <p className="font-medium text-gray-900">
            {formatCompactNumber(data.impressions)}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Clicks</p>
          <p className="font-medium text-gray-900">
            {formatCompactNumber(data.clicks)}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Conversions</p>
          <p className="font-medium text-gray-900">
            {formatCompactNumber(data.conversions)}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Spent</p>
          <p className="font-medium text-gray-900">
            {formatCurrency(data.spent)}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Revenue</p>
          <p className="font-medium text-gray-900">
            {formatCurrency(data.revenue)}
          </p>
        </div>
      </div>
    </Card>
  );
}
