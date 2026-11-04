import unittest
from models import Point, in_circle
from delaunay import delaunay_brute_force, IncrementalDelaunay

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

if __name__ == "__main__":
    unittest.main()
