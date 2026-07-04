# Cat Delivery Game

Este es un juego interactivo en 2D desarrollado en Python desde cero. El jugador controla a un gato repartidor que debe recoger y entregar pedidos en un mapa cuadriculado, adaptándose a las reglas de diferentes modos de juego.

El proyecto me sirvió para poner en práctica conceptos clave de estructuras de datos y optimización en la carrera de Ingeniería de Sistemas.

## Características y Lógica Aplicada

* **Estructuras de datos:** Utilicé `heapq` para gestionar las prioridades y tiempos límite de las entregas, y `deque` para el manejo eficiente de los estados del juego.
* **Organización del código:** Implementé Programación Orientada a Objetos (POO) y el uso de `@dataclass` para estructurar de forma limpia la información de los pedidos y las pantallas.
* **Modos de juego:**
  * **Modo Clásico:** El reto de entregas tradicional.
  * **Modo Tiempos Límite (Deadlines):** Enfocado en la velocidad y entregas contra el reloj.
  * **Modo Energía:** Cada movimiento consume energía, obligando a planificar la ruta y usar puntos de recarga.
  * **Modo Barrios (3x3):** Logística de navegación restringida por zonas.

## Cómo ejecutarlo

Para probar el juego, asegúrate de tener Python instalado y ejecuta el archivo principal desde tu terminal:

```bash
python CatDelivery.py
