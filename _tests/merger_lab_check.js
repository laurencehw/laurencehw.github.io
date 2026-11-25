// Checks tools/merger-lab.js on the worked example from Antitrust Research Methods (Chapter 6).
// Run: node _tests/merger_lab_check.js
// The expected prices come from run_logit_sim() in the book's program/R/helpers.R, run in R 4.5.2
// on 2026-11-18 (10.6553150796, 12.6553150796, 12.4923375294, 10.6397329731; alpha 0.4977962858),
// and from an independent NumPy port of it; the first-order conditions are also checked directly.
const assert = require("assert");
const M = require("../tools/merger-lab.js");
const P = [["Product 1", "Firm A", 10, 0.25, 0.33], ["Product 2", "Firm A", 12, 0.15, 0.28],
  ["Product 3", "Firm B", 11, 0.20, 0.23], ["Product 4", "Firm C", 10.5, 0.20, 0.24]]
  .map(r => ({ product: r[0], firm: r[1], price: r[2], share: r[3], margin: r[4] }));
const near = (a, b, tol = 1e-8) => assert(Math.abs(a - b) < tol, `${a} vs ${b}`);
const sim = M.simulate(P, ["Firm A", "Firm B"]);
assert(sim.converged);
near(sim.alpha, 0.4977962858397642);
[10.65531508, 12.65531508, 12.49233753, 10.63973297].forEach((v, j) => near(sim.pricesPost[j], v, 1e-7));
// First-order conditions at the solution: s_j + sum over the owner's products of (p_k - c_k) ds_k/dp_j = 0
sim.pricesPost.forEach((_, j) => {
  let r = sim.sharesPost[j];
  sim.pricesPost.forEach((pk, k) => {
    if (sim.ownershipPost[k] !== sim.ownershipPost[j]) return;
    const d = k === j ? -sim.alpha * sim.sharesPost[j] * (1 - sim.sharesPost[j]) : sim.alpha * sim.sharesPost[k] * sim.sharesPost[j];
    r += (pk - sim.mcImplied[k]) * d;
  });
  near(r, 0, 1e-9);
});
// "Merging" a firm with itself changes no ownership, so prices stay where they were
const same = M.simulate(P, ["Firm A", "Firm A"]);
same.pctChange.forEach(c => near(c, 0, 1e-8));
// Efficiencies lower the merging products' prices relative to no efficiency
const eff = M.simulate(P, ["Firm A", "Firm B"], { efficiency: 0.1 });
[0, 1, 2].forEach(j => assert(eff.pricesPost[j] < sim.pricesPost[j]));
// Concentration: firm shares of inside sales are 50, 25, 25
const h = M.hhi(P, ["Firm A", "Firm B"]);
near(h.pre, 3750); near(h.post, 6250); near(h.delta, 2500); assert(h.presumedHHI);
// Pricing pressure by hand: D_13 * margin_3 / p_1, and so on
const u = M.upp(P, ["Firm A", "Firm B"], 0, 0.5);
near(u[0].guppi, (0.20 / 0.75) * (11 * 0.23) / 10); near(u[2].guppi, ((0.25 / 0.8) * 3.3 + (0.15 / 0.8) * 3.36) / 11);
assert(u[3] === null);
// Efficiency credit: UPP_j = sum_k D_jk (p_k - (1 - e) c_k) - e c_j, by hand for Product 3
const ue = M.upp(P, ["Firm A", "Firm B"], 0.1, 0.5);
near(ue[2].upp, (0.25 / 0.8) * (10 - 0.9 * 6.7) + (0.15 / 0.8) * (12 - 0.9 * 8.64) - 0.1 * 8.47);
// Small outside option (s0 = 1%) solves cleanly without exp() underflow
const smallS0 = M.simulate([
  { product: "P1", firm: "A", price: 10, share: 0.495, margin: 0.5 },
  { product: "P2", firm: "B", price: 10, share: 0.495, margin: 0.5 }
], ["A", "B"]);
assert(smallS0.converged && smallS0.pricesPost.every(p => isFinite(p) && p > 10));
// Asymmetric market converges and flags the negative implied marginal cost
const asym = M.simulate([
  { product: "Budget", firm: "A", price: 1, share: 0.49, margin: 0.95 },
  { product: "Luxury", firm: "B", price: 1000, share: 0.49, margin: 0.05 }
], ["A", "B"]);
assert(asym.converged && asym.negativeMc.indexOf(0) >= 0);
// A non-merging rival named "A+B" is never absorbed into the merged firm
const col = M.simulate([
  { product: "P1", firm: "A", price: 10, share: 0.25, margin: 0.33 },
  { product: "P2", firm: "B", price: 11, share: 0.20, margin: 0.23 },
  { product: "P3", firm: "A+B", price: 10.5, share: 0.20, margin: 0.24 }
], ["A", "B"], { efficiency: 0.1 });
assert(col.converged && col.isMerged[2] === false && col.ownershipPost[2] === "A+B" && col.ownershipPost[0] !== "A+B");
near(col.mcPost[2], col.mcImplied[2], 1e-12);
console.log("merger-lab: all checks pass");
