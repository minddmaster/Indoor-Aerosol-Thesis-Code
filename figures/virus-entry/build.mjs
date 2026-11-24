// Fig: how a virus enters a cell and replicates, drawn as an "infection bench".
// node build.mjs [--light]
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import * as k from "../../.claude/skills/anatomy/kit/iso-kit.mjs";
import { kitScript } from "../../.claude/skills/anatomy/scripts/inline-kit.mjs";
import * as M from "./model.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const theme = process.argv.includes("--light") ? "light" : "dark";
const WIDTH = 640;
const HEIGHT = 300;

// ---- world plan (x along the bench, y toward the viewer, z up) ----
const BASE = { x: -182, y: -50, w: 372, d: 104, r: 8 };
const BASE_H = 10;
const FOOT_H = 5;
const RIM_H = 7;
const RIM_T = 5;
const MEM_X = -100; // the membrane (left rim)
const EXIT_X = 150; // right rim
const RIM_FAR = -40;
const RIM_NEAR = 34;
const GAP = 14; // half-width of the gates
const POST_H = 44;
const RAIL_Y = [-5, 5];
const CAR = { x: -12, y: -7.5, w: 24, d: 15, r: 2 }; // carriage, built at x = 0
const CAR_Z = 2;
const CAR_TOP = 5;
// virion: capsid inside an envelope sleeve carrying spikes
const V = { R: 9.5, z: CAR_TOP, h: 16 };
const SPIKE = 4;
const RECEPTOR_ANGLE = Math.PI / 4;
const RECEPTORS = [-1, 1].map((side) => {
  const a = RECEPTOR_ANGLE * side;
  const reach = V.R + SPIKE + 1.6;
  return [M.DOCK_X + reach * Math.cos(a), reach * Math.sin(a)];
});
const SPIKE_Z = (v) => [v.z + v.h * 0.33, v.z + v.h * 0.72];
// ribosome, polymerase, rack, belt
const RIBO_SMALL = { x: -17, y: -8, w: 24, d: 16, r: 3 };
const RIBO_LARGE = { x: -19, y: -10, w: 28, d: 20, r: 5 };
const TAPE_Z = 15;
const PULLEY = [-38, 0];
const PULLEY_Z = 30;
const TRAY = { x: -20, y: 11, w: 28, d: 9, r: 1.5 };
const POLY_BASE = { x: 26, y: -12, w: 18, d: 24, r: 2 };
const ROLLERS = [[35, -5], [35, 5]];
const ROLLER_R = 3.6;
const RACK = { x: 56, y: -27, w: 46, d: 31, r: 3 };
const SPINDLES = [-20, -11, -2].flatMap((y) => [62, 73, 84, 95].map((x) => [x, y]));
const BELT = { x: 108, y: -6, w: 80, d: 12, r: 5.5 };
const BELT_TOP = 3;
const SMALL = { R: 6, z: BELT_TOP, h: 10 };
const RULER = { x: -160, y: 42, w: 322, d: 7, r: 1 };
const HOUR = 37.5;
const timeX = (t) => -150 + t * HOUR;

const P = k.fitProjection(
  [...k.boxCorners(BASE, -BASE_H - FOOT_H, 0), [MEM_X, -GAP - 3, POST_H + 3], [EXIT_X, -GAP - 3, 34]],
  WIDTH,
  HEIGHT,
  { pad: 12, azimuth: 70, elevation: 34 },
);

const at = (point) => k.iso(point, P);
const S = (paths, style = {}, station) => {
  const svg = k.solidSvg(paths, style);
  return station ? svg.replace("<g ", `<g data-station="${station}" `) : svg;
};
const L = (d, style) => k.lineSvg(d, style);
const D = (points, style) => k.dotsSvg(points, style);
const depth2 = ([x, y]) => k.depthOf([x, y, 0], P);
const byDepth = (points) => [...points].sort((a, b) => depth2(a) - depth2(b));
const viewer = k.towardViewer(P);
const facing = (a) => Math.cos(a) * viewer[0] + Math.sin(a) * viewer[1] > 0;

