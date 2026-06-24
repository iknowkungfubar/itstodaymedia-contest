import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Format currency */
export function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
  }).format(value);
}

/** Format percentage */
export function formatPercent(value: number): string {
  return `${value.toFixed(2)}%`;
}

/** Format large numbers with K/M suffix */
export function formatCompactNumber(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
  return value.toLocaleString();
}

/** Format a number with commas */
export function formatNumber(value: number): string {
  return value.toLocaleString();
}

/** Format ROAS */
export function formatRoas(value: number | null): string {
  if (value === null || value === undefined) return "N/A";
  return `${value.toFixed(2)}x`;
}

/** Get severity color for insights */
export function getSeverityColor(severity: string): string {
  const colors: Record<string, string> = {
    critical: "text-red-600 bg-red-50 border-red-200",
    high: "text-orange-600 bg-orange-50 border-orange-200",
    medium: "text-yellow-600 bg-yellow-50 border-yellow-200",
    low: "text-blue-600 bg-blue-50 border-blue-200",
    info: "text-gray-600 bg-gray-50 border-gray-200",
  };
  return colors[severity] || colors.info;
}

/** Get platform display color */
export function getPlatformColor(platform: string): string {
  const colors: Record<string, string> = {
    meta: "text-blue-600",
    google: "text-green-600",
    taboola: "text-purple-600",
    tiktok: "text-cyan-600",
  };
  return colors[platform] || "text-gray-600";
}

/** Get platform icon label */
export function getPlatformLabel(platform: string): string {
  const labels: Record<string, string> = {
    meta: "Meta",
    google: "Google",
    taboola: "Taboola",
    tiktok: "TikTok",
  };
  return labels[platform] || platform;
}

/** Format date */
export function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

/** Sanitize a URL for safe use as an href — rejects non-http(s) schemes. */
export function sanitizeUrl(url: string | null | undefined): string {
  if (!url) return "#";
  try {
    const parsed = new URL(url);
    if (parsed.protocol === "http:" || parsed.protocol === "https:") {
      return url;
    }
  } catch {
    // invalid URL — don't render a dangerous href
  }
  return "#";
}
