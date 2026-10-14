// Compare the browser chart maths with Swiss Ephemeris reference values.
// Usage: node showcase/check_chart.js reference.json   (needs: npm install astronomy-engine@2.1.19)
const fs = require("fs");
const BirthChart = require("./chart.js");
const cases = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const diff = (a, b) => { const d = Math.abs(a - b) % 360; return Math.min(d, 360 - d); };
let worst = {};
let retroMismatch = 0;
for (const c of cases) {
  const r = BirthChart.compute(new Date(c.utc), c.lat, c.lon, true);
  for (const p of r.planets) {
    const [ref, retro] = c.planets[p.body];
    worst[p.body] = Math.max(worst[p.body] || 0, diff(p.longitude, ref));
    if (p.retrograde !== retro) retroMismatch++;
  }
  worst.Ascendant = Math.max(worst.Ascendant || 0, diff(r.ascendant.longitude, c.asc));
  worst.Midheaven = Math.max(worst.Midheaven || 0, diff(r.midheaven.longitude, c.mc));
}
for (const [k, v] of Object.entries(worst)) console.log(k.padEnd(10), (v * 60).toFixed(2), "arcmin max");
console.log("retrograde mismatches:", retroMismatch, "of", cases.length * 10);
const bad = Object.values(worst).some(v => v > 1 / 60 * 3);
process.exit(bad ? 1 : 0);