// ---------------- bench ----------------
function bench() {
  const out = [`<path class="iso-halo" d="${k.haloOf(BASE, -BASE_H - FOOT_H, BASE_H, P)}"/>`];
  for (const [x, y] of byDepth(k.corners(BASE, 20))) {
    out.push(S(k.cylinder(x, y, 7, -BASE_H - FOOT_H, 1.6, P, 28), { tone: "lo" }));
    out.push(S(k.cylinder(x, y, 5.4, -BASE_H - FOOT_H + 1.6, FOOT_H - 1.6, P, 28), { tone: "mid" }));
  }
  out.push(S(k.slabOf(BASE, -BASE_H, BASE_H, P, 8, 1.6), { tone: "mid" }));
  out.push(L(k.planOutline(k.insetPlan(BASE, 5), 0, P), { tone: "lo" }));
  const screws = k.corners(BASE, 10);
  out.push(L(screws.map(([x, y]) => k.ring(x, y, 2.2, 0, P, 16)).join(""), { tone: "lo" }));
  out.push(D(screws.map(([x, y]) => at([x, y, 0])), { size: 0.5 }));
  // hour ruler along the front edge: the clock of the figure
  out.push(S(k.slabOf(RULER, 0, 0.6, P, 3), { tone: "lo", crease: "none" }));
  const ticks = k.topTicks(timeX(0), timeX(M.END), HOUR / 4, 4, RULER.y + 0.6, 0.6, [1.8, 3.6], P);
  out.push(L(ticks.minor, { tone: "lo" }), L(ticks.major, { tone: "mid" }));
  out.push(L(k.lineOnTop([timeX(0), RULER.y + 0.6], [timeX(0), RULER.y + 5.2], 0.6, P), { tone: "hi" }));
  out.push(D([at([RULER.x + 3, RULER.y + 3.5, 0.6]), at([RULER.x + RULER.w - 3, RULER.y + 3.5, 0.6])], { size: 0.45 }));
  // label plate, front right
  const label = { x: 166, y: 36, w: 18, d: 12, r: 1 };
  out.push(S(k.slabOf(label, 0, 0.8, P, 4), { tone: "lo", crease: "none" }));
  out.push(L(k.planOutline(k.insetPlan(label, 1.6), 0.8, P, 4), { tone: "faint" }));
  [[3.5, 14], [6, 10], [8.5, 12]].forEach(([dy, len]) => out.push(L(k.lineOnTop([label.x + 2.5, label.y + dy], [label.x + 2.5 + len * 0.9, label.y + dy], 0.8, P), { tone: "lo", free: true })));
  // rails: outside approach through the gate to the cradle stop
  for (const y of RAIL_Y) {
    out.push(S(k.slabOf({ x: -176, y: y - 1.5, w: 128, d: 3, r: 0.8 }, 0, CAR_Z, P, 3, 0.3), { tone: "mid" }));
    out.push(D([-170, -140, -80, -56].map((x) => at([x, y, CAR_Z])), { size: 0.4 }));
  }
  out.push(S(k.slabOf({ x: -180, y: -9, w: 4, d: 18, r: 1 }, 0, 6, P, 3, 0.4), { tone: "mid" }));
  out.push(D([at([-178, -6, 6]), at([-178, 6, 6])], { size: 0.45 }));
  return out.join("");
}

// rim of the tray: the cell membrane
const rimX = (x, y0, y1) => ({ x: x - RIM_T / 2, y: y0, w: RIM_T, d: y1 - y0, r: 1 });
const rimY = (y, x0, x1) => ({ x: x0, y, w: x1 - x0, d: RIM_T, r: 1 });
const rim = (plan) => S(k.slabOf(plan, 0, RIM_H, P, 3, 0.5), { tone: "mid", inner: L(k.sideSeam(plan, 2.4, P, 3), { tone: "faint" }) });
const rimDots = (pts) => D(pts.map(([x, y]) => at([x, y, RIM_H])), { size: 0.45 });

