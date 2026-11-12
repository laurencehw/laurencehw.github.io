/* Merger Lab: concentration screen, upward pricing pressure and a Bertrand-logit
   merger simulation. The simulation follows run_logit_sim() in the Antitrust
   Methods book (program/R/helpers.R) step for step; with no efficiency it
   returns the same numbers. No dependencies. */
(function (root) {
  "use strict";

  function solve(A, b) {            // Gaussian elimination with partial pivoting
    var n = b.length, M = A.map(function (r, i) { return r.concat([b[i]]); });
    for (var c = 0; c < n; c++) {
      var piv = c;
      for (var r = c + 1; r < n; r++) if (Math.abs(M[r][c]) > Math.abs(M[piv][c])) piv = r;
      if (Math.abs(M[piv][c]) < 1e-14) throw new Error("The pricing equations cannot be solved for these inputs.");
      var t = M[c]; M[c] = M[piv]; M[piv] = t;
      for (r = c + 1; r < n; r++) {
        var f = M[r][c] / M[c][c];
        for (var k = c; k <= n; k++) M[r][k] -= f * M[c][k];
      }
    }
    var x = new Array(n);
    for (var i = n - 1; i >= 0; i--) {
      var s = M[i][n];
      for (var j = i + 1; j < n; j++) s -= M[i][j] * x[j];
      x[i] = s / M[i][i];
    }
    return x;
  }

  /* Herfindahl-Hirschman Index on firm shares of the inside market (0-10,000). */
  function hhi(products, mergingFirms) {
    var inside = products.reduce(function (a, p) { return a + p.share; }, 0), firm = {};
    products.forEach(function (p) { firm[p.firm] = (firm[p.firm] || 0) + 100 * p.share / inside; });
    var pre = 0, post = 0, merged = 0;
    Object.keys(firm).forEach(function (f) {
      pre += firm[f] * firm[f];
      if (mergingFirms.indexOf(f) >= 0) merged += firm[f]; else post += firm[f] * firm[f];
    });
    post += merged * merged;
    var delta = post - pre;
    return { pre: pre, post: post, delta: delta, combinedShare: merged, firmShares: firm,
      // 2023 US Merger Guidelines, Guideline 1
      presumedHHI: post > 1800 && delta > 100, presumedShare: merged > 30 && delta > 100 };
  }

  /* Logit diversion from j to k: s_k / (1 - s_j). Shares are of the whole market. */
  function diversion(products) {
    return products.map(function (pj, j) {
      return products.map(function (pk, k) { return j === k ? null : pk.share / (1 - pj.share); });
    });
  }

  /* Upward pricing pressure for each merging product: diversion to the other merging
     firm's products, valued at their dollar margins, less an efficiency credit. */
  function upp(products, mergingFirms, efficiency, passThrough) {
    var D = diversion(products), eff = efficiency || 0, pt = passThrough == null ? 0.5 : passThrough;
    return products.map(function (p, j) {
      if (mergingFirms.indexOf(p.firm) < 0) return null;
      var g = 0, d = 0;
      products.forEach(function (q, k) {
        if (k !== j && q.firm !== p.firm && mergingFirms.indexOf(q.firm) >= 0) {
          g += D[j][k] * (q.price * q.margin); d += D[j][k];
        }
      });
      var credit = eff * p.price * (1 - p.margin);
      return { product: p.product, diversionToPartner: d, guppiDollar: g, guppi: g / p.price,
        upp: g - credit, uppIndex: (g - credit) / p.price, firstOrderPct: pt * (g - credit) / p.price };
    });
  }

  /* Bertrand-logit merger simulation. products: [{product, firm, price, share, margin}],
     share a fraction of the whole market (inside shares sum to less than 1), margin the
     Lerner index (p - c) / p. efficiency: proportional fall in the merging products'
     marginal cost (0 reproduces run_logit_sim). */
  function simulate(products, mergingFirms, opts) {
    opts = opts || {};
    var damping = opts.damping == null ? 0.5 : opts.damping, tol = opts.tol || 1e-10,
        maxIter = opts.maxIter || 5000, eff = opts.efficiency || 0, n = products.length;
    if (mergingFirms.length < 2) throw new Error("Choose at least two merging firms.");
    var p0 = products.map(function (p) { return p.price; }),
        s = products.map(function (p) { return p.share; }),
        c = products.map(function (p) { return p.price * (1 - p.margin); }),
        firmPre = products.map(function (p) { return p.firm; }),
        s0 = 1 - s.reduce(function (a, b) { return a + b; }, 0);
    if (!(s0 > 0)) throw new Error("Shares must sum to less than 100%: the model needs an outside option.");
    products.forEach(function (p) {
      if (!(p.price > 0) || !(p.share > 0) || !(p.margin > 0) || !(p.margin < 1))
        throw new Error("Each product needs a positive price and share and a margin between 0 and 100%.");
    });
    var firmShare = firmPre.map(function (f) {
      return s.reduce(function (a, v, k) { return a + (firmPre[k] === f ? v : 0); }, 0);
    });
    // Calibrate alpha from observed margins (multiproduct logit first-order condition)
    var alphaJ = p0.map(function (p, j) { return 1 / ((p - c[j]) * (1 - firmShare[j])); }),
        alpha = alphaJ.reduce(function (a, b) { return a + b; }, 0) / n,
        delta = s.map(function (v, j) { return Math.log(v / s0) + alpha * p0[j]; });
    function shares(p) {
      var e = p.map(function (v, j) { return Math.exp(delta[j] - alpha * v); }),
          tot = 1 + e.reduce(function (a, b) { return a + b; }, 0);
      return e.map(function (v) { return v / tot; });
    }
    function markup(firm, sh) {
      var A = sh.map(function (sj, j) {
        return sh.map(function (sk, k) {
          if (firm[j] !== firm[k]) return 0;
          return j === k ? -alpha * sj * (1 - sj) : alpha * sj * sk;
        });
      });
      return solve(A, sh.map(function (v) { return -v; }));
    }
    // Costs consistent with the first-order conditions at observed pre-merger prices
    var m0 = markup(firmPre, s), mc = p0.map(function (p, j) { return p - m0[j]; });
    var name = mergingFirms.join("+"),
        firmPost = firmPre.map(function (f) { return mergingFirms.indexOf(f) >= 0 ? name : f; }),
        mcPost = mc.map(function (v, j) { return firmPost[j] === name ? v * (1 - eff) : v; });
    var p = p0.slice(), converged = false, iter = 0;
    for (; iter < maxIter; iter++) {
      var m = markup(firmPost, shares(p)), pn = mcPost.map(function (v, j) { return v + m[j]; }),
          gap = Math.max.apply(null, pn.map(function (v, j) { return Math.abs(v - p[j]); }));
      if (gap < tol) { p = pn; converged = true; break; }
      p = p.map(function (v, j) { return v + damping * (pn[j] - v); });
    }
    var sPost = shares(p);
    // Consumer surplus change per unit of market size (logit inclusive value, in price units)
    function logsum(pr) { return Math.log(1 + pr.reduce(function (a, v, j) { return a + Math.exp(delta[j] - alpha * v); }, 0)); }
    return { alpha: alpha, alphaImplied: alphaJ, pricesPre: p0, pricesPost: p,
      pctChange: p.map(function (v, j) { return v / p0[j] - 1; }), sharesPre: s, sharesPost: sPost,
      mcImplied: mc, mcPost: mcPost, ownershipPost: firmPost, outsidePre: s0,
      outsidePost: 1 - sPost.reduce(function (a, b) { return a + b; }, 0),
      ownElasticity: p0.map(function (v, j) { return -alpha * v * (1 - s[j]); }),
      consumerSurplusChange: (logsum(p) - logsum(p0)) / alpha, converged: converged, iterations: iter };
  }

  var api = { solve: solve, hhi: hhi, diversion: diversion, upp: upp, simulate: simulate };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.MergerLab = api;
})(this);
