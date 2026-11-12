/* Statecraft Lab engine. The exposure arithmetic follows the model in Chapter 1 and
   Appendix B, exercise 7, of the economic coercion book: q = s*tau*(1-lambda) and
   p1/p0 = (1-q)^(-1/eta). The pressure path is a stylized rendering of that book's
   Figure 1.5; its functional forms are this tool's and are not estimates. */
(function (root) {
  'use strict';

  function netWithdrawal(s, tau, lam) { return s * tau * (1 - lam); }

  // Exact constant-elasticity price rise, as a proportion (0.297 = 29.7 percent).
  function priceRise(q, eta) {
    if (q <= 0) return 0;
    if (q >= 1 || eta <= 0) return Infinity;
    return Math.pow(1 - q, -1 / eta) - 1;
  }

  function priceRiseApprox(q, eta) { return eta > 0 ? q / eta : Infinity; }

  // Units of supply out of 100, as in Figure B.1.
  function supply(s, tau, lam, replaced) {
    var withheld = s * tau, q = netWithdrawal(s, tau, lam), built = q * (replaced || 0);
    return {
      others: 100 * (1 - s), shipped: 100 * (s - withheld), rerouted: 100 * withheld * lam,
      built: 100 * built, missing: 100 * (q - built), q: q
    };
  }

  function exposure(o) {
    var q = netWithdrawal(o.s, o.tau, o.lam), qLong = q * (1 - (o.replaced || 0));
    return {
      q: q, shortRun: priceRise(q, o.etaShort), ruleOfThumb: priceRiseApprox(q, o.etaShort),
      longRunSameShortage: priceRise(q, o.etaLong), qLong: qLong,
      longRunWithCapacity: priceRise(qLong, o.etaLong)
    };
  }

  // Share of baseline supply still missing t months in: the replaceable part of the
  // shortage halves every halfLife months; a fraction `floor` of it is never replaced.
  function missingAt(t, q, halfLife, floor) {
    var decay = halfLife > 0 ? Math.pow(0.5, t / halfLife) : 0;
    return q * (floor + (1 - floor) * decay);
  }

  // Politically weighted pressure: the price rise on the missing supply times the
  // share of that burden reaching people who decide.
  function pressureAt(t, o) {
    return o.weight * priceRise(missingAt(t, o.q, o.halfLife, o.floor), o.eta);
  }

  // Months for which pressure exceeds the concession threshold.
  // 0: never above. Infinity: never falls below. Otherwise the month it crosses.
  function windowMonths(o) {
    if (!(o.weight > 0) || pressureAt(0, o) <= o.threshold) return 0;
    var mStar = 1 - Math.pow(1 + o.threshold / o.weight, -o.eta); // shortage at which pressure equals the threshold
    var stuck = o.q * o.floor; // shortage that is never replaced
    if (mStar <= stuck) return Infinity;
    if (!(o.halfLife > 0)) return 0;
    return o.halfLife * Math.log(o.q * (1 - o.floor) / (mStar - stuck)) / Math.LN2;
  }

  function path(o, months) {
    var out = [];
    for (var t = 0; t <= months; t++) out.push({ t: t, missing: missingAt(t, o.q, o.halfLife, o.floor), pressure: pressureAt(t, o) });
    return out;
  }

  // Cross-tabulation of cases: counts[row][col].
  function tabulate(cases, rowKey, colKey) {
    var counts = {}, rows = [], cols = [];
    cases.forEach(function (c) {
      var r = c[rowKey], k = c[colKey];
      if (rows.indexOf(r) < 0) rows.push(r);
      if (cols.indexOf(k) < 0) cols.push(k);
      counts[r] = counts[r] || {};
      counts[r][k] = (counts[r][k] || 0) + 1;
    });
    return { rows: rows, cols: cols, counts: counts };
  }

  // A case counts as adapted by its month value only when that value is a point or an
  // upper bound. Lower bounds mean "not yet", and are censored.
  function adapted(c) { return c.months != null && (c.basis === 'approx' || c.basis === 'upper_bound'); }
  function adaptedWithin(cases, months) { return cases.filter(function (c) { return adapted(c) && c.months <= months; }); }

  var api = { netWithdrawal: netWithdrawal, priceRise: priceRise, priceRiseApprox: priceRiseApprox, supply: supply,
    exposure: exposure, missingAt: missingAt, pressureAt: pressureAt, windowMonths: windowMonths, path: path,
    tabulate: tabulate, adapted: adapted, adaptedWithin: adaptedWithin };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.StatecraftLab = api;
})(this);
