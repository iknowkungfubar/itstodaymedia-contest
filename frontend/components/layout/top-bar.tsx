export function TopBar() {
  return (
    <header className="flex h-16 items-center justify-between border-b border-gray-200 bg-white px-6">
      <div>
        <h1 className="text-lg font-semibold text-gray-900">CampaignPulse</h1>
        <p className="text-sm text-gray-500">
          AI-Powered Campaign Intelligence
        </p>
      </div>
      <div className="flex items-center gap-4">
        <span className="inline-flex items-center rounded-full bg-green-50 px-2.5 py-0.5 text-xs font-medium text-green-700">
          ● Live Demo
        </span>
      </div>
    </header>
  );
}
