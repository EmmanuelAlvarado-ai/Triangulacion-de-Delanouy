"""
Benchmark empírico (Hito 4) según el protocolo experimental de 3 niveles.

  Nivel 1  Exactitud lógica: n in {10, 25, 50}, fuerza bruta vs RIC (DAG y lineal).
  Nivel 2  Escalamiento: n in {100, 500, 1000, 5000, 10000}, terreno sintético
           con perturbación ±1e-7.
  Nivel 3  Métricas: tiempo de CPU, flips y llamadas a legalize_edge por punto,
           profundidad de búsqueda (saltos DAG vs. comparaciones lineales).

Uso:  python benchmark.py [--rapido]   (--rapido: hasta n=1000, 1 repetición)
Salida: resultados_benchmark.csv y benchmark_resultados.png
"""
import argparse
import csv
import math
import time

import matplotlib
matplotlib.use("Agg")          # solo guarda PNG; el modelo 3D va por py3Dmol
import matplotlib.pyplot as plt

from delaunay import IncrementalDelaunay, delaunay_brute_force
from terrain import generate_synthetic_terrain

NIVEL1 = (10, 25, 50)
NIVEL2 = (100, 500, 1000, 5000, 10000)
MAX_N_LINEAL = 5000            # la búsqueda lineal es O(n^2): se corre 1 sola vez para n > 1000


def conjunto(tris):
    return {frozenset(t.vertices) for t in tris}


def nivel1(semillas=5):
    print("\n=== NIVEL 1: validación de exactitud (fuerza bruta vs RIC) ===")
    todo_ok = True
    for n in NIVEL1:
        ok_dag = ok_lin = 0
        for s in range(semillas):
            pts = generate_synthetic_terrain(n, 20, 20, seed=1000 * n + s)
            ref = conjunto(delaunay_brute_force(pts))
            ok_dag += conjunto(IncrementalDelaunay(pts, True).build(seed=s)) == ref
            ok_lin += conjunto(IncrementalDelaunay(pts, False).build(seed=s)) == ref
        estado = "OK" if ok_dag == ok_lin == semillas else "FALLA"
        todo_ok &= estado == "OK"
        print(f"  n={n:>3}: DAG {ok_dag}/{semillas} idénticos · lineal {ok_lin}/{semillas} idénticos → {estado}")
    return todo_ok


def correr(pts, use_dag, seed):
    solver = IncrementalDelaunay(pts, use_dag=use_dag)
    t0 = time.process_time()
    solver.build(shuffle=True, seed=seed)
    return time.process_time() - t0, solver.stats()


def nivel2_3(reps, ns):
    print("\n=== NIVEL 2/3: escalamiento y métricas ===")
    filas = []
    print(f"{'n':>6} {'t DAG (s)':>10} {'t/(n·log n)':>12} {'flips/pt':>9} {'legaliz/pt':>11} "
          f"{'saltos DAG':>11} | {'t lineal (s)':>12} {'comparac. lin.':>14}")
    for n in ns:
        td, fl, lg, pr = [], [], [], []
        tl, pl = [], []
        for r in range(reps):
            pts = generate_synthetic_terrain(n, 100, 100, eps=1e-7, seed=n * 31 + r)
            t, st = correr(pts, True, r)
            td.append(t); fl.append(st["flips_por_punto"])
            lg.append(st["legalize_por_punto"]); pr.append(st["profundidad_busqueda"])
            if n <= MAX_N_LINEAL and (n <= 1000 or r == 0):
                t2, st2 = correr(pts, False, r)
                tl.append(t2); pl.append(st2["profundidad_busqueda"])
        m = lambda v: sum(v) / len(v) if v else float("nan")
        fila = {"n": n, "t_dag": m(td), "flips_pp": m(fl), "legalize_pp": m(lg), "saltos_dag": m(pr),
                "t_lineal": m(tl), "comparaciones_lineal": m(pl)}
        fila["t_sobre_nlogn"] = fila["t_dag"] / (n * math.log(n))
        filas.append(fila)
        print(f"{n:>6} {fila['t_dag']:>10.3f} {fila['t_sobre_nlogn']:>12.2e} {fila['flips_pp']:>9.2f} "
              f"{fila['legalize_pp']:>11.2f} {fila['saltos_dag']:>11.1f} | "
              f"{fila['t_lineal']:>12.3f} {fila['comparaciones_lineal']:>14.1f}")
    return filas


