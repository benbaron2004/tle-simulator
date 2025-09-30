import csv
from skyfield.api import load, wgs84
from datetime import datetime, timezone


def calcVisibleSats(lat, lon, minElevation, maxElevation):
    user = wgs84.latlon(lat, lon)

    satellites = load.tle_file("/Users/benbaron/Desktop/tle/tleFiles/GPS.txt")
    ts = load.timescale()

    allVisibleSats = []
    now = datetime.now(timezone.utc)

    for hour in range(24):
        for minute in range(60):
            t = ts.utc(now.year, now.month, now.day, hour, minute, 0)
            visibleSats = []
            for sat in satellites:
                difference = sat - user
                topocentric = difference.at(t)
                alt, az, distance = topocentric.altaz()
                if alt.degrees >= minElevation and alt.degrees <= maxElevation:
                    visibleSats.append(sat.name)

            allVisibleSats.append(
                {"time": f"{hour:02d}:{minute:02d}", "numVisible": len(visibleSats), "sats": ", ".join(visibleSats)}
            )

    with open("visibleSats.csv", "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["time", "numVisible", "sats"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for row in allVisibleSats:
            writer.writerow(row)

    print(f"file made successful: {csvfile.name}")
