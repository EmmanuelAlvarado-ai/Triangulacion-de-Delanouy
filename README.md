# Triangulación de Delaunay para Interpolación de Alturas 

Este repositorio contiene el código fuente para el Hito Intermedio del proyecto final de la materia **Estructura de Datos y Algoritmos**. Implementa la construcción de la Triangulación de Delaunay en 2D y su aplicación para la interpolación de terrenos 3D.

## Requisitos del Sistema (Reproducibilidad)

Para ejecutar este proyecto y sus pruebas, asegúrate de contar con el siguiente entorno:

* **Python:** Versión `3.10` o superior (Recomendado: `3.12`).
* **Dependencias:** El módulo base solo utiliza librerías estándar (`decimal`, `itertools`, `math`). Para la visualización interactiva, se requiere instalar `matplotlib`.

Puedes instalar la dependencia gráfica ejecutando el siguiente comando en tu terminal (o en la consola de PyCharm):
```bash
pip install matplotlib
```

## Cómo ejecutar el proyecto

El proyecto está dividido en submódulos lógicos. A continuación se detallan los pasos exactos para evaluar cada componente:

### 1. Pruebas Unitarias y Fuerza Bruta (Validación del 15%)
El archivo `test_delaunay.py` contiene la suite de pruebas que valida matemáticamente la implementación. Esto incluye la validación de la **Fuerza Bruta O(n^4)** comparando sus resultados directamente contra el algoritmo Incremental.

Para correr las pruebas, ejecuta en la terminal de la raíz del proyecto:
```bash
python -m unittest test_delaunay.py -v
```
*Si la prueba es exitosa, la consola mostrará un mensaje indicando `OK`, validando que ambas triangulaciones generan un conjunto de aristas topológicamente idéntico.*

### 2. Visualización Paso a Paso y Renderizado 3D
Para observar la construcción geométrica del algoritmo en tiempo real (inserción incremental y *edge flips*) y el modelo de interpolación de alturas (Z) final:

1. Ejecuta el archivo principal interactivo:
   
```bash
   python main_visual.py
```
2. Se abrirá una primera ventana interactiva 2D. Podrás ver cómo se va construyendo la malla de triángulos conforme se insertan los puntos de prueba.
3. Una vez finalizada la construcción 2D, cierra esa ventana y automáticamente se abrirá el **visualizador 3D interactivo**, donde podrás usar el ratón para rotar el terreno generado a partir de las alturas interpoladas.

## Arquitectura del Repositorio

* `models.py`: Clases base (`Point`, `Triangle`) y cálculos de determinantes matemáticos exactos (Predicado *In-Circle*).
* `delaunay.py`: Lógica principal. Contiene tanto la Línea Base (`delaunay_brute_force`) como el Algoritmo Óptimo (`IncrementalDelaunay` con subrutina `legalize_edge`).
* `test_delaunay.py`: Casos de prueba mínimos para validación.
* `main_visual.py`: Script para generar instancias sintéticas y renderizar resultados.
