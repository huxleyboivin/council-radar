/* Council Radar "Window 2 clock": a timeline of the IESO LT2 Window 2 milestones with a "today" marker,
   a countdown, and (optionally) each council's next council meeting. Data: meta.lt2 from councils.json
   (source: data/lt2_timeline.json). Usage: CRClock.render(element, meta, {councils: [...council objects]}). */
(function () {
  "use strict";
  const css = `
  .clk{font-family:"Public Sans",system-ui,sans-serif;color:#1F2D44}
  .clk-top{display:flex;flex-wrap:wrap;gap:.8rem 2.2rem;margin:0 0 1.4rem}
  .clk-n strong{display:block;font:700 2.3rem/1.05 "Public Sans",system-ui,sans-serif;letter-spacing:-.02em;color:#14284B}
  .clk-n.main strong{color:#B23A3A}
  .clk-n span{display:block;font-size:.92rem;color:#52607A;max-width:17rem;margin-top:.25rem}
  .clk-track{position:relative;height:4.4rem;margin:0 .6rem 0}
  .clk-bar{position:absolute;left:0;right:0;top:1.2rem;height:6px;border-radius:99px;background:#D5DCE5}
  .clk-done{position:absolute;left:0;top:1.2rem;height:6px;border-radius:99px;background:#14284B}
  .clk-dot{position:absolute;top:.85rem;width:14px;height:14px;margin-left:-7px;border-radius:50%;background:#fff;border:3px solid #8FA3C3}
  .clk-dot.past{background:#14284B;border-color:#14284B}
  .clk-dot.key{width:20px;height:20px;margin-left:-10px;top:.68rem;border-color:#B23A3A;background:#fff;box-shadow:0 0 0 5px rgba(178,58,58,.15)}
  .clk-dot.approx{border-style:dashed}
  .clk-now{position:absolute;top:-.1rem;transform:translateX(-50%);font:700 .7rem/1 "Public Sans",sans-serif;letter-spacing:.06em;text-transform:uppercase;color:#fff;background:#2E7D4F;border-radius:4px;padding:.25rem .35rem;white-space:nowrap}
  .clk-now::after{content:"";position:absolute;left:50%;top:100%;margin-left:-4px;border:4px solid transparent;border-top-color:#2E7D4F}
  .clk-lab{position:absolute;top:2.35rem;transform:translateX(-50%);width:9.5rem;text-align:center;font-size:.8rem;line-height:1.3;color:#52607A}
  .clk-lab b{display:block;color:#14284B;font-weight:600}
  .clk-lab.first{transform:none;text-align:left;margin-left:-.6rem}.clk-lab.last{transform:translateX(-100%);text-align:right;margin-left:.6rem}
  .clk-list{display:none;list-style:none;margin:0;padding:0}
  .clk-list li{display:grid;grid-template-columns:1.1rem 1fr;gap:.6rem;padding:.4rem 0;font-size:.92rem;color:#52607A}
  .clk-list li i{width:12px;height:12px;border-radius:50%;border:3px solid #8FA3C3;margin-top:.3rem}
  .clk-list li.past i{background:#14284B;border-color:#14284B}.clk-list li.key i{border-color:#B23A3A}
  .clk-list b{color:#14284B;font-weight:600}
  .clk-list li.now{color:#2E7D4F;font-weight:700}.clk-list li.now i{background:#2E7D4F;border-color:#2E7D4F}
  .clk-mine{margin:2.6rem 0 0;border-top:1px solid #D5DCE5;padding-top:1rem}
  .clk-mine h4{margin:0 0 .4rem;font:700 .78rem/1 "Public Sans",sans-serif;letter-spacing:.07em;text-transform:uppercase;color:#52607A}
  .clk-mine ul{list-style:none;margin:0;padding:0}
  .clk-mine li{padding:.45rem 0;border-bottom:1px solid #EDF1F6;font-size:.95rem}
  .clk-mine li:last-child{border-bottom:0}
  .clk-mine li b{color:#14284B}
  .clk-mine li span{color:#52607A}
  .clk-foot{margin:1rem 0 0;font-size:.84rem;color:#52607A}
  .clk-foot a{font-weight:600}
  @media (max-width:640px){.clk-track{display:none}.clk-list{display:block}.clk-mine{margin-top:1rem}.clk-n strong{font-size:1.9rem}}`;
  document.head.insertAdjacentHTML("beforeend", `<style>${css}</style>`);
  const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]));
  const day = s => new Date(s + "T12:00:00");
  function span(from, to) {
    const days = Math.round((to - from) / 864e5);
    if (days <= 0) return null;
    if (days < 21) return days + (days === 1 ? " day" : " days");
    if (days < 60) return "about " + Math.round(days / 7) + " weeks";
    return "about " + Math.round(days / 30.44) + " months";
  }
  function render(el, meta, opts) {
    const lt2 = meta && meta.lt2; if (!el || !lt2 || !lt2.milestones) return false;
    opts = opts || {};
    const ms = lt2.milestones, now = new Date(), t0 = day(ms[0].plot), t1 = day(ms[ms.length - 1].plot);
    const pos = d => Math.min(100, Math.max(0, (d - t0) / (t1 - t0) * 100));
    const due = ms.find(m => m.deadline) || ms[ms.length - 2], pre = ms.find(m => m.key === "pre");
    const dueIn = span(now, day(due.plot)), preIn = pre && span(now, day(pre.plot));
    let h = `<div class="clk"><div class="clk-top">`;
    h += dueIn ? `<div class="clk-n main"><strong>${esc(dueIn[0].toUpperCase() + dueIn.slice(1))}</strong><span>until ${esc(lt2.name)} proposals are due, each with council support (${esc(due.when)})</span></div>`
               : `<div class="clk-n main"><strong>Due now</strong><span>${esc(lt2.name)} proposals: ${esc(due.when)}</span></div>`;
    if (preIn) h += `<div class="clk-n"><strong>${esc(preIn[0].toUpperCase() + preIn.slice(1))}</strong><span>until pre-engagement with each municipality (${esc(pre.when)})</span></div>`;
    h += `</div><div class="clk-track" aria-hidden="true"><div class="clk-bar"></div><div class="clk-done" style="width:${pos(now)}%"></div>`;
    ms.forEach((m, i) => {
      const d = day(m.plot), cls = ["clk-dot", d <= now ? "past" : "", m.deadline ? "key" : "", m.approx ? "approx" : ""].join(" ");
      h += `<span class="${cls}" style="left:${pos(d)}%"></span>`;
      h += `<span class="clk-lab${i === 0 ? " first" : i === ms.length - 1 ? " last" : ""}" style="left:${pos(d)}%"><b>${esc(m.label)}</b>${esc(m.when)}</span>`;
    });
    h += `<span class="clk-now" style="left:${pos(now)}%">Today</span></div>`;
    // list version (phones and screen readers)
    let placed = false;
    h += `<ol class="clk-list">`;
    ms.forEach(m => {
      const d = day(m.plot);
      if (!placed && d > now) { h += `<li class="now"><i></i><span>Today</span></li>`; placed = true; }
      h += `<li class="${d <= now ? "past" : ""}${m.deadline ? " key" : ""}"><i></i><span><b>${esc(m.label)}</b>, ${esc(m.when)}</span></li>`;
    });
    h += `</ol>`;
    const cs = (opts.councils || []).filter(c => c && c.c);
    if (cs.length) {
      h += `<div class="clk-mine"><h4>${cs.length === 1 ? "Its next council meeting" : "Your councils' next council meetings"}</h4><ul>`;
      for (const c of cs.slice(0, 6)) {
        const m = (c.u || []).find(u => /council/i.test(u[0])) || (c.u || [])[0];
        h += `<li><b>${esc(c.n)}</b>: <span>${m ? `${esc(m[0])}, ${esc(m[1])}${m[2] ? ` · <a href="${esc(m[2])}" rel="nofollow" target="_blank">Agenda</a>` : ""}` : "no meeting posted yet"}</span></li>`;
      }
      h += `</ul></div>`;
    }
    const base = opts.base || "";
    const ics = new URL(base + "cal/lt2-window-2.ics", location.href).href, webcal = ics.replace(/^https?:/, "webcal:");
    const srcs = [...new Set(ms.map(m => m.source).filter(Boolean))];
    h += `<p class="clk-foot">The IESO's timeline is approximate and subject to change; we update these dates when it confirms them. `
       + `Add them to your calendar: <a href="https://outlook.office.com/calendar/0/addfromweb?url=${encodeURIComponent(ics)}&name=${encodeURIComponent(lt2.name + " milestones")}" target="_blank" rel="noopener">Outlook</a> · `
       + `<a href="https://calendar.google.com/calendar/r?cid=${encodeURIComponent(webcal)}" target="_blank" rel="noopener">Google</a> · <a href="${esc(webcal)}">Apple</a>. `
       + `Sources: ${srcs.map((s, i) => `<a href="${esc(s)}" rel="nofollow" target="_blank">${i + 1}</a>`).join(", ")}.</p></div>`;
    el.innerHTML = h;
    return true;
  }
  window.CRClock = {render, span};
})();