function gatePost(x, y) {
  const out = [];
  out.push(S(k.slabOf({ x: x - 4, y: y - 4, w: 8, d: 8, r: 1.2 }, RIM_H, 3, P, 3, 0.4), { tone: "mid" }));
  out.push(S(k.slabOf({ x: x - 2.4, y: y - 2.4, w: 4.8, d: 4.8, r: 0.8 }, RIM_H + 3, POST_H - RIM_H - 3, P, 3), { tone: "mid", crease: "none", inner: L([18, 26, 34].map((z) => k.sideSeam({ x: x - 2.4, y: y - 2.4, w: 4.8, d: 4.8, r: 0.8 }, z, P, 3)).join(""), { tone: "faint" }) }));
  out.push(D([at([x - 2.6, y - 2.6, RIM_H + 3]), at([x + 2.6, y + 2.6, RIM_H + 3])], { size: 0.4 }));
  return out.join("");
}
function lintel(x, h = POST_H) {
  const plan = { x: x - 3.4, y: -GAP - 6.4, w: 6.8, d: GAP * 2 + 12.8, r: 1.2 };
  return S(k.slabOf(plan, h, 5, P, 3, 0.5), { tone: "mid" }) + D([at([x, -GAP - 3, h + 5]), at([x, GAP + 3, h + 5])], { size: 0.45 }) + L(k.planOutline(k.insetPlan(plan, 1.6), h + 5, P, 3), { tone: "faint" });
}
function shutter() {
  const plan = { x: MEM_X - 1.4, y: -GAP + 1.5, w: 2.8, d: GAP * 2 - 3, r: 0.4 };
  const slab = k.slabOf(plan, 0, 13, P, 2);
  const ribs = [3.5, 6.5, 9.5].map((z) => k.sideSeam(plan, z, P, 2)).join("");
  return S(slab, { tone: "mid", inner: L(ribs, { tone: "faint" }) }) + S(k.slabOf({ x: MEM_X - 2, y: -2.5, w: 4, d: 5, r: 0.8 }, 13, 2, P, 2), { tone: "mid" });
}
function receptor([x, y]) {
  const out = [];
  out.push(S(k.cylinder(x, y, 3.4, 0, 1.4, P, 20), { tone: "lo" }));
  out.push(S(k.cylinder(x, y, 1.1, 1.4, SPIKE_Z(V)[0] - 3.4, P, 14), { tone: "mid", crease: "none" }));
  out.push(S(k.cylinder(x, y, 2.4, SPIKE_Z(V)[0] - 2, 3.2, P, 20), { tone: "hi" }));
  out.push(L(k.ring(x, y, 1.1, SPIKE_Z(V)[0] + 1.2, P, 14), { tone: "lo" }));
  return out.join("");
}

// ---------------- virion ----------------
function spikesOf(v, front) {
  const out = [];
  const tips = [];
  SPIKE_Z(v).forEach((z, row) => {
    for (let i = 0; i < 12; i++) {
      const a = ((i + (row ? 0 : 0.5)) / 12) * Math.PI * 2 + (row ? 0 : 0);
      if (facing(a) !== front) continue;
      const len = v.R * (SPIKE / 9.5);
      const from = [Math.cos(a) * v.R, Math.sin(a) * v.R, z];
      const to = [Math.cos(a) * (v.R + len), Math.sin(a) * (v.R + len), z + 0.6];
      out.push(k.segment(from, to, P));
      tips.push(at(to));
    }
  });
  // crown of spikes on the shoulder
  for (let i = 0; i < 8; i++) {
    const a = (i / 8) * Math.PI * 2 + 0.2;
    if (facing(a) !== front) continue;
    const r0 = v.R - 0.6;
    const from = [Math.cos(a) * r0, Math.sin(a) * r0, v.z + v.h];
    const to = [Math.cos(a) * (r0 + v.R * 0.22), Math.sin(a) * (r0 + v.R * 0.22), v.z + v.h + v.R * 0.32];
    out.push(k.segment(from, to, P));
    tips.push(at(to));
  }
  return L(out.join(""), { tone: "mid" }) + D(tips, { size: v.R > 8 ? 0.95 : 0.7, tone: "hi" });
}
function capsidOf(v) {
  const r = v.R * 0.8;
  const out = [];
  out.push(S(k.cylinder(0, 0, r, v.z, v.h, P, 40, 0.5), { tone: "mid", crease: "lo", inner: L([0.3, 0.55, 0.8].map((f) => k.sideArc(0, 0, r, v.z + v.h * f, P, 24)).join(""), { tone: "faint" }) }, v.R > 8 ? "capsid" : undefined));
  out.push(L(k.ring(0, 0, r * 0.62, v.z + v.h, P, 28), { tone: "faint" }));
  out.push(D([at([0, 0, v.z + v.h])], { size: 0.7, tone: "hi" }));
  return out.join("");
}
function lidOf(v) {
  const r = v.R * 0.88;
  const top = v.z + v.h;
  return (
    S(k.cylinder(0, 0, r, top, v.R * 0.25, P, 40, 0.4), { tone: "mid" }) +
    L(k.knurl(0, 0, r, top, top + v.R * 0.25, 30, P, 0.3), { tone: "faint" }) +
    S(k.cylinder(0, 0, r * 0.3, top + v.R * 0.25, v.R * 0.2, P, 18), { tone: "mid" }) +
    D([0, 1, 2, 3].map((i) => at([Math.cos(i * 1.57 + 0.4) * r * 0.65, Math.sin(i * 1.57 + 0.4) * r * 0.65, top + v.R * 0.25])), { size: 0.4 })
  );
}
function envelopeOf(v, station) {
  const plan = k.cylinder(0, 0, v.R, v.z, v.h, P, 44, 0.5);
  return spikesOf(v, false) + S(plan, { tone: "mid", crease: "lo", inner: L(k.sideArc(0, 0, v.R, v.z + v.h * 0.5, P, 28), { tone: "faint" }) }, station) + spikesOf(v, true);
}
function carriage() {
  const out = [`<path class="iso-halo" d="${k.haloOf(k.insetPlan(CAR, 2), CAR_Z, 0.1, P)}" style="filter:blur(3px)"/>`];
  out.push(S(k.slabOf(CAR, CAR_Z, CAR_TOP - CAR_Z, P, 4, 0.5), { tone: "mid" }));
  out.push(D([-9, 9].flatMap((x) => [-5.5, 5.5].map((y) => at([x, y, CAR_TOP]))), { size: 0.4 }));
  out.push(L(k.lineOnTop([CAR.x, 0], [CAR.x + 1.8, 0], CAR_TOP, P), { tone: "faint" }));
  return out.join("");
}

