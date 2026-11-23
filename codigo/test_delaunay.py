import unittest
from models import Point, Triangle, in_circle, orient2d
from delaunay import delaunay_brute_force, IncrementalDelaunay
from terrain import generate_synthetic_terrain


def vertices_set(tris):
    return {frozenset(t.vertices) for t in tris}


class TestDelaunayHitoIntermedio(unittest.TestCase):
    def test_in_circle_determinant(self):
        p1, p2, p3 = Point(0, 0), Point(4, 0), Point(0, 4)
        inside_pt = Point(1, 1)
        outside_pt = Point(5, 5)
        self.assertTrue(in_circle(p1, p2, p3, inside_pt))
        self.assertFalse(in_circle(p1, p2, p3, outside_pt))

    def test_brute_force_vs_incremental_equivalence(self):
        # Instancia pequeña en posición general (sin 4 puntos co-circulares)
        pts = [
            Point(0.0, 0.0), Point(5.0, 0.2), Point(4.8, 5.1),
            Point(0.3, 4.7), Point(2.1, 1.9), Point(3.4, 3.2)
        ]
        bf_tris = delaunay_brute_force(pts)

        inc = IncrementalDelaunay(pts)
        for p in pts:
            inc.insert_point(p)
        inc_tris = inc.get_active_triangles(remove_super=True)

        # Comparar conjuntos de triángulos por sus vértices
        bf_set = {frozenset(t.vertices) for t in bf_tris}
        inc_set = {frozenset(t.vertices) for t in inc_tris}

        self.assertEqual(len(bf_set), len(inc_set))
        self.assertEqual(bf_set, inc_set)


class TestDelaunayHitoFinal(unittest.TestCase):
    def test_in_circle_estricto_y_robusto(self):
        p, q, r = Point(0, 0), Point(1, 0), Point(0, 1)   # circuncírculo: centro (.5,.5), radio √.5
        self.assertFalse(in_circle(p, q, r, Point(1, 1)))          # exactamente SOBRE el círculo: no es "dentro"
        self.assertFalse(in_circle(p, q, r, Point(1, 1.0000000000000002)))  # apenas fuera
        self.assertTrue(in_circle(p, q, r, Point(0.9, 0.9)))       # claramente dentro
        # el orden de p,q,r no debe cambiar la respuesta
        self.assertEqual(in_circle(p, q, r, Point(0.9, 0.9)), in_circle(q, p, r, Point(0.9, 0.9)))

    def test_nivel1_dag_y_lineal_igual_a_fuerza_bruta(self):
        for n in (10, 25, 50):
            for seed in range(3):
                pts = generate_synthetic_terrain(n, 20, 20, seed=seed * 7 + n)
                ref = vertices_set(delaunay_brute_force(pts))
                with self.subTest(n=n, seed=seed):
                    self.assertEqual(vertices_set(IncrementalDelaunay(pts, True).build(seed=seed)), ref)
                    self.assertEqual(vertices_set(IncrementalDelaunay(pts, False).build(seed=seed)), ref)

    def test_independiente_del_orden_de_insercion(self):
        pts = generate_synthetic_terrain(40, 20, 20, seed=3)
        a = vertices_set(IncrementalDelaunay(pts).build(seed=1))
        b = vertices_set(IncrementalDelaunay(pts).build(seed=99))
        self.assertEqual(a, b)

    def test_propiedad_del_circulo_vacio(self):
        pts = generate_synthetic_terrain(120, 50, 50, seed=11)
        tris = IncrementalDelaunay(pts).build(seed=0)
        for t in tris:
            for p in pts:
                if p not in t.vertices:
                    self.assertFalse(in_circle(*t.vertices, p))

    def test_triangulacion_valida_ccw_y_area_total(self):
        pts = generate_synthetic_terrain(80, 30, 30, seed=5)
        tris = IncrementalDelaunay(pts).build(seed=0)
        self.assertTrue(all(orient2d(*t.vertices) > 0 for t in tris))
        # Fórmula de Euler: T = 2n - 2 - h  (h = vértices de la envolvente) => T <= 2n - 5
        self.assertLessEqual(len(tris), 2 * len(pts) - 5)
        self.assertGreaterEqual(len(tris), len(pts) - 2)

    def test_supertriangulo_removido(self):
        pts = generate_synthetic_terrain(30, 20, 20, seed=2)
        inc = IncrementalDelaunay(pts)
        tris = inc.build(seed=0)
        for t in tris:
            self.assertFalse(any(v in inc.super_vertices for v in t.vertices))
        usados = {v for t in tris for v in t.vertices}
        self.assertEqual(usados, set(pts))     # todos los puntos quedan en la malla

    def test_adyacencias_consistentes(self):
        pts = generate_synthetic_terrain(60, 20, 20, seed=8)
        inc = IncrementalDelaunay(pts)
        inc.build(seed=0)
        for t in inc.get_active_triangles(remove_super=False):
            for i, nb in enumerate(t.neighbors):
                if nb is None:
                    continue
                self.assertTrue(nb.is_active)
                self.assertIn(t, nb.neighbors)              # bidireccional
                compartidos = set(t.vertices) & set(nb.vertices)
                self.assertEqual(len(compartidos), 2)       # comparten una arista
                self.assertNotIn(t.vertices[i], nb.vertices)  # neighbors[i] es opuesto al vértice i

    def test_dag_localiza_hoja_activa_que_contiene_al_punto(self):
        pts = generate_synthetic_terrain(50, 20, 20, seed=4)
        inc = IncrementalDelaunay(pts)
        inc.build(seed=0)
        q = Point(10.123456, 9.654321)
        hoja = inc.locate_triangle(q)
        self.assertTrue(hoja.is_active and hoja.contains_point(q))

    def test_punto_duplicado_se_ignora(self):
        pts = generate_synthetic_terrain(15, 20, 20, seed=6)
        inc = IncrementalDelaunay(pts)
        for p in pts:
            inc.insert_point(p)
        antes = len(inc.get_active_triangles())
        self.assertFalse(inc.insert_point(Point(float(pts[0].x), float(pts[0].y))))
        self.assertEqual(len(inc.get_active_triangles()), antes)

    def test_metricas_dag_mejor_que_lineal(self):
        pts = generate_synthetic_terrain(300, 50, 50, seed=9)
        dag = IncrementalDelaunay(pts, True); dag.build(seed=0)
        lin = IncrementalDelaunay(pts, False); lin.build(seed=0)
        self.assertLess(dag.locate_steps * 5, lin.locate_steps)
        self.assertLess(dag.stats()["flips_por_punto"], 5)

    def test_eventos_para_animacion(self):
        eventos = []
        pts = generate_synthetic_terrain(10, 20, 20, seed=1)
        inc = IncrementalDelaunay(pts, on_event=lambda k, p, t: eventos.append(k))
        inc.build(seed=0)
        self.assertEqual(eventos.count('split'), 10)
        self.assertEqual(eventos.count('flip'), inc.flips)


if __name__ == "__main__":
    unittest.main()
