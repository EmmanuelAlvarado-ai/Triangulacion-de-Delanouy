from decimal import Decimal
from typing import Optional, List, Tuple

class Point:
    def __init__(self, x: float, y: float, z: float = 0.0, id_pt: int = -1):
        self.x = Decimal(str(x))
        self.y = Decimal(str(y))
        self.z = Decimal(str(z))
        self.id = id_pt

    def __eq__(self, other):
        return isinstance(other, Point) and self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))

    def __repr__(self):
        return f"P({float(self.x):.2f}, {float(self.y):.2f})"


def orient2d(p: Point, q: Point, r: Point) -> Decimal:
    """Determina si p, q, r están en sentido antihorario (CCW > 0)."""
    return (q.x - p.x) * (r.y - p.y) - (q.y - p.y) * (r.x - p.x)


def in_circle(p: Point, q: Point, r: Point, s: Point) -> bool:
    """
    Evalúa si el punto 's' cae estrictamente dentro del circuncírculo de (p, q, r).
    Garantiza internamente que p, q, r estén en orden antihorario (CCW).
    """
    if orient2d(p, q, r) < 0:
        p, q = q, p  # Forzar orden CCW para consistencia del determinante

    ax, ay = p.x - s.x, p.y - s.y
    bx, by = q.x - s.x, q.y - s.y
    cx, cy = r.x - s.x, r.y - s.y

    a2 = ax * ax + ay * ay
    b2 = bx * bx + by * by
    c2 = cx * cx + cy * cy

    det = (ax * (by * c2 - b2 * cy)
           - ay * (bx * c2 - b2 * cx)
           + a2 * (bx * cy - by * cx))
    return det > Decimal('1e-12')


class Triangle:
    def __init__(self, p1: Point, p2: Point, p3: Point):
        # Asegurar sentido antihorario (CCW) al construir el triángulo
        if orient2d(p1, p2, p3) < 0:
            p2, p3 = p3, p2
        self.vertices: List[Point] = [p1, p2, p3]
        # neighbors[i] es el triángulo opuesto al vértice i
        self.neighbors: List[Optional['Triangle']] = [None, None, None]
        self.is_active: bool = True  # Para el historial del DAG en Fase Final

    def contains_point(self, p: Point) -> bool:
        """Verifica si p está dentro o sobre las aristas del triángulo."""
        v0, v1, v2 = self.vertices
        d1 = orient2d(v0, v1, p)
        d2 = orient2d(v1, v2, p)
        d3 = orient2d(v2, v0, p)
        return d1 >= 0 and d2 >= 0 and d3 >= 0

    def edges(self) -> List[Tuple[Point, Point]]:
        v = self.vertices
        return [(v[0], v[1]), (v[1], v[2]), (v[2], v[0])]