// ---------------- ribosome, tape, polymerase ----------------
function pulley() {
  const [x, y] = PULLEY;
  return (
    S(k.cylinder(x, y, 3.2, 0, 1.4, P, 20), { tone: "lo" }) +
    S(k.cylinder(x, y, 1.2, 1.4, PULLEY_Z - 1.4, P, 14), { tone: "mid", crease: "none", inner: L(k.sideArc(x, y, 1.2, 14, P, 10), { tone: "faint" }) }) +
    S(k.cylinder(x, y, 4.2, PULLEY_Z, 3.4, P, 32, 0.3), { tone: "mid", inner: L(k.sideArc(x, y, 4.2, PULLEY_Z + 1.7, P, 20), { tone: "faint" }) }) +
    L(k.ring(x, y, 1.2, PULLEY_Z + 3.4, P, 14), { tone: "lo" })
  );
}
const TAPE = [
  [M.CRADLE_X, 0, V.z + V.h],
  [PULLEY[0] - 3.2, 0, PULLEY_Z + 3.4],
  [PULLEY[0] + 3.2, 0, PULLEY_Z + 3.4],
  [RIBO_SMALL.x - 2, 0, TAPE_Z],
  [RIBO_SMALL.x + RIBO_SMALL.w + 2, 0, TAPE_Z],
  [ROLLERS[0][0], 0, TAPE_Z - 1],
];
function tape() {
  const d = k.pathOf(TAPE.map(at));
  return `<g data-part="tape" style="opacity:0">${L(d, { tone: "faint" })}<path data-part="tape-flow" class="iso-line" data-tone="hi" d="${d}"/>${D([at(TAPE[0])], { size: 0.8, tone: "hi" })}</g>`;
}
function ribosome() {
  const out = [];
  out.push(`<path class="iso-halo" d="${k.haloOf(RIBO_LARGE, 0, 1, P)}" style="filter:blur(5px)"/>`);
  out.push(S(k.slabOf(RIBO_SMALL, 0, TAPE_Z - 2.5, P, 6, 0.6), { tone: "mid", inner: L(k.sideSeam(RIBO_SMALL, 4, P, 6), { tone: "faint" }) }));
  out.push(L(k.planOutline(k.insetPlan(RIBO_SMALL, 3), TAPE_Z - 2.5, P, 6), { tone: "faint" }));
  // two spacer posts at the back hold the large subunit over the tape channel
  for (const x of [RIBO_SMALL.x + 3, RIBO_SMALL.x + RIBO_SMALL.w - 3]) out.push(S(k.cylinder(x, -5.5, 1.3, TAPE_Z - 2.5, 5.5, P, 14), { tone: "mid", crease: "none" }));
  out.push(S(k.slabOf(RIBO_LARGE, TAPE_Z + 3, 15, P, 8, 0.8), { tone: "mid", crease: "lo", inner: L(k.sideSeam(RIBO_LARGE, TAPE_Z + 7, P, 8), { tone: "faint" }) }, "ribosome"));
  out.push(L(k.planOutline(k.insetPlan(RIBO_LARGE, 4), TAPE_Z + 18, P, 8), { tone: "faint" }));
  const vents = [0, 1, 2].map((i) => k.planOutline({ x: RIBO_LARGE.x + 7 + i * 5, y: -4, w: 2, d: 8, r: 1 }, TAPE_Z + 18, P, 3)).join("");
  out.push(L(vents, { tone: "lo" }));
  out.push(D(k.corners(RIBO_LARGE, 2.6).map(([x, y]) => at([x, y, TAPE_Z + 18])), { size: 0.45 }));
  return out.join("");
}
function proteinTray() {
  const out = [S(k.slabOf(TRAY, 0, 2, P, 3, 0.4), { tone: "lo" }), L(k.planOutline(k.insetPlan(TRAY, 1.2), 2, P, 3), { tone: "faint" })];
  const cells = [];
  for (let row = 0; row < 2; row++) for (let col = 0; col < 3; col++) cells.push([TRAY.x + 3 + col * 8.4, TRAY.y + 1.3 + row * 3.6]);
  const order = cells.map((c, i) => [c, i]).sort((a, b) => depth2(a[0]) - depth2(b[0]));
  for (const [[x, y], i] of order) out.push(`<g data-protein="${i}" style="opacity:0">${S(k.slabOf({ x, y, w: 5.4, d: 3, r: 0.6 }, 2, 3, P, 2), { tone: "mid", crease: "lo" })}</g>`);
  return out.join("");
}
function polymeraseBack() {
  const out = [S(k.slabOf(POLY_BASE, 0, 5, P, 4, 0.5), { tone: "mid" }), L(k.planOutline(k.insetPlan(POLY_BASE, 2), 5, P, 4), { tone: "faint" })];
  out.push(D(k.corners(POLY_BASE, 2.5).map(([x, y]) => at([x, y, 5])), { size: 0.45 }));
  out.push(roller(ROLLERS[0]));
  return out.join("");
}
function roller([x, y]) {
  return S(k.cylinder(x, y, ROLLER_R, 5, 15, P, 28, 0.3), { tone: "mid", crease: "lo", inner: L(k.knurl(x, y, ROLLER_R, 5, 20, 22, P, 0.3), { tone: "faint" }) }, "polymerase");
}
function polymeraseFront() {
  const bridge = { x: 29.5, y: -10, w: 11, d: 20, r: 2 };
  return (
    roller(ROLLERS[1]) +
    S(k.slabOf(bridge, 20, 3, P, 3, 0.5), { tone: "mid" }) +
    L(ROLLERS.map(([x, y]) => k.ring(x, y, 1.4, 23, P, 14)).join(""), { tone: "lo" }) +
    S(k.cylinder(35, 0, 2.2, 23, 3, P, 18), { tone: "mid" }) +
    L(k.knurl(35, 0, 2.2, 23, 26, 14, P), { tone: "faint" })
  );
}

