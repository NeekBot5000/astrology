/* Chart wheel as SVG, a browser port of chartbook/wheel.py (same glyphs and layout,
 * without houses). Exposes `ChartWheel.render(chart, title)` -> SVG string. */
(function (root) {
  "use strict";
  var GLYPHS = {"signs": {"Aries": "M12 21 V9 M12 9 C12 3 4 2.5 4 8 C4 10 5 11 6.5 11 M12 9 C12 3 20 2.5 20 8 C20 10 19 11 17.5 11", "Taurus": "M7 15 a5 5 0 1 0 10 0 a5 5 0 1 0 -10 0 M4 4 C5 8 8 10 12 10 C16 10 19 8 20 4", "Gemini": "M5 4 C9 6 15 6 19 4 M5 20 C9 18 15 18 19 20 M9 5.4 V18.6 M15 5.4 V18.6", "Cancer": "M19.5 8.5 C17 4.5 9 4 7.5 6 M5.0 8.5 a2.5 2.5 0 1 0 5.0 0 a2.5 2.5 0 1 0 -5.0 0 M4.5 15.5 C7 19.5 15 20 16.5 18 M14.0 15.5 a2.5 2.5 0 1 0 5.0 0 a2.5 2.5 0 1 0 -5.0 0", "Leo": "M5.5 15.5 a2.5 2.5 0 1 0 5.0 0 a2.5 2.5 0 1 0 -5.0 0 M10.5 15.5 C10.5 11 8 9 9 6 C10 3 16 3 16 7 C16 11 12.5 14 13 17.5 C13.5 20.5 16.5 20.5 18.5 18.5", "Virgo": "M4 7 V18 M4 9.5 C4 6 9 6 9 9.5 V18 M9 9.5 C9 6 14 6 14 9.5 V17 C14 20.5 19.5 20 19.5 15 C19.5 11.5 15.5 12 14 15", "Libra": "M4 20 H20 M4 16 H8.5 C6 13 8 7 12 7 C16 7 18 13 15.5 16 H20", "Scorpio": "M4 7 V18 M4 9.5 C4 6 9 6 9 9.5 V18 M9 9.5 C9 6 14 6 14 9.5 V17 C14 19.5 16.5 19.5 19.5 17 M16.8 16 L19.5 17 L18.6 19.8", "Sagittarius": "M5 19 L19 5 M12.5 5 H19 V11.5 M8 11 L13 16", "Capricorn": "M3.5 6.5 C5.5 6 7 7.5 7 10 V18 M7 10 C7 6 12 6 12 10 V15 C12 20 18.5 20 18.5 16 C18.5 13 14.5 12.5 13.3 15 C12.3 17.5 10.5 20 8 20.5", "Aquarius": "M3 10 L6 7 L9 10 L12 7 L15 10 L18 7 L21 10 M3 17 L6 14 L9 17 L12 14 L15 17 L18 14 L21 17", "Pisces": "M5 4 C10 8 10 16 5 20 M19 4 C14 8 14 16 19 20 M6.5 12 H17.5"}, "bodies": {"Sun": "M4.5 12 a7.5 7.5 0 1 0 15.0 0 a7.5 7.5 0 1 0 -15.0 0 M11 12 a1 1 0 1 0 2 0 a1 1 0 1 0 -2 0", "Moon": "M15 3.5 A8.5 8.5 0 1 0 15 20.5 A7 7 0 1 1 15 3.5 Z", "Mercury": "M8 11 a4 4 0 1 0 8 0 a4 4 0 1 0 -8 0 M8 3.5 C8.5 6.5 15.5 6.5 16 3.5 M12 15 V22 M9 19 H15", "Venus": "M7 8.5 a5 5 0 1 0 10 0 a5 5 0 1 0 -10 0 M12 13.5 V22 M8.5 18.5 H15.5", "Mars": "M4 15 a5 5 0 1 0 10 0 a5 5 0 1 0 -10 0 M12.5 11.5 L19.5 4.5 M14 4.5 H19.5 V10", "Jupiter": "M5 8 C5 3.5 11.5 3.5 10.5 8 C9.5 11 6.5 14 4 16 H18.5 M14.5 4 V21", "Saturn": "M7 3 V16 M4 6 H10 M7 11.5 C8 8 15 8 15 12 C15 15 11 16 11 19 C11 21 13 21.5 14.5 20", "Uranus": "M7 16 a5 5 0 1 0 10 0 a5 5 0 1 0 -10 0 M11 16 a1 1 0 1 0 2 0 a1 1 0 1 0 -2 0 M12 11 V3 M9 6 L12 3 L15 6", "Neptune": "M5 5 C5 12 8 14 12 14 C16 14 19 12 19 5 M12 3 V21 M8.5 18 H15.5", "Pluto": "M5 5 C5 12.5 19 12.5 19 5 M9.5 6.5 a2.5 2.5 0 1 0 5.0 0 a2.5 2.5 0 1 0 -5.0 0 M12 11.5 V21 M8.5 17.5 H15.5", "North Node": "M7 16 C3 12 5 5 12 5 C19 5 21 12 17 16 M5 18 a2 2 0 1 0 4 0 a2 2 0 1 0 -4 0 M15 18 a2 2 0 1 0 4 0 a2 2 0 1 0 -4 0"}};
  var SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"];
  var ELEMENT = ["fire", "earth", "air", "water"];
  var FILL = { fire: "#f6e3d8", earth: "#e6eadb", air: "#e8e6f2", water: "#dde9ef" };
  var INK = "#2b2a33", MUTED = "#6d6a78", EASY = "#3b7d6e", HARD = "#b2533e";
  var DASH = { trine: "", sextile: "4 3", square: "", opposition: "8 3" };

  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function f(n) { return n.toFixed(2); }

  function spread(lons, gap) {
    var order = lons.map(function (_, i) { return i; }).sort(function (a, b) { return lons[a] - lons[b]; });
    var pos = order.map(function (i) { return lons[i]; });
    for (var it = 0; it < 50 && pos.length > 1; it++) {
      var moved = false;
      for (var k = 0; k < pos.length; k++) {
        var n = (k + 1) % pos.length;
        var g = ((pos[n] - pos[k]) % 360 + 360) % 360;
        if (g < gap) { var push = (gap - g) / 2; pos[k] -= push; pos[n] += push; moved = true; }
      }
      if (!moved) break;
    }
    var out = [];
    order.forEach(function (i, k) { out[i] = ((pos[k] % 360) + 360) % 360; });
    return out;
  }

  function glyph(d, x, y, size, color, stroke) {
    var s = size / 24;
    return '<path d="' + d + '" transform="translate(' + f(x - 12 * s) + " " + f(y - 12 * s) + ") scale(" + s.toFixed(4) +
      ')" fill="none" stroke="' + color + '" stroke-width="' + f(stroke / s) + '" stroke-linecap="round" stroke-linejoin="round"/>';
  }

  function render(chart, title) {
    var size = 600, cx = 300, cy = 300;
    var rOut = size * 0.452, rSign = size * 0.378, rPlanet = size * 0.325, rDeg = size * 0.279, rAsp = size * 0.222;
    var asc = chart.ascendant ? chart.ascendant.longitude : 0;
    function ang(lon) { return 180 + (lon - asc); }
    function polar(r, a) { a = a * Math.PI / 180; return [cx + r * Math.cos(a), cy - r * Math.sin(a)]; }
    function line(p, q, color, width, extra) {
      return '<line x1="' + f(p[0]) + '" y1="' + f(p[1]) + '" x2="' + f(q[0]) + '" y2="' + f(q[1]) + '" stroke="' + color + '" stroke-width="' + width + '"' + (extra || "") + "/>";
    }
    function text(p, s, sizePx, color, weight) {
      return '<text x="' + f(p[0]) + '" y="' + f(p[1]) + '" font-size="' + sizePx + '" fill="' + color + '"' + (weight ? ' font-weight="' + weight + '"' : "") +
        ' text-anchor="middle" dominant-baseline="central" font-family="Helvetica, Arial, sans-serif">' + esc(s) + "</text>";
    }
    var o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" role="img" aria-label="' + esc(title) + '">',
      '<circle cx="300" cy="300" r="' + rOut + '" fill="#fbfaf7" stroke="' + INK + '" stroke-width="1.5"/>'];
    SIGNS.forEach(function (sign, i) {
      var a0 = ang(i * 30), a1 = ang(i * 30 + 30);
      var p0 = polar(rOut, a0), p1 = polar(rOut, a1), p2 = polar(rSign, a1), p3 = polar(rSign, a0);
      o.push('<path d="M' + f(p0[0]) + "," + f(p0[1]) + " A" + rOut + "," + rOut + " 0 0 0 " + f(p1[0]) + "," + f(p1[1]) +
        " L" + f(p2[0]) + "," + f(p2[1]) + " A" + rSign + "," + rSign + " 0 0 1 " + f(p3[0]) + "," + f(p3[1]) +
        ' Z" fill="' + FILL[ELEMENT[i % 4]] + '" stroke="' + INK + '" stroke-width="0.8"/>');
      var g = polar((rOut + rSign) / 2, ang(i * 30 + 15));
      o.push(glyph(GLYPHS.signs[sign], g[0], g[1], 27, INK, 1.6));
      for (var d = 0; d < 30; d += 5) o.push(line(polar(rSign, ang(i * 30 + d)), polar(rSign + (d ? 7 : 12), ang(i * 30 + d)), INK, 0.6));
    });
    o.push('<circle cx="300" cy="300" r="' + rSign + '" fill="#ffffff" stroke="' + INK + '" stroke-width="1"/>');
    o.push('<circle cx="300" cy="300" r="' + rAsp + '" fill="none" stroke="' + MUTED + '" stroke-width="0.6"/>');
    if (chart.ascendant) {
      [[chart.ascendant.longitude, "AC"], [chart.midheaven.longitude, "MC"]].forEach(function (pair) {
        o.push(line(polar(rAsp, ang(pair[0])), polar(rOut, ang(pair[0])), INK, 1.6));
        o.push(line(polar(rAsp, ang(pair[0] + 180)), polar(rSign, ang(pair[0] + 180)), INK, 0.9));
        o.push(text(polar(rOut + 17, ang(pair[0])), pair[1], 14, INK, 600));
      });
    }
    var lonOf = {};
    chart.planets.forEach(function (p) { lonOf[p.body] = p.longitude; });
    chart.aspects.forEach(function (a) {
      if (a.kind === "conjunction") return;
      var color = (a.kind === "trine" || a.kind === "sextile") ? EASY : HARD;
      var op = Math.max(0.35, 1 - a.orb / 8).toFixed(2);
      o.push(line(polar(rAsp, ang(lonOf[a.body1])), polar(rAsp, ang(lonOf[a.body2])), color, 1.1,
        ' stroke-opacity="' + op + '"' + (DASH[a.kind] ? ' stroke-dasharray="' + DASH[a.kind] + '"' : "")));
    });
    var shown = spread(chart.planets.map(function (p) { return p.longitude; }), 7.5);
    chart.planets.forEach(function (p, i) {
      o.push(line(polar(rSign, ang(p.longitude)), polar(rSign - 11, ang(p.longitude)), INK, 1.4));
      var dot = polar(rAsp, ang(p.longitude));
      o.push('<circle cx="' + f(dot[0]) + '" cy="' + f(dot[1]) + '" r="3" fill="' + INK + '"/>');
      var g = polar(rPlanet, ang(shown[i]));
      o.push("<g><title>" + esc(p.body + " " + Math.floor(p.degree) + "° " + p.sign + (p.retrograde ? " (retrograde)" : "")) + "</title>" +
        glyph(GLYPHS.bodies[p.body], g[0], g[1], 27, INK, 1.7) + "</g>");
      o.push(text(polar(rDeg, ang(shown[i])), Math.floor(p.degree) + "°" + (p.retrograde ? "r" : ""), 11.4, MUTED));
    });
    o.push("</svg>");
    return o.join("\n");
  }

  root.ChartWheel = { render: render };
  if (typeof module === "object" && module.exports) module.exports = root.ChartWheel;
})(typeof globalThis !== "undefined" ? globalThis : this);
