/* Birth chart maths for the browser (no server needed).
 *
 * Planet positions come from Astronomy Engine; the Ascendant and Midheaven are
 * computed from sidereal time with the standard formulas. Checked against the
 * Swiss Ephemeris (the Python calculator in chartbook/) by showcase/check_chart.js.
 *
 * Exposes `BirthChart.compute(utcDate, latitude, longitude, timeKnown)`.
 */
(function (root) {
  "use strict";
  var SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"];
  var BODIES = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"];
  var ASPECTS = [["conjunction", 0, 8], ["sextile", 60, 4], ["square", 90, 7], ["trine", 120, 7], ["opposition", 180, 8]];
  var RAD = Math.PI / 180;

  function norm(x) { x %= 360; return x < 0 ? x + 360 : x; }

  function signOf(lon) {
    lon = norm(lon);
    return { sign: SIGNS[Math.floor(lon / 30)], degree: lon % 30 };
  }

  function longitude(A, body, date) {
    return norm(A.Ecliptic(A.GeoVector(A.Body[body], date, true)).elon);
  }

  function angles(A, date, lat, lon) {
    var time = A.MakeTime(date);
    var ramc = norm(A.SiderealTime(time) * 15 + lon) * RAD;
    var eps = A.e_tilt(time).tobl * RAD;
    var phi = lat * RAD;
    var asc = Math.atan2(Math.cos(ramc), -(Math.sin(ramc) * Math.cos(eps) + Math.tan(phi) * Math.sin(eps))) / RAD;
    var mc = Math.atan2(Math.sin(ramc), Math.cos(ramc) * Math.cos(eps)) / RAD;
    return { asc: norm(asc), mc: norm(mc) };
  }

  function placement(name, lon, retro) {
    var s = signOf(lon);
    return { body: name, longitude: lon, sign: s.sign, degree: s.degree, retrograde: !!retro };
  }

  function findAspects(points) {
    var out = [];
    for (var i = 0; i < points.length; i++) {
      for (var j = i + 1; j < points.length; j++) {
        var a = points[i], b = points[j];
        var sep = Math.abs(a.longitude - b.longitude) % 360;
        if (sep > 180) sep = 360 - sep;
        for (var k = 0; k < ASPECTS.length; k++) {
          var allowed = ASPECTS[k][2] + ((a.body === "Sun" || a.body === "Moon" || b.body === "Sun" || b.body === "Moon") ? 2 : 0);
          var off = Math.abs(sep - ASPECTS[k][1]);
          if (off <= allowed) { out.push({ body1: a.body, body2: b.body, kind: ASPECTS[k][0], orb: off }); break; }
        }
      }
    }
    return out.sort(function (x, y) { return x.orb - y.orb; });
  }

  function compute(A, utcDate, lat, lon, timeKnown) {
    var hourLater = new Date(utcDate.getTime() + 3600e3);
    var planets = BODIES.map(function (name) {
      var now = longitude(A, name, utcDate);
      var later = longitude(A, name, hourLater);
      var motion = ((later - now + 540) % 360) - 180;  // signed change, handles 359 -> 0
      return placement(name, now, name !== "Sun" && name !== "Moon" && motion < 0);
    });
    var result = { planets: planets, aspects: findAspects(planets), ascendant: null, midheaven: null };
    if (timeKnown) {
      var ang = angles(A, utcDate, lat, lon);
      result.ascendant = placement("Ascendant", ang.asc, false);
      result.midheaven = placement("Midheaven", ang.mc, false);
    }
    return result;
  }

  /* Local wall-clock time in an IANA zone -> UTC Date, using the browser's own
   * time-zone database (which knows historical daylight-saving rules). Returns
   * null if that local time never happened (clocks jumped forward). */
  function zonedToUtc(year, month, day, hour, minute, timeZone) {
    var fmt = new Intl.DateTimeFormat("en-US", {
      timeZone: timeZone, hourCycle: "h23",
      year: "numeric", month: "numeric", day: "numeric", hour: "numeric", minute: "numeric", second: "numeric"
    });
    function offsetAt(ms) {
      var p = {};
      fmt.formatToParts(new Date(ms)).forEach(function (x) { p[x.type] = x.value; });
      var asUtc = Date.UTC(+p.year, +p.month - 1, +p.day, +p.hour % 24, +p.minute, +p.second);
      return asUtc - Math.floor(ms / 1000) * 1000;
    }
    var wall = Date.UTC(year, month - 1, day, hour, minute);
    var guess = wall - offsetAt(wall);
    var fixed = wall - offsetAt(guess);
    var check = fixed + offsetAt(fixed);
    if (check !== wall) return null;  // nonexistent local time
    return new Date(fixed);
  }

  root.BirthChart = {
    SIGNS: SIGNS,
    signOf: signOf,
    zonedToUtc: zonedToUtc,
    compute: function (utcDate, lat, lon, timeKnown) {
      var A = root.Astronomy || (typeof require === "function" ? require("astronomy-engine") : null);
      return compute(A, utcDate, lat, lon, timeKnown);
    }
  };
  if (typeof module === "object" && module.exports) module.exports = root.BirthChart;
})(typeof globalThis !== "undefined" ? globalThis : this);
