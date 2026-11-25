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
     firm's products, valued at their dollar margins, less an efficiency credit. The
     efficiency lowers the cost of every merging product, as in simulate(), so the
     diverted sales are valued at the partner's post-efficiency margin:
     UPP_j = sum_k D_jk (p_k - (1 - e) c_k) - e c_j. With e = 0 this is GUPPI in dollars. */
  function upp(products, mergingFirms, efficiency, passThrough) {
    var D = diversion(products), eff = efficiency || 0, pt = passThrough == null ? 0.5 : passThrough;
    return products.map(function (p, j) {
      if (mergingFirms.indexOf(p.firm) < 0) return null;
      var g = 0, d = 0, partnerCost = 0;
      products.forEach(function (q, k) {
        if (k !== j && q.firm !== p.firm && mergingFirms.indexOf(q.firm) >= 0) {
          g += D[j][k] * (q.price * q.margin);
          partnerCost += D[j][k] * q.price * (1 - q.margin);
          d += D[j][k];
        }
      });
      var credit = eff * (p.price * (1 - p.margin) - partnerCost);
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
    // Log-sum-exp stabilized shares and inclusive value, so a small outside share never underflows
    function shares(pr) {
      var u = pr.map(function (v, j) { return delta[j] - alpha * v; }),
          mx = Math.max.apply(null, u.concat([0])),
          e = u.map(function (x) { return Math.exp(x - mx); }),
          tot = Math.exp(-mx) + e.reduce(function (a, b) { return a + b; }, 0);
      return e.map(function (v) { return v / tot; });
    }
    function logsum(pr) {
      var u = pr.map(function (v, j) { return delta[j] - alpha * v; }),
          mx = Math.max.apply(null, u.concat([0])),
          tot = Math.exp(-mx) + u.reduce(function (a, x) { return a + Math.exp(x - mx); }, 0);
      return mx + Math.log(tot);
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
    // With logit demand and one price coefficient, the first-order conditions give every
    // product of firm f the same markup, 1 / (alpha * (1 - S_f)), where S_f is the firm's share.
    function markupClosed(firm, sh) {
      var fs = {};
      sh.forEach(function (sj, j) { fs[firm[j]] = (fs[firm[j]] || 0) + sj; });
      return sh.map(function (_, j) {
        var denom = alpha * (1 - fs[firm[j]]);
        if (!(denom > 1e-14)) throw new Error("The pricing equations cannot be solved for these inputs.");
        return 1 / denom;
      });
    }
    // Costs consistent with the first-order conditions at observed pre-merger prices
    var m0 = markup(firmPre, s), mc = p0.map(function (p, j) { return p - m0[j]; });
    var isMerged = firmPre.map(function (f) { return mergingFirms.indexOf(f) >= 0; });
    var uniqMerging = mergingFirms.filter(function (f, i, a) { return a.indexOf(f) === i; });
    var name = uniqMerging.join("+");
    // A rival that happens to carry the merged firm's name must not be absorbed into it
    while (firmPre.some(function (f, j) { return !isMerged[j] && f === name; })) name = "Merged (" + name + ")";
    var firmPost = firmPre.map(function (f, j) { return isMerged[j] ? name : f; }),
        mcPost = mc.map(function (v, j) { return isMerged[j] ? v * (1 - eff) : v; });

    // Damped fixed-point iteration; a step that would push the outside share to zero is halved
    function iterate(step0, limit) {
      var pr = p0.slice(), conv = false, it = 0;
      for (; it < limit; it++) {
        var sh = shares(pr), m;
        try { m = markupClosed(firmPost, sh); } catch (_) { return { p: pr, converged: false, iter: it }; }
        var pn = mcPost.map(function (v, j) { return v + m[j]; }),
            gap = Math.max.apply(null, pn.map(function (v, j) { return Math.abs(v - pr[j]); }));
        if (!isFinite(gap)) return { p: pr, converged: false, iter: it };
        if (gap < tol) { pr = pn; conv = true; break; }
        var cur = step0, accepted = false;
        for (var h = 0; h < 12; h++) {
          var cand = pr.map(function (v, j) { return v + cur * (pn[j] - v); }), shC = shares(cand);
          if (shC.every(isFinite) && (1 - shC.reduce(function (a, b) { return a + b; }, 0)) > 1e-14) {
            pr = cand; accepted = true; break;
          }
          cur *= 0.5;
        }
        if (!accepted) return { p: pr, converged: false, iter: it };
      }
      return { p: pr, converged: conv, iter: it };
    }
    var res = iterate(damping, maxIter);
    if (!res.converged && damping > 0.15) res = iterate(0.1, maxIter);
    var p = res.p, converged = res.converged, iter = res.iter;
    var sPost = shares(p);
    var negativeMc = [];
    mc.forEach(function (v, j) { if (v < 0) negativeMc.push(j); });
    // Consumer surplus change per unit of market size (logit inclusive value, in price units)
    return { alpha: alpha, alphaImplied: alphaJ, pricesPre: p0, pricesPost: p,
      pctChange: p.map(function (v, j) { return v / p0[j] - 1; }), sharesPre: s, sharesPost: sPost,
      mcImplied: mc, mcPost: mcPost, negativeMc: negativeMc, isMerged: isMerged,
      ownershipPost: firmPost, outsidePre: s0,
      outsidePost: 1 - sPost.reduce(function (a, b) { return a + b; }, 0),
      ownElasticity: p0.map(function (v, j) { return -alpha * v * (1 - s[j]); }),
      consumerSurplusChange: (logsum(p) - logsum(p0)) / alpha, converged: converged, iterations: iter };
  }

  var api = { solve: solve, hhi: hhi, diversion: diversion, upp: upp, simulate: simulate };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.MergerLab = api;
})(this);
