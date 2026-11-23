import random
from itertools import combinations
from typing import Callable, List, Optional, Tuple
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
# 2. ALGORITMO ÓPTIMO: RIC = INSERCIÓN INCREMENTAL ALEATORIZADA
#    + LEGALIZE_EDGE + DAG DE LOCALIZACIÓN
# ==========================================================
class IncrementalDelaunay:
    """
    use_dag=True  -> localización por descenso en el DAG, O(log n) esperado.
    use_dag=False -> búsqueda lineal (solo para comparar en el benchmark).
    on_event(kind, punto, triángulos_nuevos) se invoca tras cada división
    ('split') y tras cada edge flip ('flip'); lo usa la visualización paso a paso.
    """

    # El súper-triángulo se hace MUY grande: así los triángulos de la envolvente
    # convexa real no quedan "tapados" por sus vértices ficticios.
    SUPER_FACTOR = 1000.0

    def __init__(self, points: List[Point], use_dag: bool = True,
                 on_event: Optional[Callable] = None):
        self.points = points
        self.use_dag = use_dag
        self.on_event = on_event
        self.triangles: List[Triangle] = []
        self.root: Optional[Triangle] = None
        self.super_vertices = self._create_super_triangle(points)
        # Métricas para el Nivel 3 del benchmark
        self.inserted = 0
        self.legalize_calls = 0
        self.flips = 0
        self.locate_steps = 0

    # ---------- construcción ----------
    def _create_super_triangle(self, points: List[Point]) -> List[Point]:
        min_x = float(min(p.x for p in points))
        max_x = float(max(p.x for p in points))
        min_y = float(min(p.y for p in points))
        max_y = float(max(p.y for p in points))
        dx, dy = max_x - min_x, max_y - min_y
        delta = max(dx, dy, 1.0) * self.SUPER_FACTOR
        mid_x, mid_y = (min_x + max_x) / 2.0, (min_y + max_y) / 2.0

        sp1 = Point(mid_x - 2 * delta, mid_y - delta, id_pt=-1)
        sp2 = Point(mid_x + 2 * delta, mid_y - delta, id_pt=-2)
        sp3 = Point(mid_x, mid_y + 2 * delta, id_pt=-3)

        root_tri = Triangle(sp1, sp2, sp3)
        self.triangles.append(root_tri)
        self.root = root_tri
        return [sp1, sp2, sp3]

    def build(self, shuffle: bool = True, seed: Optional[int] = None) -> List[Triangle]:
        """RIC completo: orden aleatorio + inserciones + remoción del súper-triángulo."""
        order = list(self.points)
        if shuffle:
            random.Random(seed).shuffle(order)
        for p in order:
            self.insert_point(p)
        return self.get_active_triangles(remove_super=True)

    # ---------- localización ----------
    def locate_triangle(self, p: Point) -> Triangle:
        if self.use_dag:
            return self._locate_dag(p)
        return self._locate_linear(p)

    def _locate_dag(self, p: Point) -> Triangle:
        """Desciende por el DAG desde la raíz; cada salto es un nivel de historia."""
        node = self.root
        if not node.contains_point(p):
            raise ValueError(f"Punto {p} fuera del dominio del súper-triángulo.")
        while node.children:
            for child in node.children:
                if child.contains_point(p):
                    node = child
                    self.locate_steps += 1
                    break
            else:  # no debería ocurrir con aritmética exacta
                raise ValueError(f"DAG inconsistente al ubicar {p}.")
        return node

    def _locate_linear(self, p: Point) -> Triangle:
        for tri in self.triangles:
            self.locate_steps += 1
            if tri.is_active and tri.contains_point(p):
                return tri
        raise ValueError(f"Punto {p} fuera del dominio del súper-triángulo.")

    # ---------- inserción ----------
    def insert_point(self, p: Point) -> bool:
        """Inserta p, divide su triángulo en 3 y legaliza. False si p ya existía."""
        t = self.locate_triangle(p)
        if any(p == v for v in t.vertices):
            return False  # punto duplicado: se ignora

        t.is_active = False
        v0, v1, v2 = t.vertices
        n0, n1, n2 = t.neighbors

        # Crear los 3 nuevos sub-triángulos
        t0 = Triangle(p, v1, v2)
        t1 = Triangle(p, v2, v0)
        t2 = Triangle(p, v0, v1)
        t.children = [t0, t1, t2]  # arista del DAG

        # Conectar adyacencias internas y externas
        t0.neighbors = [n0, t1, t2]
        t1.neighbors = [n1, t2, t0]
        t2.neighbors = [n2, t0, t1]

        self._replace_neighbor(n0, t, t0)
        self._replace_neighbor(n1, t, t1)
        self._replace_neighbor(n2, t, t2)

        self.triangles.extend([t0, t1, t2])
        self.inserted += 1
        self._emit('split', p, [t0, t1, t2])

        # Legalizar las 3 aristas opuestas al nuevo punto p
        self.legalize_edge(p, t0, 0)
        self.legalize_edge(p, t1, 0)
        self.legalize_edge(p, t2, 0)
        return True

    def _emit(self, kind: str, p: Point, tris: List[Triangle]):
        if self.on_event is not None:
            self.on_event(kind, p, tris)

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
        self.legalize_calls += 1
        neighbor = tri.neighbors[edge_idx]
        if neighbor is None or not neighbor.is_active:
            return

        # Encontrar el índice del vértice opuesto en el triángulo vecino
        opp_idx = neighbor.neighbors.index(tri)
        pl = neighbor.vertices[opp_idx]

        v0, v1, v2 = tri.vertices
        if in_circle(v0, v1, v2, pl):
            # Desactivar triángulos actuales (quedan como nodos del DAG)
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

            # Los dos triángulos viejos apuntan a los dos nuevos en el DAG
            tri.children = [new_t1, new_t2]
            neighbor.children = [new_t1, new_t2]

            # Actualizar punteros de vecinos en O(1)
            new_t1.neighbors = [n_nb_1, new_t2, n_tri_2]
            new_t2.neighbors = [n_nb_2, n_tri_1, new_t1]

            self._replace_neighbor(n_nb_1, neighbor, new_t1)
            self._replace_neighbor(n_tri_2, tri, new_t1)
            self._replace_neighbor(n_nb_2, neighbor, new_t2)
            self._replace_neighbor(n_tri_1, tri, new_t2)

            self.triangles.extend([new_t1, new_t2])
            self.flips += 1
            self._emit('flip', pr, [new_t1, new_t2])

            # Llamadas recursivas sobre las dos aristas externas frente a pr
            self.legalize_edge(pr, new_t1, 0)
            self.legalize_edge(pr, new_t2, 0)

    # ---------- resultados ----------
    def get_active_triangles(self, remove_super: bool = True) -> List[Triangle]:
        active = [t for t in self.triangles if t.is_active]
        if not remove_super:
            return active
        return [
            t for t in active
            if not any(v in self.super_vertices for v in t.vertices)
        ]

    def stats(self) -> dict:
        n = max(self.inserted, 1)
        return {
            "n": self.inserted,
            "flips_por_punto": self.flips / n,
            "legalize_por_punto": self.legalize_calls / n,
            "profundidad_busqueda": self.locate_steps / n,
        }