// ---------------- rack of copies ----------------
function rack() {
  const out = [S(k.slabOf(RACK, 0, 3, P, 5, 0.6), { tone: "lo" }), L(k.planOutline(k.insetPlan(RACK, 2.2), 3, P, 5), { tone: "faint" })];
  out.push(D(k.corners(RACK, 2).map(([x, y]) => at([x, y, 3])), { size: 0.45 }));
  const order = SPINDLES.map((p, i) => [p, i]).sort((a, b) => depth2(a[0]) - depth2(b[0]));
  for (const [[x, y], i] of order) {
    out.push(S(k.cylinder(x, y, 1, 3, 10, P, 12), { tone: "mid", crease: "none" }));
    out.push(L(k.ring(x, y, 2.6, 3, P, 18), { tone: "faint" }));
    out.push(
      `<g data-spool="${i}" style="opacity:0">` +
        S(k.cylinder(x, y, 4.2, 3, 1, P, 24), { tone: "mid" }) +
        S(k.cylinder(x, y, 2.9, 4, 4.4, P, 22), { tone: "mid", crease: "lo", inner: L([5.5, 7].map((z) => k.sideArc(x, y, 2.9, z, P, 14)).join(""), { tone: "faint" }) }) +
        S(k.cylinder(x, y, 4.2, 8.4, 1, P, 24), { tone: "mid" }) +
        S(k.cylinder(x, y, 1, 9.4, 3.6, P, 12), { tone: "mid", crease: "none" }) +
        `</g>`,
    );
  }
  return out.join("");
}

