import csv
from skyfield.api import load
from datetime import datetime, timezone
import numpy as np
from collections import Counter
import matplotlib.pyplot as plt

ts = load.timescale()
now = datetime.now(timezone.utc)


def createSatRoute():
    satellite = load.tle_file("tleFiles/omerTle.txt")[0]
    rows = []

    for hour in range(24):
        for minute in range(60):
            t = ts.utc(now.year, now.month, now.day, hour, minute, 0)
            geo = satellite.at(t)
            rows.append({"time": f"{hour:02d}:{minute:02d}", "x": geo.xyz.km[0], "y": geo.xyz.km[1], "z": geo.xyz.km[2]})

    with open("satRoute.csv", "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["time", "x", "y", "z"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"{csvfile.name} created")


def measureVisibleSats():
    minElevation = 20
    maxElevation = 90

    satellites = load.tle_file("tleFiles/Gps.txt")
    results = []

    with open("satRoute.csv", newline="", encoding="utf-8") as satRoute:
        reader = csv.DictReader(satRoute)
        for row in reader:
            xNav, yNav, zNav = float(row["x"]), float(row["y"]), float(row["z"])
            navPos = np.array([xNav, yNav, zNav])

            hour, minute = map(int, row["time"].split(":"))
            t = ts.utc(now.year, now.month, now.day, hour, minute, 0)

            for sat in satellites:
                gpsSatPos = np.array(sat.at(t).position.km)

                satsVector = gpsSatPos - navPos
                earthVector = -navPos

                cosElevation = np.dot(satsVector, earthVector) / (np.linalg.norm(satsVector) * np.linalg.norm(earthVector))
                el = np.degrees(np.arccos(cosElevation))

                if el >= minElevation and el <= maxElevation:
                    dis = np.linalg.norm(satsVector)
                    xGps, yGps, zGps = gpsSatPos

                    results.append(
                        {"time": row["time"], "sat name": sat.name, "x": xGps, "y": yGps, "z": zGps, "el": el, "dis": dis}
                    )

    with open("visibleSatsForSat.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["time", "sat name", "x", "y", "z", "el", "dis"])
        writer.writeheader()
        writer.writerows(results)

    print("visibleSatsForSat.csv created")


createSatRoute()
measureVisibleSats()


def plotVisibleSats():
    minuteCounts = Counter()

    with open("visibleSatsForSat.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            time = row["time"]
            minuteCounts[time] += 1

    times = sorted(minuteCounts.keys())
    counts = [minuteCounts[t] for t in times]

    plt.figure(figsize=(15, 6))
    plt.plot(times, counts, marker="o", linestyle="-")
    plt.xticks(times[::30], rotation=90)
    plt.xlabel("Time (HH:MM)")
    plt.ylabel("satellites")
    plt.title("visible satellites per minute")
    plt.grid(True)
    plt.tight_layout()
    plt.show()


plotVisibleSats()
