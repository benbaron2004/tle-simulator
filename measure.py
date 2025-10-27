import csv
from skyfield.api import load
from datetime import datetime, timezone
import numpy as np

ts = load.timescale()
now = datetime.now(timezone.utc)


def calcAngle(vector1, vector2):
    cosBeam = np.dot(vector1, vector2) / (np.linalg.norm(vector1) * np.linalg.norm(vector2))
    return np.degrees(np.arccos(cosBeam))


def calcGdopByMinute(navLoc, satellitesLoc):
    A = []
    for satLoc in satellitesLoc:
        diff = satLoc - navLoc
        dis = np.linalg.norm(diff)
        rangeVector = diff / dis
        A.append(np.append(rangeVector, 1))

    A = np.array(A)
    if A.shape[0] < 4:
        return None, None, None

    Q = np.linalg.inv(A.T @ A)
    pdop = np.sqrt(Q[0, 0] + Q[1, 1] + Q[2, 2])
    tdop = np.sqrt(Q[3, 3])
    gdop = np.sqrt(Q[0, 0] + Q[1, 1] + Q[2, 2] + Q[3, 3])
    return pdop, tdop, gdop


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
    satellites = load.tle_file("tleFiles/Gps2.txt")
    results = []
    gdopByMinute = []

    with open("satRoute.csv", newline="", encoding="utf-8") as satRoute:
        reader = csv.DictReader(satRoute)
        for row in reader:
            visSatsByMinute = []
            xNav, yNav, zNav = float(row["x"]), float(row["y"]), float(row["z"])
            navPos = np.array([xNav, yNav, zNav])

            hour, minute = map(int, row["time"].split(":"))
            t = ts.utc(now.year, now.month, now.day, hour, minute, 0)

            for sat in satellites:
                gpsSatPos = np.array(sat.at(t).position.km)

                satsVector = gpsSatPos - navPos
                earthVector = -navPos
                el = calcAngle(satsVector, earthVector)

                gpsToEarth = -gpsSatPos  # וקטור מהלווין לכדור הארץ
                gpsToNav = navPos - gpsSatPos  # וקטור מהלווין לנווט
                beamAngle = calcAngle(gpsToNav, gpsToEarth)
                GPS_BEAM_ANGLE = 28.5

                choice = "both"  # down, up or both

                def checkChoice(el, direction_choice):
                    if direction_choice == "up":
                        return 120 <= el <= 180
                    elif direction_choice == "down":
                        return 20 <= el <= 90
                    elif direction_choice == "both":
                        return (20 <= el <= 90) or (120 <= el <= 180)

                if checkChoice(el, choice) and beamAngle <= GPS_BEAM_ANGLE:
                    dis = np.linalg.norm(satsVector)
                    xSat, ySat, zSat = gpsSatPos

                    visSatsByMinute.append(gpsSatPos)

                    results.append(
                        {"time": row["time"], "sat name": sat.name, "x": xSat, "y": ySat, "z": zSat, "el": el, "dis": dis}
                    )

            if len(visSatsByMinute) >= 4:
                pdop, tdop, gdop = calcGdopByMinute(navPos, visSatsByMinute)
                gdopByMinute.append(
                    {"time": row["time"], "satsNumber": len(visSatsByMinute), "pdop": pdop, "tdop": tdop, "gdop": gdop}
                )

    with open("gdopByMinute.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["time", "satsNumber", "pdop", "tdop", "gdop"])
        writer.writeheader()
        writer.writerows(gdopByMinute)

    with open("visibleSatsForSat.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["time", "sat name", "x", "y", "z", "el", "dis"])
        writer.writeheader()
        writer.writerows(results)

    print("visibleSatsForSat.csv created")


createSatRoute()
measureVisibleSats()


from collections import Counter
import matplotlib.pyplot as plt


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