def ajuste(filas):
    """Regresión por mínimos cuadrados t = a·(n log n) + b y R² (también vs n^2 para comparar)."""
    def r2(xs, ys):
        n = len(xs); mx, my = sum(xs) / n, sum(ys) / n
        sxx = sum((x - mx) ** 2 for x in xs); sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        a = sxy / sxx; b = my - a * mx
        ss_res = sum((y - (a * x + b)) ** 2 for x, y in zip(xs, ys)); ss_tot = sum((y - my) ** 2 for y in ys)
        return a, b, 1 - ss_res / ss_tot
    ns = [f["n"] for f in filas]; ts = [f["t_dag"] for f in filas]
    a, b, R_nlogn = r2([n * math.log(n) for n in ns], ts)
    _, _, R_n2 = r2([n * n for n in ns], ts)
    print(f"\nAjuste del tiempo DAG:  R²(n log n) = {R_nlogn:.4f}   vs   R²(n²) = {R_n2:.4f}")
    # pendiente log-log: t ~ n^k  (k≈1.1 para n log n, k≈2 para n²)
    k = (math.log(ts[-1]) - math.log(ts[0])) / (math.log(ns[-1]) - math.log(ns[0]))
    print(f"Exponente empírico (log-log) t ~ n^{k:.2f}   (n log n ≈ 1.1–1.2, n² = 2)")
    return a, b, R_nlogn, R_n2, k


def graficar(filas, a, b, k):
    ns = [f["n"] for f in filas]
    fig, ax = plt.subplots(1, 3, figsize=(16, 4.6))

    ax[0].loglog(ns, [f["t_dag"] for f in filas], "o-", label="RIC + DAG (medido)")
    ln = [(f["n"], f["t_lineal"]) for f in filas if f["t_lineal"] == f["t_lineal"]]
    ax[0].loglog([x for x, _ in ln], [y for _, y in ln], "s--", label="RIC + búsqueda lineal")
    xs = [n * math.log(n) for n in ns]
    c = sum(f["t_dag"] * x for f, x in zip(filas, xs)) / sum(x * x for x in xs)   # ajuste por el origen
    ax[0].loglog(ns, [c * x for x in xs], ":", color="gray", label="ajuste c·n·log n")
    ax[0].set(title=f"Tiempo de CPU (exponente empírico ≈ {k:.2f})", xlabel="n", ylabel="segundos")
    ax[0].legend(); ax[0].grid(True, which="both", alpha=.3)

    ax[1].semilogx(ns, [f["flips_pp"] for f in filas], "o-", label="edge flips / punto")
    ax[1].semilogx(ns, [f["legalize_pp"] for f in filas], "s-", label="llamadas legalize_edge / punto")
    ax[1].set(title="Reestructuración local por inserción", xlabel="n", ylabel="promedio", ylim=(0, 12))
    ax[1].legend(); ax[1].grid(True, alpha=.3)

    ax[2].loglog(ns, [f["saltos_dag"] for f in filas], "o-", label="saltos en el DAG")
    ln = [(f["n"], f["comparaciones_lineal"]) for f in filas if f["comparaciones_lineal"] == f["comparaciones_lineal"]]
    ax[2].loglog([x for x, _ in ln], [y for _, y in ln], "s--", label="comparaciones búsqueda lineal")
    ax[2].set(title="Profundidad de búsqueda por punto", xlabel="n", ylabel="pasos promedio")
    ax[2].legend(); ax[2].grid(True, which="both", alpha=.3)

    fig.tight_layout()
    fig.savefig("benchmark_resultados.png", dpi=140)
    print("Gráfica guardada: benchmark_resultados.png")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rapido", action="store_true")
    a = ap.parse_args()
    ns = NIVEL2[:3] if a.rapido else NIVEL2
    reps = 1 if a.rapido else 3

    ok = nivel1()
    filas = nivel2_3(reps, ns)
    coef, b, R, R2, k = ajuste(filas)

    with open("resultados_benchmark.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader(); w.writerows(filas)
    print("Datos guardados: resultados_benchmark.csv")
    graficar(filas, coef, b, k)
    print("\nNivel 1:", "APROBADO" if ok else "FALLÓ")


if __name__ == "__main__":
    main()
