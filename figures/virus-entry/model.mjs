// Infection timeline, in hours after the virion meets the cell.
// Rough SARS-CoV-2 timing in cultured cells: entry within the first hour,
// new genomes from ~2-3 h, first progeny leaving ~6-8 h. Copy counts are illustrative.
export const END = 8;
export const PHASES = [
  { key: "attach", from: 0, to: 0.3, word: "spike docks" },
  { key: "fuse", from: 0.3, to: 0.6, word: "envelope fuses" },
  { key: "enter", from: 0.6, to: 0.9, word: "capsid enters" },
  { key: "uncoat", from: 0.9, to: 1.2, word: "RNA released" },
  { key: "translate", from: 1.2, to: 2.5, word: "making replicase" },
  { key: "copy", from: 2.5, to: 5.5, word: "genome copied" },
  { key: "assemble", from: 5.5, to: 6.2, word: "virions packed" },
  { key: "release", from: 6.2, to: 8.01, word: "virions leave" },
];
export const START_X = -152, DOCK_X = -124, CRADLE_X = -60;
export const PROTEINS = 6, DOUBLINGS = 12, VIRIONS = 6;
export const BELT_FROM = 116, BELT_TO = 182;
const clamp01 = (v) => Math.min(1, Math.max(0, v));
export const share = (t, a, b) => { const s = clamp01((t - a) / (b - a)); return s * s * (3 - 2 * s); };
export const phaseAt = (t) => PHASES.find((p) => t < p.to) || PHASES[PHASES.length - 1];
export function stateAt(t) {
  const x = t < 0.6 ? START_X + (DOCK_X - START_X) * share(t, 0, 0.3) : DOCK_X + (CRADLE_X - DOCK_X) * share(t, 0.6, 0.9);
  const envelope = 1 - share(t, 0.3, 0.6);
  const shutter = share(t, 0.32, 0.58) - share(t, 0.95, 1.15);
  const lid = share(t, 0.9, 1.2);
  const tape = share(t, 0.95, 1.2);
  const made = PROTEINS * clamp01((t - 1.3) / (2.5 - 1.3));
  const proteins = Array.from({ length: PROTEINS }, (_, i) => clamp01(made - i));
  const doublings = DOUBLINGS * clamp01((t - 2.5) / (5.5 - 2.5));
  const spools = Array.from({ length: DOUBLINGS }, (_, i) => clamp01(doublings - i));
  const virions = Array.from({ length: VIRIONS }, (_, i) => {
    const born = 5.6 + 0.28 * i;
    const vx = BELT_FROM + Math.max(0, t - born) * 70;
    const alpha = share(t, born, born + 0.12) * (1 - share(vx, BELT_TO - 12, BELT_TO));
    return { x: Math.min(vx, BELT_TO), alpha, out: vx >= BELT_TO - 6 };
  });
  return { x, envelope, shutter, lid, tape, proteins, copies: Math.round(2 ** doublings), spools, virions, released: virions.filter((v) => v.out).length, flowing: t > 1.2 && t < 5.5 };
}
export function readoutAt(t) {
  const p = phaseAt(t), s = stateAt(t);
  let extra = "";
  if (p.key === "translate") extra = ` · ${Math.floor(PROTEINS * Math.min(1, Math.max(0, (t - 1.3) / 1.2)))}/${PROTEINS}`;
  if (p.key === "copy") extra = ` · ${s.copies.toLocaleString("en")} copies`;
  if (p.key === "release" || p.key === "assemble") extra = ` · ${s.released} out`;
  return `${t.toFixed(1)} h · ${p.word}${extra}`;
}