// ---------------- conveyor out ----------------
function belt() {
  const out = [];
  out.push(S(k.slabOf(BELT, 0, BELT_TOP, P, 6, 0.4), { tone: "lo" }));
  out.push(L(k.planOutline(k.insetPlan(BELT, 2), BELT_TOP, P, 6), { tone: "faint" }));
  for (const x of [BELT.x + 5.5, BELT.x + BELT.w - 5.5]) out.push(L(k.ring(x, 0, 1.4, BELT_TOP, P, 14), { tone: "lo" }));
  return out.join("");
}
function beltRail(y) {
  const plan = { x: BELT.x + 4, y: y - 1, w: BELT.w - 8, d: 2, r: 0.6 };
  return S(k.slabOf(plan, 0, 5, P, 2, 0.3), { tone: "mid" }) + D([BELT.x + 10, BELT.x + BELT.w / 2, BELT.x + BELT.w - 10].map((x) => at([x, y, 5])), { size: 0.4 });
}
function smallVirion(i) {
  return `<g data-virion="${i}" style="opacity:0">${capsidOf(SMALL)}${envelopeOf(SMALL, "progeny")}${lidOf(SMALL)}</g>`;
}

// ---------------- assembly ----------------
const leftFar = rimX(MEM_X, RIM_FAR + RIM_T, -GAP);
const leftNear = rimX(MEM_X, GAP, RIM_NEAR);
const rightFar = rimX(EXIT_X, RIM_FAR + RIM_T, -GAP + 2);
const rightNear = rimX(EXIT_X, GAP - 2, RIM_NEAR);
const farWall = rimY(RIM_FAR, MEM_X - RIM_T / 2, EXIT_X + RIM_T / 2);
const nearWall = rimY(RIM_NEAR, MEM_X - RIM_T / 2, EXIT_X + RIM_T / 2);

const body = [
  bench(),
  rim(farWall),
  rimDots([[MEM_X + 20, RIM_FAR + 2.5], [25, RIM_FAR + 2.5], [EXIT_X - 20, RIM_FAR + 2.5]]),
  rim(leftFar),
  rim(rightFar),
  gatePost(MEM_X, -GAP - 3),
  receptor(RECEPTORS[0]),
  `<g data-part="shutter">${shutter()}</g>`,
  lintel(MEM_X),
  `<g data-slot="outside">`,
  `<g data-part="capsid">${carriage()}${capsidOf(V)}</g>`,
  `<g data-part="envelope">${envelopeOf(V, "envelope")}</g>`,
  `<g data-part="lid">${lidOf(V)}</g>`,
  `</g>`,
  receptor(RECEPTORS[1]),
  gatePost(MEM_X, GAP + 3),
  rim(leftNear),
  `<g data-slot="inside"></g>`,
  S(k.slabOf({ x: M.CRADLE_X + 12, y: -9, w: 4, d: 18, r: 1 }, 0, 6, P, 3, 0.4), { tone: "mid" }),
  D([at([M.CRADLE_X + 14, -6, 6]), at([M.CRADLE_X + 14, 6, 6])], { size: 0.45 }),
  pulley(),
  polymeraseBack(),
  rack(),
  tape(),
  ribosome(),
  proteinTray(),
  polymeraseFront(),
  belt(),
  beltRail(-8),
  gatePost(EXIT_X, -GAP - 1),
  lintel(EXIT_X, 30),
  ...Array.from({ length: M.VIRIONS }, (_, i) => smallVirion(M.VIRIONS - 1 - i)),
  beltRail(8),
  gatePost(EXIT_X, GAP + 1),
  rim(rightNear),
  rim(nearWall),
  rimDots([[MEM_X + 20, RIM_NEAR + 2.5], [25, RIM_NEAR + 2.5], [EXIT_X - 20, RIM_NEAR + 2.5]]),
  `<g data-part="cursor">${S(k.slabOf({ x: -1.6, y: RULER.y - 1.2, w: 3.2, d: RULER.d + 2.4, r: 0.8 }, 0.6, 2, P, 2), { tone: "hi", lit: true })}</g>`,
];

