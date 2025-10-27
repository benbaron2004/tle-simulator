import numpy as np
import sympy as sp
import matplotlib.pyplot as plt


def calcSatelliteDerivative(satelliteLoc, guessLocation):
    xS, yS, zS = satelliteLoc
    Xu, yU, zU = guessLocation

    distance = np.sqrt((Xu - xS) ** 2 + (yU - yS) ** 2 + (zU - zS) ** 2)

    x, y, z = sp.symbols("x,y,z")
    Δx, Δy, Δz = sp.symbols("Δx ,Δy, Δz")
    variables = [Δx, Δy, Δz]

    func = sp.sqrt((x - xS) ** 2 + (y - yS) ** 2 + (z - zS) ** 2)

    derivatives = [sp.diff(func, var) for var in (x, y, z)]
    subs = [deriv.subs({x: Xu, y: yU, z: zU}) for deriv in derivatives]

    return distance + sum((s * v) for s, v in zip(subs, variables))


def errorEquation(rangeByTime, equation):
    return sp.Eq(rangeByTime, equation)


def MakeMatrix(equations):
    delta_x, delta_y, delta_z = sp.symbols("Δx Δy Δz")
    variables = [delta_x, delta_y, delta_z]

    matrix = []

    for eq in equations:
        simplified_eq = sp.simplify(eq.lhs - eq.rhs)
        coefficients = [simplified_eq.coeff(var) for var in variables]
        result = -simplified_eq.subs({delta_x: 0, delta_y: 0, delta_z: 0})
        matrix.append(coefficients + [result])

    return np.array(matrix, dtype=float)


def matrixSolving(matrix):
    A = matrix[:, :-1]
    B = matrix[:, -1]
    return np.linalg.solve(A, B)


satellites = [
    (4000, 3000, 20000),
    (-2000, 5000, 19000),
    (2000, -2000, 22000),
]
guessLocation = (20, 440, 0)
t = [0.0699705, 0.0668086, 0.076351045]
lightSpeed = 300000

rangesByTimes = np.array(t) * lightSpeed
print("ranges:", rangesByTimes)
iterations = 4
errors = []

for _ in range(iterations):
    derivatives = [calcSatelliteDerivative(sat, guessLocation) for sat in satellites]

    errorEquations = [errorEquation(rangeTime, derivative) for rangeTime, derivative in zip(rangesByTimes, derivatives)]

    matrix = MakeMatrix(errorEquations)
    changes = matrixSolving(matrix)

    prevGuessLocation = guessLocation
    guessLocation = tuple((guess + change) for guess, change in zip(guessLocation, changes))

    error = np.linalg.norm(np.array(guessLocation) - np.array(prevGuessLocation))

    errors.append(error)

print("errors", errors)
print("the location:", np.round(guessLocation, 2))
print(
    f"dis real loc and sat1: {round(np.linalg.norm(np.array(guessLocation) - np.array(satellites[0])), 2)}",
)

plt.plot(range(iterations), errors, marker="o", color="b")
plt.xlabel("iterations")
plt.ylabel("Error distance")
plt.show()
