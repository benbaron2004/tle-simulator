import math
from datetime import datetime, timezone


# חישוב checksum לשורה
def compute_checksum(line):
    s = 0
    for c in line[:68]:  # עמודות 1–68
        if c.isdigit():
            s += int(c)
        elif c == "-":
            s += 1
    return s % 10


# epoch בפורמט YYDDD.DDDDDDDD
def datetime_to_tle_epoch(dt):
    year = dt.year % 100
    day_of_year = dt.timetuple().tm_yday
    fraction_of_day = (dt.hour * 3600 + dt.minute * 60 + dt.second + dt.microsecond / 1e6) / 86400
    return f"{year:02d}{day_of_year:03d}.{fraction_of_day:.8f}"


def makeTle():
    EARTH_RADIUS = 6378
    mu = 398600.4418  # km^3/s^2

    # פרמטרי מסלול
    h = 15000
    a = EARTH_RADIUS + h
    incl = 55.0
    ecc = 0.0
    mean_motion = math.sqrt(mu / a**3) * 86400 / (2 * math.pi)  # rev/day

    # פרמטרי מערכת לוויינים
    N = 15
    sat_base_num = 10001
    rev_number = 1

    # epoch להיום
    now = datetime.now(timezone.utc)
    epoch = datetime_to_tle_epoch(now)

    tleList = []

    for i in range(N):
        sat_num = sat_base_num + i
        mean_anomaly = (360 / N) * i
        raan = 0.0
        arg_perigee = 0.0

        ecc_str = f"{ecc:.7f}".split(".")[1]  # בלי נקודה

        # בונים שורות בפורמט נכון
        line1 = f"1 {sat_num:05d}U 00000A   {epoch}  .00000000  00000-0  00000-0 0  0000"
        line2 = f"2 {sat_num:05d} {incl:8.4f} {raan:8.4f} {ecc_str:7s} {arg_perigee:8.4f} {mean_anomaly:8.4f} {mean_motion:11.8f} {rev_number:5d}"

        # מוסיפים checksum
        line1 = line1[:68] + str(compute_checksum(line1))
        line2 = line2[:68] + str(compute_checksum(line2))

        tleList.append(f"Ben-{i+1}\n{line1}\n{line2}")

    with open("tleFiles/constellation.txt", "w") as f:
        f.write("\n".join(tleList))

makeTle()