const svg = k.figureSvg({
  width: WIDTH,
  height: HEIGHT,
  label:
    "An infection bench. A tray whose rim is the cell membrane stands on a base plate. A spiked canister, the virion, rides a rail to two receptor posts at a gate in the rim; its spiked sleeve, the envelope, fuses and stays behind while the gate opens and the inner canister, the capsid, rolls in. Its lid lifts and a tape, the RNA genome, feeds over a pulley through a two-part reader, the ribosome, which drops protein blocks into a tray, and into a pair of rollers, the polymerase, whose copies fill a rack of spools. New spiked canisters ride a conveyor out through a second gate. A ruler along the front edge marks hours.",
  body,
});

const MODEL = readFileSync(join(HERE, "model.mjs"), "utf8").replace(/^export /gm, "");
const live = `
${MODEL}
const P = ${JSON.stringify(P)};
const SMALL_STEP = ${JSON.stringify(k.axisVector(P, [1, 0, 0]))};
const MEM_X = ${MEM_X};
const stage = document.querySelector(".iso-stage");
const svg = stage.querySelector("svg");
const $ = (s) => svg.querySelector(s);
const parts = { capsid: $('[data-part="capsid"]'), envelope: $('[data-part="envelope"]'), lid: $('[data-part="lid"]'), shutter: $('[data-part="shutter"]'), tape: $('[data-part="tape"]'), flow: $('[data-part="tape-flow"]'), cursor: $('[data-part="cursor"]') };
const slots = { outside: $('[data-slot="outside"]'), inside: $('[data-slot="inside"]') };
const proteins = [...svg.querySelectorAll("[data-protein]")].sort((a, b) => a.dataset.protein - b.dataset.protein);
const spools = [...svg.querySelectorAll("[data-spool]")].sort((a, b) => a.dataset.spool - b.dataset.spool);
const virions = [...svg.querySelectorAll("[data-virion]")].sort((a, b) => a.dataset.virion - b.dataset.virion);
const stations = [...svg.querySelectorAll("[data-station]")];
const readout = document.querySelector("[data-readout]");
const still = matchMedia("(prefers-reduced-motion: reduce)");
const LIT = { attach: "envelope", fuse: "envelope", enter: "capsid", uncoat: "capsid", translate: "ribosome", copy: "polymerase", assemble: "progeny", release: "progeny" };
const op = (el, a) => { const v = a.toFixed(3); if (el.style.opacity !== v) el.style.opacity = v; };
let where = "outside", lastPhase = "";
function draw(t) {
  const s = stateAt(t);
  const inside = s.x > MEM_X;
  if ((inside ? "inside" : "outside") !== where) {
    where = inside ? "inside" : "outside";
    slots[where].append(parts.capsid, parts.lid);
  }
  parts.capsid.setAttribute("transform", translateAlong(P, [s.x, 0, 0]));
  parts.envelope.setAttribute("transform", translateAlong(P, [Math.min(s.x, DOCK_X), 0, 0]));
  op(parts.envelope, s.envelope);
  parts.lid.setAttribute("transform", translateAlong(P, [s.x, 0, s.lid * 16]));
  op(parts.lid, 1 - s.lid);
  parts.shutter.setAttribute("transform", translateAlong(P, [0, 0, s.shutter * 26]));
  op(parts.tape, s.tape);
  if (s.flowing !== parts.flow.hasAttribute("data-flow")) parts.flow.toggleAttribute("data-flow", s.flowing && !still.matches);
  parts.flow.style.opacity = s.flowing ? "1" : "0";
  proteins.forEach((el, i) => op(el, s.proteins[i]));
  spools.forEach((el, i) => op(el, s.spools[i]));
  virions.forEach((el, i) => { const v = s.virions[i]; op(el, v.alpha); el.setAttribute("transform", translateAlong(P, [v.x, 0, 0])); });
  parts.cursor.setAttribute("transform", translateAlong(P, [-150 + Math.min(t, END) * ${HOUR}, 0, 0]));
  const phase = phaseAt(t).key;
  if (phase !== lastPhase) {
    lastPhase = phase;
    stations.forEach((el) => el.toggleAttribute("data-lit", el.dataset.station === LIT[phase]));
    stage.setAttribute("aria-valuetext", readoutAt(t));
  }
  const text = readoutAt(t);
  if (readout.textContent !== text) readout.textContent = text;
  stage.setAttribute("aria-valuenow", t.toFixed(1));
}
const TOUR = 30, HOLD = 3;
let t = 0, target = 0, clock = 0, touring = true, visible = false, frame = 0, last = 0, idle = 0;
const tourAt = (c) => Math.min(END, (c % (TOUR + HOLD)) / TOUR * END);
function tick(now) {
  const dt = last ? Math.min((now - last) / 1000, 1 / 30) : 1 / 60;
  last = now;
  if (touring) { clock += dt; target = tourAt(clock); t = target; }
  else t = still.matches ? target : t + (target - t) * (1 - Math.exp(-dt / 0.25));
  if (!touring && Math.abs(target - t) < 0.002) t = target;
  draw(t);
  const settled = !touring && t === target;
  frame = visible && !settled ? requestAnimationFrame(tick) : 0;
}
const run = () => { if (!frame && visible) { last = 0; frame = requestAnimationFrame(tick); } };
const steer = (next) => { touring = false; target = Math.min(END, Math.max(0, next)); clearTimeout(idle); idle = setTimeout(() => { touring = !still.matches; clock = target / END * TOUR; run(); }, 3600); run(); };
new IntersectionObserver((e) => { visible = e[e.length - 1].isIntersecting; if (visible) run(); }, { rootMargin: "120px 0px" }).observe(stage);
if (still.matches) { touring = false; target = t = 3.5; }
stage.addEventListener("pointermove", (e) => { const b = svg.getBoundingClientRect(); steer(((e.clientX - b.left) / b.width - 0.08) / 0.84 * END); });
stage.addEventListener("pointerdown", (e) => { const b = svg.getBoundingClientRect(); steer(((e.clientX - b.left) / b.width - 0.08) / 0.84 * END); });
stage.addEventListener("keydown", (e) => {
  let to = null;
  if (e.key === "ArrowRight" || e.key === "ArrowUp") to = target + (e.shiftKey ? 1 : 0.25);
  if (e.key === "ArrowLeft" || e.key === "ArrowDown") to = target - (e.shiftKey ? 1 : 0.25);
  if (e.key === "Home") to = 0;
  if (e.key === "End") to = END;
  if (to === null) return;
  e.preventDefault();
  steer(to);
});
draw(still.matches ? 3.5 : 0);
`;

