"""Global CSS constants — injected once with shared=True in main.py."""

GLOBAL_CSS = """
<style>
  body { font-family: 'Inter', 'Segoe UI', sans-serif; }

  /* ── Sidebar ── */
  .rr-sidebar { background: #0b0f1a; min-height: 100vh; }
  .rr-nav-btn  { width: 100%; text-align: left; padding: 9px 14px;
                 border-radius: 6px; font-size: 13px; transition: background .15s; }
  .rr-nav-btn:hover  { background: rgba(59,130,246,.12) !important; }
  .rr-nav-active     { background: rgba(59,130,246,.2) !important;
                       color: #60a5fa !important; border-left: 3px solid #3b82f6 !important; }

  /* ── KPI cards ── */
  .rr-kpi { border-radius: 10px; padding: 18px 20px; min-width: 150px;
            border: 1px solid rgba(255,255,255,.06); }

  /* ── Badge chips ── */
  .rr-badge { display:inline-block; padding:2px 9px; border-radius:20px;
              font-size:11px; font-weight:700; color:#fff; letter-spacing:.02em; }

  /* ── Region selector buttons ── */
  .rr-region-btn {
    padding: 5px 13px; border-radius: 5px; font-size: 12px; font-weight: 600;
    border: 1px solid #334155; transition: all .12s ease; letter-spacing: .03em;
    line-height: 1.6; cursor: pointer; white-space: nowrap;
  }
  .rr-region-active {
    background: #2563eb !important; color: #fff !important;
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 2px rgba(59,130,246,.25), 0 2px 8px rgba(37,99,235,.3);
  }
  .rr-region-inactive {
    background: #131b2e !important; color: #64748b !important;
    border-color: #1e293b !important;
  }
  .rr-region-inactive:hover {
    background: #1e2d45 !important; color: #94a3b8 !important;
    border-color: #334155 !important;
  }

  /* ── Section card baseline ── */
  .rr-card  { border: 1px solid #1e293b; border-radius: 10px; }
  .rr-card-hdr { border-bottom: 1px solid #1e293b; padding-bottom: 10px; margin-bottom: 14px; }

  /* ── AI Console card ── */
  .rr-ai-card { background: #080d18 !important; border: 1px solid #312e81 !important; }
  .rr-ai-launch {
    background: linear-gradient(135deg, #4338ca, #7c3aed) !important;
    color: #fff !important; font-weight: 600 !important; border-radius: 7px !important;
    border: 1px solid #6d28d9 !important; width: 100%;
    letter-spacing: .03em; font-size: 13px !important;
    transition: opacity .15s !important;
  }
  .rr-ai-launch:hover { opacity: .9; }
  .rr-ai-launch:disabled { opacity: .4 !important; }

  /* ── Spinner badge ── */
  .rr-task-badge {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 4px 10px; border-radius: 5px;
    background: rgba(79,70,229,.18); border: 1px solid rgba(99,102,241,.3);
    font-size: 11px; font-weight: 600; color: #a5b4fc;
    letter-spacing: .04em;
  }

  /* ── AI Smart Alerts card ── */
  .rr-alert-card { background: #060d1a !important; border: 1px solid #193153 !important; }

  /* ── Frequency toggle buttons ── */
  .rr-freq-btn {
    padding: 6px 18px; border-radius: 5px; font-size: 12px; font-weight: 600;
    border: 1px solid; cursor: pointer; transition: all .12s; letter-spacing: .02em;
  }
  .rr-freq-btn-active {
    background: #1d4ed8 !important; color: #fff !important;
    border-color: #3b82f6 !important; box-shadow: 0 0 0 2px rgba(59,130,246,.2);
  }
  .rr-freq-btn-inactive {
    background: #0b0f1a !important; color: #475569 !important;
    border-color: #1e293b !important;
  }

  /* ── Jurisdiction selection chips ── */
  .rr-jur-chip {
    padding: 3px 12px; border-radius: 20px; font-size: 11px; font-weight: 700;
    border: 1px solid; cursor: pointer; transition: all .12s; letter-spacing: .04em;
  }
  .rr-jur-active   { background: rgba(29,78,216,.18) !important; color: #60a5fa !important;
                     border-color: #1d4ed8 !important; }
  .rr-jur-inactive { background: #0b0f1a !important; color: #475569 !important;
                     border-color: #1e293b !important; }

  /* ── Version history timeline ── */
  .rr-timeline-item {
    border-left: 2px solid #1e293b; padding: 2px 0 18px 20px; position: relative;
  }
  .rr-timeline-item:last-child { padding-bottom: 2px; }
  .rr-timeline-dot {
    width: 10px; height: 10px; border-radius: 50%;
    position: absolute; left: -6px; top: 3px;
  }
  .rr-impact-pill {
    display: inline-block; padding: 2px 10px; border-radius: 20px;
    font-size: 10px; font-weight: 800; letter-spacing: .08em;
  }
  .rr-impact-critical { background:rgba(127,29,29,.25);  color:#fca5a5; border:1px solid rgba(220,38,38,.4); }
  .rr-impact-high     { background:rgba(220,38,38,.12);  color:#f87171; border:1px solid rgba(220,38,38,.3); }
  .rr-impact-medium   { background:rgba(217,119,6,.12);  color:#fbbf24; border:1px solid rgba(217,119,6,.3); }
  .rr-impact-low      { background:rgba(5,150,105,.12);  color:#34d399; border:1px solid rgba(5,150,105,.3); }
</style>
"""
