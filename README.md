# Triangulación de Delaunay para Interpolación de Alturas

Proyecto final de **Estructura de Datos y Algoritmos** en Python. Implementa la construcción de la Triangulación de Delaunay en 2D y su aplicación para la interpolación de terrenos 3D, contrastando una línea base por **Fuerza Bruta** $\mathcal{O}(n^4)$ frente a la solución óptima **RIC (Construcción Incremental Aleatorizada) + DAG** en tiempo esperado $\mathcal{O}(n \log n)$.

## Requisitos del Sistema

* **Python:** Versión `3.10` o superior.
* **Dependencias:** El núcleo algorítmico (`models.py`, `delaunay.py`, `terrain.py`) y las pruebas unitarias usan únicamente la biblioteca estándar de Python (`decimal`, `itertools`, `math`, `random`, `unittest`). Para las gráficas del benchmark y el modelo 3D interactivo se requieren `matplotlib` y `py3Dmol`:

```bash
pip install matplotlib py3Dmol
```

## Cómo ejecutar el proyecto

Todos los scripts de Python se encuentran dentro de la carpeta `codigo/`. Antes de ejecutar cualquier comando, entra a ese directorio desde la raíz del repositorio:

```bash
cd codigo
```

### 1. Pruebas unitarias y validación contra Fuerza Bruta
Ejecuta las 12 pruebas unitarias de `test_delaunay.py`, que validan la aritmética exacta (`in_circle`), la equivalencia topológica entre Fuerza Bruta y RIC (DAG y lineal), la propiedad del círculo vacío, la fórmula de Euler, la remoción del súper-triángulo y la consistencia de adyacencias:

```bash
python -m unittest test_delaunay.py -v
```

### 2. Fuerza Bruta y Benchmark empírico (3 niveles)
Ejecuta la validación cruzada contra Fuerza Bruta ($n \in \{10, 25, 50\}$) y las pruebas de escalamiento hasta $n = 10{,}000$, generando `resultados_benchmark.csv` y `benchmark_resultados.png`:

```bash
# Versión rápida (hasta n=1000, ideal para pruebas breves)
python benchmark.py --rapido

# Benchmark completo (hasta n=10000, 3 repeticiones)
python benchmark.py
```

### 3. Visualización 3D interactiva paso a paso
Genera el archivo `terreno_delaunay.html` con `py3Dmol` y lo abre en el navegador para reproducir cada inserción y *edge flip* en 3D:

```bash
python main_visual.py
```

> **Nota:** Por defecto la visualización se genera con **60 puntos** (198 pasos de animación). Si deseas cambiar o aumentar la cantidad de puntos, usa el parámetro `--n`, por ejemplo:
> ```bash
> python main_visual.py --n 150
> ```
> *(En entornos sin navegador gráfico como GitHub Codespaces, agrega `--no-open` para solo generar el archivo HTML).*

## Estructura del Repositorio

* `codigo/models.py`: Clases `Point` y `Triangle` (con punteros `neighbors` y nodos `children` del DAG), además de `orient2d` e `in_circle` con `Decimal` a 100 dígitos de precisión.
* `codigo/delaunay.py`: Algoritmo base `delaunay_brute_force` $\mathcal{O}(n^4)$ y clase óptima `IncrementalDelaunay` (RIC + DAG + `legalize_edge`).
* `codigo/terrain.py`: Generador de terrenos sintéticos con perturbación $\pm 10^{-7}$ para posición general.
* `codigo/test_delaunay.py`: Suite de 12 pruebas unitarias.
* `codigo/benchmark.py`: Protocolo experimental de 3 niveles, regresión $R^2$ y generación de métricas/gráficas.
* `codigo/main_visual.py`: Visualizador 3D paso a paso con `py3Dmol`.
* `docs/`: Documentación y reportes del proyecto.
