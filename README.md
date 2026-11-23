# Triangulación de Delaunay para Interpolación de Alturas

Proyecto final de la materia **Estructura de Datos y Algoritmos** (Universidad Anáhuac Querétaro).  
**Autor:** Noé Emmanuel Alvarado Ríos

Implementación modular en Python de la **Triangulación de Delaunay 2D** aplicada a la interpolación de terrenos 3D, comparando una línea base exhaustiva por **Fuerza Bruta** $\mathcal{O}(n^4)$ frente al algoritmo óptimo de **Construcción Incremental Aleatorizada (RIC)** con **Grafo Acíclico Dirigido (DAG)** de localización en $\mathcal{O}(n \log n)$ esperado, aritmética exacta de 100 dígitos (`decimal`) y visualización 3D interactiva paso a paso en el navegador (`py3Dmol`).

---

## Requisitos del Sistema

* **Python:** `3.10` o superior (probado en Python `3.12`).
* **Librerías estándar utilizadas:** `decimal`, `itertools`, `math`, `random`, `unittest`, `csv`, `time`, `argparse`, `json`, `os`, `webbrowser`.
* **Dependencias externas:**
  * `matplotlib` (para generar la gráfica comparativa del benchmark `benchmark_resultados.png`).
  * `py3Dmol` (para generar el modelo 3D interactivo paso a paso `terreno_delaunay.html`).

Instala las dependencias desde la terminal (o consola de PyCharm / VS Code):

```bash
pip install matplotlib py3Dmol
```

---

## Estructura del Repositorio

* `models.py`: Clases base `Point` y `Triangle` (con referencias a 3 vecinos para *edge flips* en $\mathcal{O}(1)$ y lista `children` para el DAG), junto con los predicados exactos `orient2d` e `in_circle` configurados a 100 dígitos de precisión (`getcontext().prec = 100`).
* `delaunay.py`:
  * `delaunay_brute_force`: Algoritmo de fuerza bruta $\mathcal{O}(n^4)$ (100% funcional) usado como referencia exacta.
  * `IncrementalDelaunay`: Algoritmo óptimo RIC con súper-triángulo (`SUPER_FACTOR = 1000.0`), localización en DAG (`_locate_dag`), subrutina recursiva `legalize_edge`, remoción del súper-triángulo, registro de eventos (`on_event`) y recolección de métricas (`stats`).
* `terrain.py`: Generador de terrenos sintéticos `generate_synthetic_terrain` con superficie continua $Z(x,y) = 5\sin(0.5x)\cos(0.5y)$ y perturbación microscópica $\pm 10^{-7}$ para asegurar posición general.
* `test_delaunay.py`: Suite de **12 pruebas unitarias** (`unittest`) que valida fuerza bruta vs. RIC (DAG y lineal), casos borde de `in_circle`, propiedad del círculo vacío, fórmula de Euler, consistencia bidireccional de adyacencias, remoción del súper-triángulo, duplicados y eficiencia del DAG.
* `benchmark.py`: Ejecuta el protocolo experimental de 3 niveles (Nivel 1: exactitud $n \in \{10, 25, 50\}$; Nivel 2/3: escalamiento $n \in \{10^2, 5 \times 10^2, 10^3, 5 \times 10^3, 10^4\}$, regresión $R^2$ y métricas por punto). Genera `resultados_benchmark.csv` y `benchmark_resultados.png`.
* `main_visual.py`: Graba cada división $1 \to 3$ y cada *edge flip* del algoritmo RIC + DAG, genera `terreno_delaunay.html` usando `py3Dmol` y lo abre automáticamente en el navegador con controles de reproducción paso a paso.

---

## Pasos Exactos de Ejecución y Reproducibilidad

### 1. Ejecutar las Pruebas Unitarias y Validación de Fuerza Bruta
Ejecuta la suite completa de 12 pruebas (incluyendo el contraste exacto entre `delaunay_brute_force` y `IncrementalDelaunay` en $n \in \{10, 25, 50\}$):

```bash
python -m unittest test_delaunay.py -v
```

Resultado esperado: las 12 pruebas finalizan con estado `OK` sin errores de ejecución.

### 2. Ejecutar el Benchmark Empírico (Fuerza Bruta vs. RIC + DAG vs. Lineal)
Para una corrida rápida de verificación (Nivel 1 completo + escalamiento hasta $n = 1{,}000$, 1 repetición):

```bash
python benchmark.py --rapido
```

Para reproducir el benchmark completo reportado en el PDF (hasta $n = 10{,}000$, 3 repeticiones por tamaño):

```bash
python benchmark.py
```

Salidas generadas:
* `resultados_benchmark.csv`: Tabla con tiempos de CPU, *edge flips*/punto, llamadas a `legalize_edge`/punto y profundidad de búsqueda.
* `benchmark_resultados.png`: Gráfica comparativa de 3 paneles (tiempo log-log con exponente empírico $\approx 1.13$, estabilidad de flips y saltos del DAG vs. búsqueda lineal).

### 3. Ejecutar la Visualización 3D Interactiva Paso a Paso (`py3Dmol`)
Genera y abre en tu navegador la animación interactiva de la construcción incremental:

```bash
python main_visual.py
```

> **Nota sobre la cantidad de puntos:** Por defecto, el visualizador genera **60 puntos** (lo que produce 198 cuadros de animación entre inserciones, *edge flips* y el modelo final). Si deseas cambiar la cantidad o agregar más puntos, utiliza el parámetro `--n` desde la terminal, por ejemplo:
>
> ```bash
> python main_visual.py --n 150
> ```

También puedes combinarlo con otras opciones personalizadas (`--seed` para variar el relieve y `--salida` para elegir el nombre del archivo HTML):

```bash
python main_visual.py --n 150 --seed 7 --salida terreno_delaunay.html
```

En la ventana del navegador puedes usar los botones de reproducción (`⏮`, `◀`, `⏸/▶`, `▶`, `⏭`), el deslizador de paso, el control de velocidad y el factor de altura `Z` (`Z = 0` muestra la malla 2D clásica), además de rotar y hacer zoom con el ratón.

---

## Resumen de Resultados del Benchmark

* **Exactitud Nivel 1 ($n \in \{10, 25, 50\}$):** 100% de coincidencia topológica entre Fuerza Bruta, RIC + DAG y RIC lineal.
* **Ajuste Asintótico:** $R^2(n \log n) = 0.9995$ frente a $R^2(n^2) = 0.9660$, con exponente empírico $t \sim n^{1.13}$.
* **Desempeño en $n = 5{,}000$:** `0.849 s` con DAG vs. `32.031 s` con búsqueda lineal ($37.7\times$ más rápido), reduciendo la búsqueda de `16,650.4` comparaciones a `25.3` saltos promedio ($658\times$ menos pasos).
* **Reestructuración Local:** Promedio constante de **2.64 a 2.99 *edge flips* por punto** (y **8.27 a 8.98** llamadas a `legalize_edge` por punto) hasta $n = 10{,}000$.
