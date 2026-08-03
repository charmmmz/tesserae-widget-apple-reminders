// Apple Reminders widget for Tesserae.
// Derived from Reminders, Fridge by Kayden D'Mello at revision 89edb0e;
// modified by Charm beginning 2026-08-03. AGPL-3.0-or-later.

function escapeHtml(value) {
  return String(value ?? "").replace(
    /[&<>"']/g,
    (character) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        character
      ],
  );
}

function countLabelHtml(value) {
  return String(value || "Items")
    .trim()
    .split(/\s+/)
    .map(escapeHtml)
    .join("<br>");
}

function stateBadge(state, updated) {
  const stale = state === "stale";
  const label = updated
    ? `${stale ? "Stale" : "Fresh"} · ${escapeHtml(updated)}`
    : stale
      ? "Stale"
      : "Fresh";
  return `<span class="ar-state ${stale ? "is-stale" : "is-fresh"}"><span class="ar-dot"></span>${label}</span>`;
}

const STYLE = `
  .w[data-widget="apple_reminders"] { padding: 0; }
  .apple-reminders {
    --ar-accent: var(--accent-1);
    height: 100%; display: flex; flex-direction: column;
    border: max(3px, 0.5cqmin) solid var(--text-primary);
    border-radius: var(--cell-corner-radius, var(--radius-0));
    overflow: hidden; container-type: size;
  }
  .apple-reminders.is-dim { opacity: 0.72; }
  .apple-reminders.is-muted { --ar-accent: var(--text-muted); }
  .ar-head { display: flex; align-items: stretch; border-bottom: max(3px, 0.5cqmin) solid var(--text-primary); }
  .ar-count {
    background: var(--ar-accent); color: var(--on-accent);
    display: flex; align-items: baseline; gap: 0.4em; padding: 0.5em 0.7em;
    border-right: max(3px, 0.5cqmin) solid var(--text-primary);
  }
  .ar-num { font-size: clamp(1.6em, 15cqmin, 4em); font-weight: var(--fw-black); line-height: 0.85; letter-spacing: -0.03em; font-variant-numeric: tabular-nums; }
  .ar-lab { font-size: 0.62em; font-weight: var(--fw-black); letter-spacing: 0.06em; text-transform: uppercase; line-height: 1.05; }
  .ar-meta { flex: 1; min-width: 0; display: flex; flex-direction: column; justify-content: center; gap: 0.15em; padding: 0.4em 0.7em; }
  .ar-title { font-size: 0.82em; font-weight: var(--fw-black); letter-spacing: 0.02em; text-transform: uppercase; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .ar-state { display: inline-flex; align-items: center; gap: 0.4em; font-size: 0.6em; font-weight: var(--fw-bold); letter-spacing: 0.04em; color: var(--text-muted); }
  .ar-dot { width: 0.62em; height: 0.62em; border-radius: 50%; background: var(--accent-3); flex: 0 0 auto; }
  .ar-state.is-stale .ar-dot { background: var(--accent-2); }
  .ar-list { flex: 1; min-height: 0; display: flex; flex-direction: column; padding: 0 0.7em; }
  .ar-list.is-two { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); grid-auto-rows: minmax(0, 1fr); column-gap: 0.65em; }
  .ar-row { display: flex; align-items: center; gap: 0.55em; padding: 0.34em 0.4em; border-left: max(4px, 0.65cqmin) solid transparent; border-bottom: max(1.5px, 0.28cqmin) solid color-mix(in oklab, var(--text-primary) 16%, transparent); flex: 1; min-height: 0; }
  .ar-list.is-two .ar-row:nth-last-child(-n + 2) { border-bottom-color: transparent; }
  .ar-box { flex: 0 0 auto; width: 0.9em; height: 0.9em; border: max(2px, 0.32cqmin) solid var(--text-primary); border-radius: 2px; }
  .ar-box.is-high { background: var(--ar-accent); border-color: var(--ar-accent); }
  .ar-name { flex: 1; min-width: 0; font-size: 0.86em; font-weight: var(--fw-bold); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .ar-due { flex: 0 0 auto; font-size: 0.62em; font-weight: var(--fw-black); letter-spacing: 0.03em; text-transform: uppercase; color: var(--text-muted); }
  .apple-reminders.due-relative .ar-due { font-size: 0.86em; letter-spacing: 0; text-transform: none; }
  .apple-reminders.use-urgency-colors .ar-row.is-overdue,
  .apple-reminders.use-urgency-colors .ar-row.is-today { border-left-color: var(--accent-1); }
  .apple-reminders.use-urgency-colors .ar-row.is-soon { border-left-color: var(--accent-2); }
  .apple-reminders.use-urgency-colors .ar-row.is-overdue .ar-due,
  .apple-reminders.use-urgency-colors .ar-row.is-today .ar-due { color: var(--accent-1); }
  .apple-reminders.use-urgency-colors .ar-row.is-soon .ar-due { color: color-mix(in oklab, var(--accent-2) 78%, var(--text-primary)); }
  .ar-more { font-size: 0.62em; font-weight: var(--fw-bold); color: var(--text-muted); padding: 0.3em 0; }
  .ar-blank { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 0.4em; color: var(--text-muted); text-align: center; padding: 0.8em; }
  .ar-blank i { font-size: 1.8em; }
  .ar-blank .msg { font-size: 0.82em; font-weight: var(--fw-bold); }
  .ar-blank .sub { font-size: 0.68em; }
  @container (max-width: 210px) {
    .ar-due, .ar-lab { display: none; }
    .ar-list.is-two { display: flex; }
  }
`;