const bodyHtml = k.plateHtml({
  fig: "Fig 1",
  title: "Virus entry and replication",
  hint: "Hover to scrub the hours",
  readout: M.readoutAt(0),
  keys: [
    { mark: "lit", label: "The step happening now" },
    { mark: "raised", label: "Envelope with spikes, capsid, ribosome, polymerase rollers" },
    { mark: "flat", label: "Rim of the tray: the cell membrane" },
  ],
  caption:
    "A coronavirus-like virion meets a cell. Its spike proteins lock onto receptor posts (ACE2) at the membrane; the envelope fuses with the membrane and the capsid passes in. Uncoated, its RNA genome is read by a ribosome, which makes the replicase proteins; the polymerase then copies the genome again and again, each spool on the rack one doubling. New virions are packed and leave through the far side. Times on the ruler follow SARS-CoV-2 in cultured cells only roughly (entry within the first hour, new genomes from about 2–3 h, first virions out by about 6–8 h); copy counts are illustrative.",
  body: `<div class="iso-stage" tabindex="0" role="slider" aria-label="Infection timeline: arrow keys step a quarter hour, Shift for an hour" aria-valuemin="0" aria-valuemax="${M.END}" aria-valuenow="0" style="touch-action:pan-y">${svg}</div>`,
});

const file = theme === "light" ? "virus-entry-light.html" : "virus-entry.html";
writeFileSync(join(HERE, file), k.pageHtml({ title: "Virus entry", theme, body: bodyHtml, script: kitScript() + live, width: 720 }));
console.log("wrote", file);
