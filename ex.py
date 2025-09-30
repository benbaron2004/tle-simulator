import numpy as np

v = np.array([1, 0])

vectors = [
    np.array([np.sqrt(3) / 2, 1 / 2]),
    np.array([1 / 2, np.sqrt(3) / 2]),
    np.array([0, 1]),
    np.array([-1 / 2, np.sqrt(3) / 2]),
    np.array([-np.sqrt(3) / 2, 1 / 2]),
    np.array([-1, 0]),
    np.array([-np.sqrt(3) / 2, -1 / 2]),
    np.array([-1 / 2, -np.sqrt(3) / 2]),
    np.array([0, -1]),
    np.array([1 / 2, -np.sqrt(3) / 2]),
    np.array([np.sqrt(3) / 2, -1 / 2]),
    np.array([1, 0])
]

for i, vector in enumerate(vectors):
    scalar = np.dot(v, vector)
    cosEngle = scalar / (np.linalg.norm(v) * np.linalg.norm(vector))
    angle = np.degrees(np.arccos(cosEngle))
    print(f"scalar: {scalar}, angle: {angle:.2f}")
