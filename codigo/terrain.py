import math
import random
from typing import List
from models import Point


def generate_synthetic_terrain(n: int, width: float, height: float,
                               eps: float = 1e-7, seed: int = None) -> List[Point]:
    """
    Genera 'n' puntos con elevación Z simulando colinas y valles.
    Cada coordenada recibe una perturbación microscópica (±eps) para evitar
    degeneraciones (3 colineales / 4 co-circulares), como pide el protocolo.
    """
    rng = random.Random(seed)
    points = []
    for i in range(n):
        x = rng.uniform(0, width) + rng.uniform(-eps, eps)
        y = rng.uniform(0, height) + rng.uniform(-eps, eps)
        # Función de relieve para el terreno
        z = math.sin(x * 0.5) * math.cos(y * 0.5) * 5.0
        points.append(Point(x, y, z, id_pt=i))
    return points
