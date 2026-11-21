/* Council Radar "plan of decisions": the hero drawing.
   Rural Ontario is surveyed into lots and concessions, and every support resolution has to identify its
   project's land. This draws a schematic survey plan (not a map: lots are not placed geographically) where
   each shaded parcel is a real, public council decision from councils.json, or a count of subscriber items.
   One radar sweep crosses the plan on load and lights each parcel as it passes; reduced motion skips it.
   Usage: CRPlan.render(el, data) ; CRPlan.highlight(councilObject | null). */
(function () {
  "use strict";
  const NS = "http://www.w3.org/2000/svg";
  const W = 536, H = 500;
  const X0 = 22, Y0 = 22, COLS = 5, ROWS = 4, LOT_W = 95, LOT_H = 82, ROAD = 15, SIDE = 15;
  const SIDE_AFTER = 3;                         // a sideroad between lot 3 and lot 4
  const KIND = {
    support_granted: ["Support given", "#2E7D4F"],
    support_denied: ["No support", "#B3412E"],
    policy_protocol: ["New rules", "#2F6FB5"],
    delegation: ["Early signal", "#A86F0E"],
    locked: ["Subscriber item", "#6A5BB5"],
  };
  // Where decisions land on the plan: a scatter that keeps parcels apart and reads well.
  const SPOTS = [[0, 3], [1, 1], [2, 4], [3, 2], [0, 0], [2, 0], [1, 4], [3, 4], [0, 2], [3, 0]];
  const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]));
  const fold = s => s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]+/g, " ").trim();
  const short = n => n.replace(/^(City|Town|Township|Municipality|Village|Regional Municipality|United Counties|Region) of /, "");
  const lotX = c => X0 + c * LOT_W + (c >= SIDE_AFTER ? SIDE : 0);
  const lotY = r => Y0 + r * (LOT_H + ROAD);
  let host = null, placed = [], free = [], pin = null;

  function lines(text, max) {
    const words = text.split(" "), out = [];
    let cur = "";
    for (const w of words) {
      if ((cur + " " + w).trim().length > max && cur) { out.push(cur); cur = w; } else cur = (cur + " " + w).trim();
    }
    if (cur) out.push(cur);
    return out.slice(0, 3);
  }

  function pick(data) {
    const out = [];
    for (const c of data.councils) {
      const items = c.i || [];
      if (items.length) {
        const latest = items[items.length - 1];
        out.push({c, kind: KIND[latest[0]] ? latest[0] : "policy_protocol", note: items.length > 1 ? `${items.length} public items` : latest[1]});
      }
    }
    for (const c of data.councils) {
      if (c.l && !(c.i || []).length) out.push({c, kind: "locked", note: `${c.l} in the Monday email`});
    }
    return out.slice(0, SPOTS.length);
  }

  function render(el, data) {
    if (!el || !data || !data.councils) return false;
    host = el;
    const parcels = pick(data);
    const used = new Set();
    let s = `<svg xmlns="${NS}" viewBox="0 0 ${W} ${H}" role="img" aria-labelledby="plan-t plan-d" class="plan-svg">`;
    s += `<title id="plan-t">Plan of energy decisions</title><desc id="plan-d">A schematic survey plan. Each shaded parcel is an Ontario council's public decision on energy projects, or a count of items in the subscriber email. Lots are not placed geographically.</desc>`;
    s += `<defs>`;
    for (const [k, [, col]] of Object.entries(KIND)) {
      s += `<pattern id="h-${k}" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="7" height="7" fill="${col}" fill-opacity=".07"/><line x1="0" y1="0" x2="0" y2="7" stroke="${col}" stroke-width="2.2" stroke-opacity=".55"/></pattern>`;
    }
    s += `</defs>`;
    // plan sheet
    s += `<rect x=".5" y=".5" width="${W - 1}" height="${H - 1}" fill="#fff" stroke="#14284B" stroke-width="1"/>`;
    s += `<rect x="8.5" y="8.5" width="${W - 17}" height="${H - 17}" fill="none" stroke="#14284B" stroke-width=".6" stroke-opacity=".5"/>`;
    // roads (concession road allowances and one sideroad)
    const gridR = lotX(COLS - 1) + LOT_W, gridB = lotY(ROWS - 1) + LOT_H;
    for (let r = 1; r < ROWS; r++) {
      const y = lotY(r) - ROAD;
      s += `<rect x="${X0}" y="${y}" width="${gridR - X0}" height="${ROAD}" fill="#F3F6FA"/>`;
      s += `<line x1="${X0}" y1="${y}" x2="${gridR}" y2="${y}" class="pl-road"/><line x1="${X0}" y1="${y + ROAD}" x2="${gridR}" y2="${y + ROAD}" class="pl-road"/>`;
      s += `<text x="${(X0 + lotX(SIDE_AFTER) - SIDE) / 2}" y="${y + ROAD / 2 + 3.2}" class="pl-roadname" text-anchor="middle">CONCESSION ROAD ${r * 2}</text>`;
      s += `<text x="${(lotX(SIDE_AFTER) + gridR) / 2}" y="${y + ROAD / 2 + 3.2}" class="pl-roadname" text-anchor="middle">CONCESSION ROAD ${r * 2}</text>`;
    }
    const sx = lotX(SIDE_AFTER) - SIDE;
    s += `<rect x="${sx}" y="${Y0}" width="${SIDE}" height="${gridB - Y0}" fill="#F3F6FA"/>`;
    s += `<line x1="${sx}" y1="${Y0}" x2="${sx}" y2="${gridB}" class="pl-road"/><line x1="${sx + SIDE}" y1="${Y0}" x2="${sx + SIDE}" y2="${gridB}" class="pl-road"/>`;
    s += `<text transform="translate(${sx + SIDE / 2 + 3.2} ${(Y0 + gridB) / 2}) rotate(-90)" class="pl-roadname" text-anchor="middle">SIDEROAD 15</text>`;
    // parcels
    placed = [];
    parcels.forEach((p, i) => {
      const [r, c] = SPOTS[i];
      used.add(r + "," + c);
      placed.push({r, c, p});
    });
    free = [];
    for (let r = 0; r < ROWS; r++) for (let c = 0; c < COLS; c++) if (!used.has(r + "," + c)) free.push([r, c]);
    // lots (numbers only where no parcel sits)
    let lotNo = 1;
    for (let r = 0; r < ROWS; r++) for (let c = 0; c < COLS; c++) {
      const x = lotX(c), y = lotY(r);
      s += `<rect x="${x}" y="${y}" width="${LOT_W}" height="${LOT_H}" class="pl-lot"/>`;
      if (!used.has(r + "," + c)) s += `<text x="${x + 7}" y="${y + 15}" class="pl-lotno">LOT ${lotNo}</text>`;
      lotNo++;
    }
    // radar: centred near the top-right of the plan
    const RX = gridR - 6, RY = Y0 + 6;
    s += `<g class="pl-rings" aria-hidden="true">${[120, 240, 360, 480].map(r => `<circle cx="${RX}" cy="${RY}" r="${r}" fill="none" stroke="#2F6FB5" stroke-opacity=".16" stroke-dasharray="2 5"/>`).join("")}</g>`;
    s += `<g id="pl-parcels">`;
    placed.forEach(({r, c, p}, i) => s += parcelSVG(r, c, p, i, RX, RY));
    s += `</g><g id="pl-pin"></g>`;
    const R = 640, a = -26 * Math.PI / 180;   // beam points east at 0deg; the faint trail sits just behind it
    s += `<g class="pl-sweep" style="transform-origin:${RX}px ${RY}px" aria-hidden="true"><path d="M${RX} ${RY} L${RX + R * Math.cos(a)} ${RY + R * Math.sin(a)} A${R} ${R} 0 0 1 ${RX + R} ${RY} Z" fill="#2F6FB5" fill-opacity=".1"/><line x1="${RX}" y1="${RY}" x2="${RX + R}" y2="${RY}" stroke="#2F6FB5" stroke-opacity=".55" stroke-width="1.4"/></g>`;
    s += `<circle cx="${RX}" cy="${RY}" r="4" fill="#14284B"/>`;
    // key (two columns) and title block, as on a registered plan
    const ky = gridB + 16;
    const kinds = [...new Set(parcels.map(p => p.kind))];
    kinds.forEach((k, i) => {
      const kx = X0 + (i % 2) * 118, kyy = ky + Math.floor(i / 2) * 17;
      s += `<rect x="${kx}" y="${kyy}" width="15" height="11" fill="url(#h-${k})" stroke="${KIND[k][1]}" stroke-width="1"/><text x="${kx + 21}" y="${kyy + 9.5}" class="pl-legend">${esc(KIND[k][0])}</text>`;
    });
    const m = data.meta || {};
    const tbx = X0 + 252, tby = gridB + 12, tbw = gridR - tbx, tbh = H - 18 - tby;
    const upd = new Date((m.built || "") + "T12:00:00").toLocaleDateString("en-CA", {month: "short", day: "numeric", year: "numeric"});
    s += `<g class="pl-title"><rect x="${tbx}" y="${tby}" width="${tbw}" height="${tbh}" fill="#fff" stroke="#14284B" stroke-width=".9"/>`;
    s += `<line x1="${tbx + 34}" y1="${tby}" x2="${tbx + 34}" y2="${tby + tbh}" stroke="#14284B" stroke-width=".6"/>`;
    s += `<g transform="translate(${tbx + 11} ${tby + 12})" aria-hidden="true"><path d="M6 0 L12 17 L6 13 L0 17 Z" fill="#14284B"/><text x="6" y="31" text-anchor="middle" class="pl-tb1">N</text></g>`;
    s += `<text x="${tbx + 44}" y="${tby + 18}" class="pl-tb1">PLAN OF ENERGY DECISIONS</text>`;
    s += `<text x="${tbx + 44}" y="${tby + 33}" class="pl-tb2">${esc(m.covered || 150)} Ontario councils, read daily</text>`;
    s += `<text x="${tbx + 44}" y="${tby + 46}" class="pl-tb2">Schematic, not to scale</text>`;
    s += `<text x="${tbx + 44}" y="${tby + 59}" class="pl-tb2">Updated ${esc(upd)}</text></g>`;
    s += `</svg>`;
    el.innerHTML = s;
    if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) el.classList.add("pl-animate");
    return true;
  }

  function parcelSVG(r, c, p, i, RX, RY, extra) {
    const x = lotX(c), y = lotY(r), [lab, col] = KIND[p.kind] || ["", "#14284B"];
    const name = lines(short(p.c.n), 11);
    const cx = x + LOT_W / 2, cy = y + LOT_H / 2;
    // The sweep turns clockwise from 75deg to 195deg (screen angles: 90 = south, 180 = west) over 2.4s;
    // each parcel lights when the beam reaches its bearing from the radar.
    const ang = (Math.atan2(cy - RY, cx - RX) * 180 / Math.PI + 360) % 360;
    const d = Math.min(2.4, Math.max(0, (ang - 75) / 120 * 2.4));
    const slug = fold(p.c.n).replace(/ /g, "-");
    let t = `<a href="councils/${slug}/" class="pl-parcel${extra ? " " + extra : ""}" data-n="${esc(p.c.n)}" style="--d:${d.toFixed(2)}s" aria-label="${esc(p.c.n)}: ${esc(lab)}, ${esc(p.note)}">`;
    t += `<title>${esc(p.c.n)}: ${esc(lab)}</title>`;
    t += `<rect x="${x + 3}" y="${y + 3}" width="${LOT_W - 6}" height="${LOT_H - 6}" fill="${p.kind === "pin" ? "#fff" : `url(#h-${p.kind})`}" stroke="${col}" stroke-width="1.6" ${p.kind === "pin" ? 'stroke-dasharray="4 3"' : ""}/>`;
    const ty = y + LOT_H - 10 - (name.length - 1) * 12.5 - 12;
    t += `<rect x="${x + 7}" y="${ty - 11}" width="${LOT_W - 14}" height="${name.length * 12.5 + 15}" fill="#fff" fill-opacity=".9"/>`;
    name.forEach((ln, k) => t += `<text x="${x + 10}" y="${ty + k * 12.5}" class="pl-name">${esc(ln)}</text>`);
    t += `<text x="${x + 10}" y="${ty + name.length * 12.5}" class="pl-kind" fill="${col}">${esc(lab)}</text>`;
    t += `</a>`;
    return t;
  }

  function highlight(c) {
    if (!host) return;
    host.querySelectorAll(".pl-parcel.hl").forEach(a => a.classList.remove("hl"));
    const pinG = host.querySelector("#pl-pin");
    if (pinG) pinG.innerHTML = "";
    if (!c) return;
    const hit = [...host.querySelectorAll(".pl-parcel")].find(a => a.dataset.n === c.n);
    if (hit) { hit.classList.add("hl"); return; }
    // Not on the plan: stake it out in an empty lot.
    const spot = free[(c.n.length * 7) % Math.max(1, free.length)];
    if (!spot || !pinG) return;
    KIND.pin = [c.c ? "Read daily" : "Not read yet", c.c ? "#14284B" : "#7F8DA3"];
    pinG.innerHTML = parcelSVG(spot[0], spot[1], {c, kind: "pin", note: KIND.pin[0]}, 0, 0, 0, "hl pin");
  }

  window.CRPlan = {render, highlight};
})();
