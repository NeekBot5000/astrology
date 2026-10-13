# Progress log

Newest entries go at the top. Each entry: date, what was done, what was verified, what is next.

## 2026-10-13: Milestone 1 done (birth-chart calculator) + founder forecast
- Built `chartbook/`, a Python birth-chart calculator using the Swiss Ephemeris (the standard planet-position library). From a birth date, time and place it works out the sign and degree of the Sun, Moon, planets and North Node, retrograde motion (when a planet appears to move backwards), the 12 houses (Placidus, switching to whole-sign near the poles), the Ascendant and Midheaven, and the major aspects (angles between planets).
- Handles historical time zones and daylight saving, refuses birth times that didn't exist or happened twice when clocks changed, and supports an unknown birth time (houses are left out, with a note).
- Verified with 10 automated tests (`pytest`), all passing. Einstein's chart matches the published reference values to the arcminute, and the Sun sits at exactly 0° Aries / 0° Cancer at the 2024 equinox and the 2025 solstice.
- NOT verified: looking up places by name (OpenStreetMap). The build sandbox blocks that network call. Entering latitude and longitude directly works.
- Wrote `docs/FORECAST.md`, the founder-style forecast. New risk found: the Swiss Ephemeris license (AGPL) means either publishing the site's code or buying a professional license. The owner has to decide.
- Next: milestone 2, the chart wheel SVG image.

## 2026-10-13: Repo created
- Created the repository with the project brief, instructions for Claude Code, and this log.
- Nothing is built yet.
- Next: milestone 1, a birth-chart calculator that works from date, time and place, with tests against a few known charts.
