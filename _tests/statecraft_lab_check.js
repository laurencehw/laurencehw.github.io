/* Checks the Statecraft Lab engine against the worked numbers in the coercion book
   (Appendix B, exercises 7 and 8; Chapter 9, the grain embargo). Run: node _tests/statecraft_lab_check.js */
var L = require('../tools/statecraft-lab.js'), C = require('../tools/statecraft-cases.js');
var fails = 0;
function near(name, got, want, tol) { var ok = Math.abs(got - want) <= (tol || 5e-4); if (!ok) fails++; console.log((ok ? 'ok   ' : 'FAIL ') + name + ': ' + got + ' (want ' + want + ')'); }
function eq(name, got, want) { var ok = got === want || JSON.stringify(got) === JSON.stringify(want) && got !== Infinity && want !== Infinity; if (!ok) fails++; console.log((ok ? 'ok   ' : 'FAIL ') + name + ': ' + JSON.stringify(got) + (ok ? '' : ' (want ' + JSON.stringify(want) + ')')); }

// Exercise 7 worked answer
var e = L.exposure({ s: 0.2, tau: 0.5, lam: 0.25, etaShort: 0.3, etaLong: 1.5, replaced: 5 / 7.5 });
near('q', e.q, 0.075, 1e-12);
near('short-run rise 29.7%', e.shortRun, 0.297);
near('long-run, same shortage 5.3%', e.longRunSameShortage, 0.053);
near('long-run shortage 0.025', e.qLong, 0.025, 1e-12);
near('long-run, new capacity 1.7%', e.longRunWithCapacity, 0.017);
near('45% withdrawal, exact about 630%', L.priceRise(0.45, 0.3), 6.3, 0.05);
near('45% withdrawal, rule of thumb 150%', L.priceRiseApprox(0.45, 0.3), 1.5, 1e-12);
var u = L.supply(0.2, 0.5, 0.25, 5 / 7.5);
eq('Figure B.1 units', [u.others, u.shipped, u.rerouted, u.built, u.missing].map(function (x) { return Math.round(x * 10) / 10; }), [80, 10, 2.5, 5, 2.5]);
// Further question 1: rerouted share cut to 10 percent
near('q with 10% rerouting', L.netWithdrawal(0.2, 0.5, 0.1), 0.09, 1e-12);

// Grain embargo: 25 of 35 Mt, 17 withheld, all but 4 arrived
near('grain q about 11%', L.netWithdrawal(25 / 35, 17 / 25, 13 / 17), 4 / 35, 1e-12);
near('grain: eta of about one-half gives about 25%', L.priceRise(4 / 35, 0.54), 0.25, 0.005);
var g = C.filter(function (c) { return c.id === 'C03'; })[0];
near('dataset grain q matches s*tau*(1-lambda)', L.netWithdrawal(g.s, g.tau, g.lam), g.q, 0.012);

// Pressure path: closed-form window agrees with the path, and limits behave
var o = { q: 0.3, eta: 0.3, halfLife: 12, floor: 0, weight: 0.5, threshold: 0.2 };
var w = L.windowMonths(o);
near('pressure at the window equals the threshold', L.pressureAt(w, o), 0.2, 1e-9);
eq('no pressure, no window', L.windowMonths({ q: 0.3, eta: 0.3, halfLife: 12, floor: 0, weight: 0, threshold: 0.2 }), 0);
eq('stalled adaptation keeps pressure above the threshold', L.windowMonths({ q: 0.3, eta: 0.3, halfLife: 12, floor: 0.8, weight: 0.5, threshold: 0.2 }), Infinity);
eq('small shock never reaches the threshold', L.windowMonths({ q: 0.02, eta: 1, halfLife: 12, floor: 0, weight: 0.5, threshold: 0.2 }), 0);
near('missing halves at the half-life', L.missingAt(12, 0.3, 12, 0), 0.15, 1e-12);

// Exercise 8
eq('fifteen cases', C.length, 15);
var sought = C.filter(function (c) { return c.concession !== 'not_sought'; });
eq('twelve cases where a concession was sought', sought.length, 12);
var byClock = L.tabulate(sought, 'clock', 'concession').counts;
function n(x) { return x || 0; }
eq('8(a): political clock: 2 full and 1 partial concession', [n(byClock.political.yes), n(byClock.political.partial)], [2, 1]);
eq('8(a): no concession on the other clocks', [n(byClock.adaptation.yes) + n(byClock.adaptation.partial), n(byClock.network.yes) + n(byClock.network.partial)], [0, 0]);
eq('8(a): political-clock cases', sought.filter(function (c) { return c.clock === 'political'; }).length, 6);
var byBand = L.tabulate(sought, 'band', 'concession').counts;
eq('8(a): high-exposure cases: 2 yes, 1 unattributed, 5 no', [byBand.high.yes, byBand.high.unattributed, byBand.high.no], [2, 1, 5]);
eq('8(b): six adapted-by values', C.filter(L.adapted).length, 6);
eq('8(b): adapted within 24 months', L.adaptedWithin(C, 24).map(function (c) { return c.id; }), ['C03', 'C12', 'C13', 'C14']);
eq('8(b): all four on the adaptation clock', L.adaptedWithin(C, 24).every(function (c) { return c.clock === 'adaptation'; }), true);

console.log(fails ? fails + ' check(s) failed' : 'all checks passed');
process.exit(fails ? 1 : 0);
