/* Council Radar "Start" panel.
   One place to start a free trial or subscribe, from any page. It replaces raw mailto: links, which do
   nothing for visitors without a desktop mail app (Outlook on the web, Gmail in a browser).
   Nothing typed here is stored or sent anywhere by this page: it only goes into the email the visitor
   sends, or into Stripe's checkout form.
   Pages can set window.CRStart = {context: () => ({councils: [...names], company: "..."})} before load. */
(function () {
  "use strict";
  const TO = "councilradaron@gmail.com";
  const PAID = "https://buy.stripe.com/eVqaEZ3ZGbwjc1Qdm38Vi00";
  const TEAM = "https://buy.stripe.com/4gM8wRfIo9ob4zobdV8Vi01";
  const cfg = window.CRStart = Object.assign({context: () => ({})}, window.CRStart || {});
  const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]));
  const fold = s => s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]+/g, " ").trim();
  const core = n => fold(n.replace(/^(City|Town|Township|Municipality|County|Village|Region|United Counties|Regional Municipality) of /, "").replace(/ County$/, ""));

  const css = `
  .crs-dock{position:fixed;right:1.25rem;bottom:1.25rem;z-index:40;display:flex;align-items:center;gap:.8rem;background:#14284B;color:#fff;border-radius:14px;padding:.6rem .6rem .6rem 1rem;box-shadow:0 20px 40px -18px rgba(10,20,40,.6);font:500 .95rem/1.3 "Public Sans",system-ui,sans-serif;transform:translateY(140%);transition:transform .3s ease}
  .crs-dock.on{transform:none}
  .crs-dock b{font-weight:700}
  .crs-dock small{display:block;color:#AFC0DA;font-size:.8rem}
  .crs-dock button{font:700 .95rem/1 "Public Sans",system-ui,sans-serif;background:#fff;color:#14284B;border:0;border-radius:9px;padding:.75rem 1rem;cursor:pointer;white-space:nowrap}
  .crs{border:0;padding:0;margin:0 0 0 auto;height:100%;max-height:100%;width:min(30rem,100%);max-width:100%;background:#fff;color:#1F2D44;font:400 1rem/1.55 "Public Sans",system-ui,sans-serif;box-shadow:-20px 0 60px -20px rgba(10,20,40,.5)}
  .crs[open]{animation:crs-in .28s ease-out}
  @keyframes crs-in{from{transform:translateX(30px);opacity:0}to{transform:none;opacity:1}}
  .crs::backdrop{background:rgba(12,22,42,.45)}
  .crs-in{display:flex;flex-direction:column;min-height:100%}
  .crs-h{display:flex;align-items:flex-start;gap:1rem;padding:1.4rem 1.5rem 1rem;border-bottom:1px solid #D5DCE5}
  .crs-h h2{margin:0;font:700 1.35rem/1.25 "Public Sans",system-ui,sans-serif;color:#14284B;letter-spacing:-.01em}
  .crs-h p{margin:.3rem 0 0;color:#52607A;font-size:.95rem}
  .crs-x{margin-left:auto;background:none;border:0;font-size:1.6rem;line-height:1;color:#52607A;cursor:pointer;padding:.1rem .3rem;border-radius:6px}
  .crs-b{padding:1.2rem 1.5rem 1.5rem;flex:1}
  .crs-step{display:flex;gap:.6rem;align-items:center;font:700 .78rem/1 "Public Sans",system-ui,sans-serif;letter-spacing:.07em;text-transform:uppercase;color:#52607A;margin:1.2rem 0 .6rem}
  .crs-step:first-child{margin-top:0}
  .crs-step i{font-style:normal;display:inline-grid;place-items:center;width:1.45rem;height:1.45rem;border-radius:50%;background:#14284B;color:#fff;font-size:.78rem;letter-spacing:0}
  .crs-chips{list-style:none;margin:0 0 .6rem;padding:0;display:flex;flex-wrap:wrap;gap:.4rem}
  .crs-chips li{display:inline-flex;align-items:center;gap:.3rem;background:#EEF3F8;border:1px solid #D5DCE5;border-radius:999px;padding:.28rem .35rem .28rem .7rem;font-size:.9rem;color:#14284B}
  .crs-chips li.off{border-style:dashed}
  .crs-chips button{border:0;background:none;color:#52607A;font-size:1.05rem;line-height:1;cursor:pointer;padding:0 .2rem}
  .crs input{width:100%;font:500 1rem/1.2 "Public Sans",system-ui,sans-serif;color:#14284B;padding:.7rem .75rem;border:1.5px solid #9AA8BD;border-radius:8px;background:#fff}
  .crs input:focus{outline:0;border-color:#14284B;box-shadow:0 0 0 3px rgba(47,111,181,.22)}
  .crs label{display:block;font-size:.88rem;color:#52607A;margin:.7rem 0 .3rem}
  .crs .crs-two{display:grid;grid-template-columns:1fr 1fr;gap:.7rem}
  .crs .crs-two label{margin-top:.7rem}
  .crs-send{display:grid;grid-template-columns:1fr 1fr;gap:.5rem;margin-top:.2rem}
  .crs-send a,.crs-send button,.crs-pay a{display:flex;align-items:center;justify-content:center;gap:.45rem;text-align:center;font:600 .95rem/1.2 "Public Sans",system-ui,sans-serif;text-decoration:none;border-radius:9px;padding:.8rem .7rem;border:1.5px solid #14284B;cursor:pointer;background:#fff;color:#14284B}
  .crs-send .main{grid-column:1/-1;order:-1;background:#14284B;color:#fff;font-size:1.02rem;padding:.95rem}
  .crs-send a:hover,.crs-send button:hover{background:#EEF3F8}.crs-send .main:hover{background:#0d1c36}
  .crs [aria-disabled="true"]{opacity:.45;pointer-events:none}
  .crs-hint{font-size:.85rem;color:#52607A;margin:.55rem 0 0}
  .crs-ok{font-size:.88rem;color:#2E7D4F;margin:.5rem 0 0;min-height:1.2em}
  .crs-or{display:flex;align-items:center;gap:.8rem;color:#52607A;font-size:.85rem;margin:1.4rem 0 .8rem}
  .crs-or::before,.crs-or::after{content:"";flex:1;height:1px;background:#D5DCE5}
  .crs-pay{display:grid;gap:.5rem}
  .crs-pay a{flex-direction:column;gap:.15rem}
  .crs-pay a.paid{background:#EEF3F8;border-color:#EEF3F8}
  .crs-pay a.paid:hover{border-color:#14284B}
  .crs-pay small{display:block;font-weight:500;color:#52607A;font-size:.82rem}
  .crs-f{padding:1rem 1.5rem 1.4rem;border-top:1px solid #D5DCE5;font-size:.82rem;color:#52607A}
  @media (max-width:640px){.crs{width:100%;margin:0}.crs-dock{left:.75rem;right:.75rem;bottom:.75rem;justify-content:space-between}}
  @media (prefers-reduced-motion: reduce){.crs[open]{animation:none}.crs-dock{transition:none}}`;
  document.head.insertAdjacentHTML("beforeend", `<style>${css}</style>`);

  // ---- council names (for the "add a council" box) ----
  let ALL = null;
  function councils() {
    if (ALL) return Promise.resolve(ALL);
    const inline = document.getElementById("council-data");
    if (inline) { try { ALL = JSON.parse(inline.textContent).councils; return Promise.resolve(ALL); } catch (e) {} }
    const base = (document.querySelector('script[src$="start.js"]') || {}).src || location.href;
    return fetch(new URL("councils.json", base)).then(r => r.json()).then(d => (ALL = d.councils)).catch(() => (ALL = []));
  }

  // ---- the panel ----
  const dlg = document.createElement("dialog");
  dlg.className = "crs"; dlg.setAttribute("aria-labelledby", "crs-title");
  dlg.innerHTML = `<div class="crs-in"><div class="crs-h"><div><h2 id="crs-title">Get your first issue free</h2>
    <p>Pick your councils and we'll send a trial Monday email that covers them. No payment, no account.</p></div>
    <button type="button" class="crs-x" data-crs-close aria-label="Close">×</button></div>
    <div class="crs-b">
      <p class="crs-step"><i>1</i>Your councils</p>
      <ul class="crs-chips" id="crs-chips"></ul>
      <input id="crs-add" list="crs-list" placeholder="Add a council, e.g. Haldimand" autocomplete="off" aria-label="Add a council">
      <datalist id="crs-list"></datalist>
      <p class="crs-step"><i>2</i>Where to send it</p>
      <label for="crs-email">Work email</label>
      <input id="crs-email" type="email" autocomplete="email" placeholder="you@company.com" required>
      <div class="crs-two"><div><label for="crs-co">Company</label><input id="crs-co" autocomplete="organization"></div>
        <div><label for="crs-role">Role <span style="font-weight:400">(optional)</span></label><input id="crs-role" autocomplete="organization-title"></div></div>
      <p class="crs-step"><i>3</i>Send your request</p>
      <div class="crs-send">
        <a id="crs-mailto" class="main">Open in my email app</a>
        <a id="crs-gmail" target="_blank" rel="noopener">Gmail</a>
        <a id="crs-outlook" target="_blank" rel="noopener">Outlook on the web</a>
        <button type="button" id="crs-copy" style="grid-column:1/-1">Copy the request instead</button>
      </div>
      <p class="crs-hint" id="crs-hint">It sends from your own email, so you can reply to Huxley directly. You'll hear back within one business day.</p>
      <p class="crs-ok" id="crs-ok" role="status"></p>
      <p class="crs-or">or skip the trial</p>
      <div class="crs-pay">
        <a class="paid" id="crs-paid">Subscribe for $59 a month <small>Founding rate, first 25 subscribers</small></a>
        <a class="paid" id="crs-team">Team of up to 5 for $249 a month</a>
      </div>
    </div>
    <p class="crs-f">Nothing you type here is stored. It goes only into the email you send, or into Stripe's secure checkout. Cancel any time.</p></div>`;
  document.body.appendChild(dlg);
  const $ = id => dlg.querySelector("#" + id);
  let picked = [], company = "", lastFocus = null, src = "site";

  const valid = () => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test($("crs-email").value.trim());
  function compose() {
    const email = $("crs-email").value.trim(), co = $("crs-co").value.trim(), role = $("crs-role").value.trim();
    const byName = Object.fromEntries((ALL || []).map(c => [c.n, c]));
    const lines = picked.length ? picked.map(n => "- " + n + (byName[n] && !byName[n].c ? " (not read yet, please add it)" : "")).join("\n") : "- (I'll tell you which councils)";
    const subject = `Free trial: ${co || email || "Council Radar"} (${picked.length || "?"} ${picked.length === 1 ? "council" : "councils"})`;
    const body = `Hi Huxley,\n\nI'd like a free trial issue of Council Radar.\n\nCouncils:\n${lines}\n\nEmail: ${email}\nCompany: ${co}\nRole: ${role}\n\n(Sent from the Council Radar site: ${src})`;
    return {subject, body, email};
  }
  function refresh() {
    $("crs-chips").innerHTML = picked.length
      ? picked.map((n, i) => `<li>${esc(n)}<button type="button" data-crs-rm="${i}" aria-label="Remove ${esc(n)}">×</button></li>`).join("")
      : `<li class="off">No councils yet: add one below, or leave it and tell Huxley in the email</li>`;
    const {subject, body, email} = compose(), e = encodeURIComponent, ok = valid();
    $("crs-gmail").href = `https://mail.google.com/mail/?view=cm&fs=1&to=${TO}&su=${e(subject)}&body=${e(body)}`;
    $("crs-outlook").href = `https://outlook.office.com/mail/deeplink/compose?to=${TO}&subject=${e(subject)}&body=${e(body)}`;
    $("crs-mailto").href = `mailto:${TO}?subject=${e(subject)}&body=${e(body)}`;
    ["crs-gmail", "crs-outlook", "crs-mailto", "crs-copy"].forEach(id => $(id).setAttribute("aria-disabled", String(!ok)));
    // Lead with the tool they most likely use: Gmail for Gmail addresses, the email app (usually Outlook) otherwise.
    const gmail = /@(gmail|googlemail)\.com$/i.test(email);
    $("crs-gmail").classList.toggle("main", gmail); $("crs-mailto").classList.toggle("main", !gmail);
    $("crs-gmail").textContent = gmail ? "Send with Gmail" : "Gmail";
    $("crs-mailto").textContent = gmail ? "Email app" : "Open in my email app";
    $("crs-hint").textContent = ok ? "It sends from your own email, so you can reply to Huxley directly. You'll hear back within one business day." : "Enter your work email to continue.";
    const ref = ("s_" + picked.map(n => core(n).replace(/ /g, "-")).join("_")).slice(0, 200);
    const q = (email && ok ? "prefilled_email=" + e(email) + "&" : "") + (picked.length ? "client_reference_id=" + e(ref) : "");
    $("crs-paid").href = PAID + (q ? "?" + q.replace(/&$/, "") : "");
    $("crs-team").href = TEAM + (q ? "?" + q.replace(/&$/, "") : "");
  }
  function add(v) {
    v = (v || "").trim(); if (!v) return;
    const list = ALL || [];
    const c = list.find(x => x.n === v) || list.find(x => fold(x.n) === fold(v)) || list.filter(x => core(x.n) === fold(v)).sort((a, b) => (b.c || 0) - (a.c || 0))[0];
    const name = c ? c.n : v;
    if (!picked.includes(name)) picked.push(name);
    $("crs-add").value = ""; refresh();
  }

  function open(opts) {
    opts = opts || {};
    const ctx = Object.assign({}, cfg.context() || {}, opts);
    picked = [...new Set(ctx.councils || [])]; company = ctx.company || "";
    src = ctx.source || location.pathname.split("/").pop() || "index.html";
    if (company && !$("crs-co").value) $("crs-co").value = company;
    lastFocus = document.activeElement;
    refresh();
    councils().then(list => { $("crs-list").innerHTML = list.map(c => `<option value="${esc(c.n)}">`).join(""); refresh(); });
    if (typeof dlg.showModal === "function") dlg.showModal(); else dlg.setAttribute("open", "");
    setTimeout(() => ($("crs-email").value ? dlg.querySelector(".crs-send .main") : $("crs-email")).focus(), 30);
  }
  function close() { dlg.close ? dlg.close() : dlg.removeAttribute("open"); }
  dlg.addEventListener("close", () => { if (lastFocus && lastFocus.focus) lastFocus.focus(); });
  dlg.addEventListener("click", e => {
    if (e.target === dlg) return close();                         // click on the backdrop
    if (e.target.closest("[data-crs-close]")) return close();
    const rm = e.target.closest("[data-crs-rm]"); if (rm) { picked.splice(+rm.dataset.crsRm, 1); refresh(); }
  });
  ["crs-email", "crs-co", "crs-role"].forEach(id => $(id).addEventListener("input", refresh));
  $("crs-add").addEventListener("change", () => add($("crs-add").value));
  $("crs-add").addEventListener("keydown", e => { if (e.key === "Enter") { e.preventDefault(); add($("crs-add").value); } });
  ["crs-gmail", "crs-outlook", "crs-mailto"].forEach(id => $(id).addEventListener("click", () => {
    $("crs-ok").textContent = "Your email should be open with everything filled in. Press send, and you're done.";
  }));
  $("crs-copy").addEventListener("click", async () => {
    const {subject, body} = compose(), text = `To: ${TO}\nSubject: ${subject}\n\n${body}`;
    try { await navigator.clipboard.writeText(text); $("crs-ok").textContent = `Copied. Paste it into a new email to ${TO}.`; }
    catch (e) { $("crs-ok").textContent = `Email ${TO} with: ${subject}`; }
  });

  // Every trial link on the site opens the panel; without JavaScript they still work as mailto links.
  document.addEventListener("click", e => {
    const a = e.target.closest(`a[href^="mailto:${TO}?subject="], [data-start]`);
    if (!a || dlg.contains(a) || e.defaultPrevented || e.metaKey || e.ctrlKey || e.shiftKey) return;
    e.preventDefault();
    open(a.dataset.councils ? {councils: a.dataset.councils.split("|")} : {});
  });

  // Optional dock: shown by pages that call CRStart.dock(n) (e.g. once a watchlist exists).
  const dock = document.createElement("div");
  dock.className = "crs-dock"; dock.setAttribute("role", "region"); dock.setAttribute("aria-label", "Your councils");
  dock.innerHTML = `<div><b id="crs-dock-n"></b><small>First Monday email free</small></div><button type="button" data-start>Start free</button>`;
  document.body.appendChild(dock);
  let dockN = 0, dockHidden = false;
  cfg.dock = function (n, hide) {
    dockN = n; if (hide !== undefined) dockHidden = hide;
    dock.querySelector("#crs-dock-n").textContent = n === 1 ? "1 council picked" : `${n} councils picked`;
    dock.classList.toggle("on", n > 0 && !dockHidden && !dlg.open);
  };
  dlg.addEventListener("close", () => cfg.dock(dockN));
  new MutationObserver(() => dock.classList.toggle("on", dockN > 0 && !dockHidden && !dlg.open)).observe(dlg, {attributes: true, attributeFilter: ["open"]});
  cfg.open = open;
  if (typeof cfg.onReady === "function") cfg.onReady();
})();
