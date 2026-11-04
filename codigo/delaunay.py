from itertools import combinations
from typing import List, Set, Tuple
from models import Point, Triangle, orient2d, in_circle

# ==========================================================
# 1. LÍNEA BASE: FUERZA BRUTA O(n^4) - 100% FUNCIONAL
# ==========================================================
def delaunay_brute_force(points: List[Point]) -> List[Triangle]:
    """
    Construye la Triangulación de Delaunay evaluando todas las ternas posibles
    y verificando la propiedad del círculo vacío contra el resto de los puntos.
    """
    n = len(points)
    valid_triangles = []

    for i, j, k in combinations(range(n), 3):
        p, q, r = points[i], points[j], points[k]
        # Ignorar ternas colineales
        if abs(orient2d(p, q, r)) < 1e-12:
            continue

        is_delaunay = True
        for m in range(n):
            if m in (i, j, k):
                continue
            if in_circle(p, q, r, points[m]):
                is_delaunay = False
                break

        if is_delaunay:
            valid_triangles.append(Triangle(p, q, r))

    return valid_triangles


# ==========================================================
# 2. ALGORITMO ÓPTIMO: INSERCIÓN INCREMENTAL + LEGALIZE_EDGE
# ==========================================================
class IncrementalDelaunay:
    def __init__(self, points: List[Point]):
        self.points = points
        self.triangles: List[Triangle] = []
        self.super_vertices = self._create_super_triangle(points)

    def _create_super_triangle(self, points: List[Point]) -> List[Point]:
        min_x = float(min(p.x for p in points))
        max_x = float(max(p.x for p in points))
        min_y = float(min(p.y for p in points))
        max_y = float(max(p.y for p in points))
        dx, dy = max_x - min_x, max_y - min_y
        delta = max(dx, dy, 1.0) * 10.0
        mid_x, mid_y = (min_x + max_x) / 2.0, (min_y + max_y) / 2.0

        sp1 = Point(mid_x - 2 * delta, mid_y - delta, id_pt=-1)
        sp2 = Point(mid_x + 2 * delta, mid_y - delta, id_pt=-2)
        sp3 = Point(mid_x, mid_y + 2 * delta, id_pt=-3)

        root_tri = Triangle(sp1, sp2, sp3)
        self.triangles.append(root_tri)
        return [sp1, sp2, sp3]

    def locate_triangle(self, p: Point) -> Triangle:
        """Subrutina de localización (en Semana 5-6 se enlaza al DAG)."""
        for tri in self.triangles:
            if tri.is_active and tri.contains_point(p):
                return tri
        raise ValueError(f"Punto {p} fuera del dominio del súper-triángulo.")

    def insert_point(self, p: Point):
        """Inserta un punto p, divide el triángulo en 3 y legaliza las aristas."""
        t = self.locate_triangle(p)
        t.is_active = False
        v0, v1, v2 = t.vertices
        n0, n1, n2 = t.neighbors

        # Crear los 3 nuevos sub-triángulos
        t0 = Triangle(p, v1, v2)
        t1 = Triangle(p, v2, v0)
        t2 = Triangle(p, v0, v1)

        # Conectar adyacencias internas y externas
        t0.neighbors = [n0, t1, t2]
        t1.neighbors = [n1, t2, t0]
        t2.neighbors = [n2, t0, t1]

        self._replace_neighbor(n0, t, t0)
        self._replace_neighbor(n1, t, t1)
        self._replace_neighbor(n2, t, t2)

        self.triangles.extend([t0, t1, t2])

        # Legalizar las 3 aristas opuestas al nuevo punto p
        self.legalize_edge(p, t0, 0)
        self.legalize_edge(p, t1, 0)
        self.legalize_edge(p, t2, 0)

    def _replace_neighbor(self, neighbor: Triangle, old_t: Triangle, new_t: Triangle):
        if neighbor is not None:
            for i in range(3):
                if neighbor.neighbors[i] is old_t:
                    neighbor.neighbors[i] = new_t
                    break

    def legalize_edge(self, pr: Point, tri: Triangle, edge_idx: int):
        """
        Subrutina recursiva que verifica la condición in-circle con el vecino
        opuesto y ejecuta un Edge Flip en O(1) si la arista es ilegal.
        """
        neighbor = tri.neighbors[edge_idx]
        if neighbor is None or not neighbor.is_active:
            return

        # Encontrar el índice del vértice opuesto en el triángulo vecino
        opp_idx = neighbor.neighbors.index(tri)
        pl = neighbor.vertices[opp_idx]

        v0, v1, v2 = tri.vertices
        if in_circle(v0, v1, v2, pl):
            # Desactivar triángulos actuales (para historial futuro del DAG)
            tri.is_active = False
            neighbor.is_active = False

            # Vértices de la arista compartida (pi, pj) en orden CCW de tri
            pi = tri.vertices[(edge_idx + 1) % 3]
            pj = tri.vertices[(edge_idx + 2) % 3]

            # Vecinos externos que se deben preservar tras el flip
            n_tri_1 = tri.neighbors[(edge_idx + 1) % 3]      # opuesto a pi en tri
            n_tri_2 = tri.neighbors[(edge_idx + 2) % 3]      # opuesto a pj en tri
            n_nb_1 = neighbor.neighbors[(opp_idx + 1) % 3]   # opuesto a pj en neighbor
            n_nb_2 = neighbor.neighbors[(opp_idx + 2) % 3]   # opuesto a pi en neighbor

            # Crear los 2 nuevos triángulos volteando la arista (pi, pj) -> (pr, pl)
            new_t1 = Triangle(pr, pi, pl)
            new_t2 = Triangle(pr, pl, pj)

            # Actualizar punteros de vecinos en O(1)
            new_t1.neighbors = [n_nb_1, new_t2, n_tri_2]
            new_t2.neighbors = [n_nb_2, n_tri_1, new_t1]

            self._replace_neighbor(n_nb_1, neighbor, new_t1)
            self._replace_neighbor(n_tri_2, tri, new_t1)
            self._replace_neighbor(n_nb_2, neighbor, new_t2)
            self._replace_neighbor(n_tri_1, tri, new_t2)

            self.triangles.extend([new_t1, new_t2])

            # Llamadas recursivas sobre las dos aristas externas frente a pr
            self.legalize_edge(pr, new_t1, 0)
            self.legalize_edge(pr, new_t2, 0)

    def get_active_triangles(self, remove_super: bool = True) -> List[Triangle]:
        active = [t for t in self.triangles if t.is_active]
        if not remove_super:
            return active
        return [
            t for t in active
            if not any(v in self.super_vertices for v in t.vertices)
        ]
