import random
import math
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from models import Point
from delaunay import IncrementalDelaunay


def generate_synthetic_terrain(n: int, width: float, height: float) -> list[Point]:
    """Genera 'n' puntos con elevación Z simulando colinas y valles."""
    points = []
    for i in range(n):
        x = random.uniform(0, width)
        y = random.uniform(0, height)
        # Función de relieve para el terreno
        z = math.sin(x * 0.5) * math.cos(y * 0.5) * 5.0
        points.append(Point(x, y, z, id_pt=i))
    return points


def plot_3d_terrain(triangles):
    """Renderiza el terreno 3D final."""
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    ax.set_title("Modelo de Terreno 3D (Interpolación de Alturas final)")

    verts = []
    for tri in triangles:
        coords = [(float(v.x), float(v.y), float(v.z)) for v in tri.vertices]
        verts.append(coords)

    mesh = Poly3DCollection(verts, edgecolors='black', linewidths=0.5, alpha=0.8)
    z_centers = [sum(v[2] for v in t) / 3.0 for t in verts]
    mesh.set_array(z_centers)
    mesh.set_cmap('viridis')

    ax.add_collection3d(mesh)
    fig.colorbar(mesh, ax=ax, label="Elevación", shrink=0.5)

    all_x = [float(v.x) for tri in triangles for v in tri.vertices]
    all_y = [float(v.y) for tri in triangles for v in tri.vertices]
    all_z = [float(v.z) for tri in triangles for v in tri.vertices]

    if all_x and all_y and all_z:
        ax.set_xlim(min(all_x), max(all_x))
        ax.set_ylim(min(all_y), max(all_y))
        ax.set_zlim(min(all_z) - 1, max(all_z) + 1)

    plt.show()


if __name__ == "__main__":
    # 1. Parámetros
    NUM_PUNTOS = 60  # Reducido un poco para que la animación no tarde demasiado
    ANCHO_TERRENO = 20.0
    ALTO_TERRENO = 20.0

    print(f"Generando {NUM_PUNTOS} puntos...")
    puntos_terreno = generate_synthetic_terrain(NUM_PUNTOS, ANCHO_TERRENO, ALTO_TERRENO)

    delaunay_solver = IncrementalDelaunay(puntos_terreno)

    # 2. Configurar la Animación 2D interactiva
    plt.ion()  # Encender modo interactivo
    fig, ax = plt.subplots(figsize=(8, 8))
    fig.canvas.manager.set_window_title('Construcción Paso a Paso - Delaunay')

    puntos_insertados = []

    # 3. Bucle de Inserción y Animación
    for i, p in enumerate(puntos_terreno):
        # Lógica de inserción del algoritmo
        delaunay_solver.insert_point(p)
        puntos_insertados.append(p)

        # Limpiar el lienzo para el siguiente fotograma
        ax.clear()
        ax.set_title(f"Insertando punto {i + 1}/{NUM_PUNTOS}")

        # Obtener los triángulos (sin remover el súper-triángulo para ver las conexiones externas)
        current_triangles = delaunay_solver.get_active_triangles(remove_super=False)

        # Dibujar aristas
        for tri in current_triangles:
            t_points = [(float(v.x), float(v.y)) for v in tri.vertices]
            t_points.append(t_points[0])
            xs, ys = zip(*t_points)
            ax.plot(xs, ys, color='blue', linewidth=0.5, alpha=0.4)

        # Dibujar los puntos
        px = [float(pt.x) for pt in puntos_insertados]
        py = [float(pt.y) for pt in puntos_insertados]

        # Puntos anteriores en negro, el punto recién insertado en rojo y más grande
        if len(px) > 1:
            ax.scatter(px[:-1], py[:-1], color='black', s=15, zorder=5)
        ax.scatter(px[-1], py[-1], color='red', s=50, zorder=6)

        # Fijar los límites de la cámara para que no brinque intentando enfocar el súper-triángulo
        ax.set_xlim(-2, ANCHO_TERRENO + 2)
        ax.set_ylim(-2, ALTO_TERRENO + 2)

        # Pausar 0.1 segundos para crear el efecto de video
        plt.pause(0.1)

    plt.ioff()  # Apagar modo interactivo al terminar el bucle

    # 4. Mostrar el resultado final limpio (sin súper-triángulo)
    triangulos_finales = delaunay_solver.get_active_triangles(remove_super=True)
    ax.clear()
    ax.set_title("Triangulación 2D Final")
    for tri in triangulos_finales:
        t_points = [(float(v.x), float(v.y)) for v in tri.vertices]
        t_points.append(t_points[0])
        xs, ys = zip(*t_points)
        ax.plot(xs, ys, color='blue', linewidth=1, alpha=0.8)

    ax.scatter(px, py, color='black', s=20, zorder=5)
    ax.set_xlim(-2, ANCHO_TERRENO + 2)
    ax.set_ylim(-2, ALTO_TERRENO + 2)
    plt.show()  # La ventana 2D se queda abierta esperando que la cierres

    # 5. Lanzar el render 3D
    print("Abriendo modelo 3D...")
    plot_3d_terrain(triangulos_finales)