export default function render(shadow, ctx) {
  const data = ctx?.data ?? {};
  const css = `<link rel="stylesheet" href="/static/style/spectra-widgets.css">`;
  const accent = `var(--${/^accent-[1-6]$/.test(data.accent) ? data.accent : "accent-1"})`;
  const style = `<style>${STYLE}</style>`;
  const framed = (inner, extra = "") =>
    `${css}${style}<div class="w" data-widget="apple_reminders"><div class="apple-reminders${extra}" style="--ar-accent:${accent}">${inner}</div></div>`;

  if (ctx?.fragment === "value") {
    shadow.innerHTML = `${css}<style>.fv{height:100%;display:flex;align-items:center;justify-content:center;background:${accent};color:var(--on-accent)}.fv b{font-size:clamp(2em,32cqmin,8em);font-weight:var(--fw-black);line-height:1;font-variant-numeric:tabular-nums}</style><div class="w" data-widget="apple_reminders"><div class="fv"><b>${data.count ?? 0}</b></div></div>`;
    return;
  }

  if (data.state === "expired") {
    shadow.innerHTML = framed(
      `<div class="ar-blank"><i class="ph-bold ph-clock-countdown"></i><span class="msg">Snapshot expired</span><span class="sub">Open Companion to sync Reminders again.</span></div>`,
      " is-muted",
    );
    return;
  }
  if (data.reason === "no_snapshot") {
    shadow.innerHTML = framed(
      `<div class="ar-blank"><i class="ph-bold ph-device-mobile"></i><span class="msg">No Reminders snapshot</span><span class="sub">Choose lists and sync them in Companion.</span></div>`,
      " is-muted",
    );
    return;
  }
  if (data.reason === "list_required") {
    shadow.innerHTML = framed(
      `<div class="ar-blank"><i class="ph-bold ph-list-checks"></i><span class="msg">Choose a Reminders list</span><span class="sub">Edit this cell after Companion uploads its selected lists.</span></div>`,
      " is-muted",
    );
    return;
  }
  if (data.reason === "list_missing") {
    shadow.innerHTML = framed(
      `<div class="ar-blank"><i class="ph-bold ph-warning-circle"></i><span class="msg">Selected list is unavailable</span><span class="sub">Restore it in Companion or choose another list.</span></div>`,
      " is-muted",
    );
    return;
  }

  const countLabel = countLabelHtml(data.count_label);
  const header = `<div class="ar-head"><div class="ar-count"><span class="ar-num">${data.count ?? 0}</span><span class="ar-lab">${countLabel}</span></div><div class="ar-meta"><span class="ar-title">${escapeHtml(data.title || "Reminders")}</span>${stateBadge(data.state, data.updated_label)}</div></div>`;
  const stateClasses = `${data.state === "stale" ? " is-dim" : ""}${data.urgency_colors ? " use-urgency-colors" : ""}${data.due_style === "relative" ? " due-relative" : ""}`;
  if (data.empty) {
    shadow.innerHTML = framed(
      `${header}<div class="ar-blank"><i class="ph-bold ph-check-circle"></i><span class="msg">Nothing left on this list</span></div>`,
      stateClasses,
    );
    return;
  }

  const items = Array.isArray(data.items) ? data.items : [];
  const rows = items
    .map(
      (item) =>
        `<div class="ar-row is-${escapeHtml(item.status || "undated")}"><span class="ar-box${item.high ? " is-high" : ""}"></span><span class="ar-name">${escapeHtml(item.title)}</span>${item.due ? `<span class="ar-due">${escapeHtml(item.due)}</span>` : ""}</div>`,
    )
    .join("");
  const more =
    (data.count ?? 0) > (data.shown ?? 0)
      ? `<div class="ar-more">+${data.count - data.shown} more</div>`
      : "";
  const listClass = data.columns === 2 ? " is-two" : "";
  shadow.innerHTML = framed(
    `${header}<div class="ar-list${listClass}">${rows}${more}</div>`,
    stateClasses,
  );
}
