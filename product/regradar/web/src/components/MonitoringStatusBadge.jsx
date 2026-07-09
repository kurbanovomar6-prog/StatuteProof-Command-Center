import { useEffect, useState } from "react";

// Truthful monitoring badge (eval finding N3). "Monitoring active" may only
// render when /api/health reports a run within the freshness window;
// otherwise the badge states the honest configured-but-pending status.
// Never claims active on fetch failure.

const FRESH_WINDOW_MS = 24 * 60 * 60 * 1000;

export default function MonitoringStatusBadge() {
  const [active, setActive] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetch("/api/health")
      .then((r) => (r.ok ? r.json() : null))
      .then((h) => {
        if (cancelled || !h || !h.last_run_at) return;
        const ts = Date.parse(h.last_run_at);
        if (Number.isFinite(ts) && Date.now() - ts < FRESH_WINDOW_MS) {
          setActive(true);
        }
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  if (active) {
    return (
      <div className="inline-flex items-center gap-2 text-sm font-medium text-emerald-300">
        <span className="sp-live-dot" />
        Monitoring active
      </div>
    );
  }
  return (
    <div className="inline-flex items-center gap-2 text-sm font-medium text-slate-300">
      <span className="h-2 w-2 rounded-full bg-slate-500" />
      Monitoring configured — activation pending
    </div>
  );
}
