import pygame #libreria que ayuda al funcionamiento del juego (grafico y eventos)
import sys #modulo para interactuar con el sistema
import math #modulo matematico estandan (se utiliza para distancias, etc)
import random #generador de numeros aleatorios
import heapq #implementa colas de prioridad (util para algoritmos de busqueda)
from collections import deque #cola doble
from dataclasses import dataclass #nos permite definir estructuras de datos
from enum import Enum, auto #define valores constantes con significado

#Seccion 1: estructuras de datos del juego

@dataclass(frozen=True) #aqui definimos una clase de datos
class Order:
    order_id: int #identificador de cada orden
    pickup: tuple[int, int] #coordenadas donde se recoge
    dropoff: tuple[int, int] #coordenada donde se entrega
    tip: int #propina asociada a la orden
    deadline: float #tiempo limite para entregar la orden        

class Screen(Enum):
    Splash = auto() #pantalla de presentacion
    Menu = auto() ##pantalla del menu
    Rules = auto() #pantalla de reglas
    Game = auto() #pantalla donde corre el juego


@dataclass #no es frozen porque se pueden ajustar los valores dinamicamente
class ModeConfig:
    key: str #identificador
    title: str #titulo a mostrar
    description: str #texto explicativo
    carry_max: int #maximo de ordenes que el gato puede agarrar
    time_max: float #tiempo maximo del modo
    time_gain: float #tiempo que se gana al entregar una orden
    num_orders_start: int #numero de ordenes al iniciar el modo
    wall_density_start: float #"cantidad" de paredes por modo


@dataclass
class Button: #representa los botones interactivos
    rect: pygame.Rect #area del boton (posicion, tamano, etc)
    text: str #texto del boton
    payload: object #dato asociado al boton

#Seccion 2: constantes y colores

ORDER_COLORS = [ #lista de colores posibles para los paquetes
    (255, 92, 116), (255, 170, 64), (255, 235, 86), #rosado, naranja y amarillo
    (92, 255, 156), (92, 200, 255), (172, 120, 255), #verde, azulito y violeta
    (255, 120, 220), (80, 255, 235),] #magenta y turquesa

BG_COLOR = (14, 14, 20) #color del fondo
TILE_A = (46, 46, 68) #color tablero 1
TILE_B = (40, 40, 62) #color tablero 2 (para alternar com 1)
GRID_LINE = (210, 210, 245) #color de las lineas que dividen el espacio
HUD_TEXT = (235, 235, 255) #color del texto (principal)
HUD_SUB = (170, 170, 210) #color del texto (secundario)

#Aqui se definen los colores del gato
CAT_FUR = (255, 170, 70) #pelaje naranja
CAT_FUR_2 = (255, 150, 55) #variacion del pelaje
CAT_LINE = (30, 22, 14) #contornos del gato - marron
CAT_EYE = (245, 245, 255) #ojos del gato
CAT_PUPIL = (25, 25, 30) #pupila del gato
CAT_NOSE = (255, 120, 120) #nariz rosita del gato
CAT_WHISK = (30, 22, 14) #color de los bigotes del gato

ENERGY_STATION_COLOR = (140, 255, 180) #color de la estacion de energia (modo energia) - verde
ENERGY_STATION_BORDER = (25, 45, 30) #borde oscuro de energia

WORLD_CHUNKS = 3  #aqui definimos cuantos barrios hay (en nuestro caso es una matriz 3x3)
CHUNK_MIN = -(WORLD_CHUNKS // 2) #limite minimo de coordenadad (-1)
CHUNK_MAX = (WORLD_CHUNKS // 2) #limite maximo de coordenadad (1)

#Seccion 3: como se distribuye la pantalla

@dataclass
class Layout: #en esta clase se guardan numeros calculados que nos ayudan en las funciones de dibujo
    width: int #tamano total de la ventana (ancho)
    height: int #tamano total de la ventana (largo)
    cell: int #tamano en pixeles de las celdas
    grid_w: int #cantidadd de celdas horizontales
    grid_h: int #cantidadd de celdas horizontales
    map_w: int #tamano total del mapa en pixeles (ancho)
    map_h: int #tamano total del mapa en pixeles (largo)
    map_x: int #posicion del mapa en ventana
    map_y: int #posicion del mapa en ventana
    side_x: int #posicion panel lateral
    side_y: int #posicion panel lateral
    side_w: int #tamano del panel lateral
    side_h: int #tamano del panel lateral
    hud_y: int #posicion vertical donde empiexa el HUD (informacion visual en pantalla) inferior

def compute_layout(width: int, height: int, grid_w: int, grid_h: int) -> Layout: #aqui se calcula el layout completo
    margin = 20 #margen que evita que todo este pegado al borde
    hud_h = 170 #altura reservada para HUD inferior
    side_min_w = 300 #ancho del panel lateral
    avail_h = max(320, height - hud_h - 2 * margin) #altura disponible para el mapa
    avail_w_for_map = max(520, width - side_min_w - 3 * margin) #ancho disponible para el mapa
    cell_by_h = avail_h // grid_h #tamano de celda segun disponibilidad de altura
    cell_by_w = avail_w_for_map // grid_w #tamano de segun ancho disponible
    cell = int(max(24, min(46, cell_by_h, cell_by_w))) #permite que el mapa siempre sea leible
    map_w = grid_w * cell #conversion a pixeles
    map_h = grid_h * cell #conversion a pixeles

    side_w = max(side_min_w, width - (map_w + 3 * margin)) #aqui se calcula el ancho que resta tras colocar el mapa
    if side_w < 240:
        side_w = 240 #si es muy estrecho se pone el limite de seguridad
    total_w = map_w + side_w + 2 * margin #se calcula el ancho total usado por el layout
    if total_w > width:
        side_w = max(240, width - map_w - 2 * margin) #se corrige si se sale de ventana

    map_x = margin #esto es para que empiecen despues del margen
    map_y = margin
    side_x = map_x + map_w + margin #aqui alineamos el pael a la derecha del mapa
    side_y = map_y
    side_h = map_h #definimos que el panel lateral tiene la misma altura que el pana
    hud_y = map_y + map_h + 10 #el HUD empieza debajo del mapa separado por 10 pixeles

    return Layout( #se construye el objeto con lo calculado (queda centralizado)
        width=width, height=height, cell=cell, grid_w=grid_w, grid_h=grid_h,
        map_w=map_w, map_h=map_h, map_x=map_x, map_y=map_y, side_x=side_x, 
        side_y=side_y, side_w=side_w, side_h=side_h, hud_y=hud_y)

#Seccion 4: funciones auxiliares generales

def clamp(v, a, b): #funcion que limita un valor (v=valor a limitar,a=minimo permitido,b=maximo permitido)
    return max(a, min(b, v))

def neighbors4(c, r): #nos devuelve los vecinos de las celda, no incluye diagonales, movimiento del grid
    return [(c + 1, r), (c - 1, r), (c, r + 1), (c, r - 1)]

def in_bounds_local(c, r, grid_w, grid_h): #verifica si una celda esta dentro del mapa
    return 0 <= c < grid_w and 0 <= r < grid_h

def in_bounds_world(c, r, world_w, world_h): #verifica si una celda esta en el mundo (modo barrios)
    return 0 <= c < world_w and 0 <= r < world_h

def wrap_text(text, font, max_width): #divide el texto en lineas que quepan en un ancho
    words = text.split() #divide el texto en palabras
    lines = [] #lista de lineas
    cur = "" #linea que se esta construyendo
    for w in words: #itera por palabras
        test = (cur + " " + w).strip() #intenta anadir la palabra a la linea actua;
        if font.size(test)[0] <= max_width: #si cabe
            cur = test #acepta la palabra en la linea
        else: #si no cabe
            if cur: #guarda linea actua;
                lines.append(cur)
            cur = w #comienza una nueva linea
    if cur: #agrega ultima linea pentiende
        lines.append(cur)
    return lines #devuelve una lista de las lineas

#Seccion 5: sistema de coordenadas en modo barrios

def chunk_to_world_index(chunk_x: int, chunk_y: int) -> tuple[int, int]: #convierte coordenadas centradas en 0 a los indices de una matriz
    return chunk_x - CHUNK_MIN, chunk_y - CHUNK_MIN #nos devuelve los indices validos para la lista o matriz

def local_to_world(chunk_x: int, chunk_y: int, col: int, row: int, grid_w: int, grid_h: int) -> tuple[int, int]: #convierte una posicion local de un barrio a una global del mundo
    ix, iy = chunk_to_world_index(chunk_x, chunk_y) #convierte en indices positivos
    return ix * grid_w + col, iy * grid_h + row #obtenemos una coordenada unica y global para el mundo

def world_to_chunk_local(world_col: int, world_row: int, grid_w: int, grid_h: int) -> tuple[int, int, int, int]: #convierte coordenadas globales a barrio o posicion
    ix = world_col // grid_w #determina en que bloque horizontal estoy
    iy = world_row // grid_h #determina en que bloque vertical estoy
    col = world_col % grid_w #posicion horizontal dentro del barrio
    row = world_row % grid_h #posicion vertical dentro del barrio
    chunk_x = ix + CHUNK_MIN #devuelve un sistema centrado
    chunk_y = iy + CHUNK_MIN
    return chunk_x, chunk_y, col, row

def barrio_name(chunk_x: int, chunk_y: int) -> str: #devuelve un nombre para cada barrio
    if chunk_x == 0 and chunk_y == 0:
        return "Centro"
    parts = []
    if chunk_y < 0:
        parts.append("Norte")
    elif chunk_y > 0:
        parts.append("Sur")
    if chunk_x < 0:
        parts.append("Oeste")
    elif chunk_x > 0:
        parts.append("Este")
    return " ".join(parts) if parts else "Centro" #aqui se devuelven los nombres y sus combinaciones

#Seccion 6: calcula las celdas alcanzables en el mundo completo

def bfs_reachable_world(start: tuple[int, int], walls_world: set[tuple[int, int]], world_w: int, world_h: int): #calcula las posiciones alcanzables 
    q = deque([start]) #crea una cola
    seen = {start} #celdas ya visitadas
    while q: #sigue
        c, r = q.popleft() #saca la mas antigua de la cola
        for nc, nr in neighbors4(c, r): #se dan los 4 vecinos
            if in_bounds_world(nc, nr, world_w, world_h) and (nc, nr) not in walls_world and (nc, nr) not in seen: #valida que este en el mundo, que no sea una pared y que no se haya visitado antes
                seen.add((nc, nr)) #marca la celda como visitada
                q.append((nc, nr)) #la agrega a la cola
    return seen ##devuelve el conjunto de todas las celdas alcanzables

#Seccion 7: costos y rutas optimas

def generate_traffic_generic(walls: set[tuple[int, int]], level: int, world_w: int, world_h: int, seed=None): #genera un mapa de trafico
    if seed is not None: #si hay semilla se genera el trafico
        random.seed(seed)
    traffic = {} #diccionario que almacena la clave y el costo de moverse por esa celda
    for r in range(world_h): #recorre todo el mundo
        for c in range(world_w):
            if (c, r) in walls: #si son paredes no son transitables
                continue
            traffic[(c, r)] = 1.0 #costo base

    hotspots = min(2 + level // 2, 10) #cantidad de zonas congestionadas (aumentan con nivel y se define un limite)
    candidates = list(traffic.keys()) #transitables candidatas a hotspot
    random.shuffle(candidates) #mezcla aleatoriamente
    for i in range(min(hotspots, len(candidates))): #selecciona los primeros hotspots tras mezclar
        cc, rr = candidates[i]
        for dc in (-1, 0, 1):
            for dr in (-1, 0, 1):
                nc, nr = cc + dc, rr + dr
                if (nc, nr) in traffic: #verifica que no sea pared
                    dist = abs(dc) + abs(dr) #distancia manhattan
                    mult = 1.9 if dist == 0 else (1.5 if dist == 1 else 1.25) #multiblicador del costo
                    traffic[(nc, nr)] = max(traffic[(nc, nr)], mult)
    return traffic #devuelve el mapa de costos

def dijkstra_cost_generic(start: tuple[int, int], goal: tuple[int, int], walls: set[tuple[int, int]], traffic: dict,
                         world_w: int, world_h: int): #calcula el costo minimo entre 2 puntos
    if start == goal:
        return 0.0
    if goal in walls: #si el destino es una pared, es imposible
        return float("inf")

    pq = [(0.0, start)] #cola de prioridad que inicia en el punto de inicio
    dist = {start: 0.0} #diccionario de las distancias minimas conocidas
    while pq: #sigue mientras haya nodos que explorar
        cost, cur = heapq.heappop(pq) #extrae el nodo con menor costo
        if cur == goal: #si llegamos al destino es el costo minimo
            return cost
        if cost != dist.get(cur, float("inf")): #descarta entradas no obsoletas de la cola
            continue

        c, r = cur
        for nc, nr in neighbors4(c, r): #explora los vecinos
            if not in_bounds_world(nc, nr, world_w, world_h): #evita que salga del mundo
                continue
            if (nc, nr) in walls: #no atraviesa paredes
                continue
            step = traffic.get((nc, nr), 1.0) #costo de moverse a la celda vecina
            ncost = cost + step #nuevo costo acumulado
            if ncost < dist.get((nc, nr), float("inf")):
                dist[(nc, nr)] = ncost #si encontramos un camino mejor actualiza la mejor distancia conocida
                heapq.heappush(pq, (ncost, (nc, nr))) #agrega a la cola de prioridad
    return float("inf") #si se agota la cola, el destino no es alcanzable

#Seccion 8: genera un nivel

def generate_level_local(grid_w: int, grid_h: int, seed=None, num_orders=3, wall_density=0.18): #genera un nivel dentro de un solo mapa
    if seed is not None:
        random.seed(seed)

    start_local = (2, 2)
    walls_local = set()

    all_cells = [(c, r) for r in range(grid_h) for c in range(grid_w)]
    free_cells = [cell for cell in all_cells if cell != start_local]
    random.shuffle(free_cells)

    orders_local = []
    used = {start_local}

    def take_free_cell(): #esta funcion encapsula la seleccion de celdas validas
        while free_cells:
            cell = free_cells.pop()
            if cell not in used:
                used.add(cell)
                return cell
        raise RuntimeError("No hay suficientes celdas libres para generar ordenes.")

    for oid in range(num_orders):
        p = take_free_cell()
        d = take_free_cell()
        tip = random.randint(10, 60)
        deadline = random.uniform(6.0, 12.0)
        orders_local.append((oid, p, d, tip, deadline))

    blocked = {start_local}
    for (_, p, d, _, _) in orders_local:
        blocked.add(p)
        blocked.add(d)

    target_walls = int(grid_w * grid_h * wall_density)
    candidates = [cell for cell in all_cells if cell not in blocked]
    random.shuffle(candidates)

    def still_playable(walls_set): #verifica si el mapa sigue siendo jugable
        q = deque([start_local])
        seen = {start_local}
        while q:
            c, r = q.popleft()
            for nc, nr in neighbors4(c, r):
                if in_bounds_local(nc, nr, grid_w, grid_h) and (nc, nr) not in walls_set and (nc, nr) not in seen:
                    seen.add((nc, nr))
                    q.append((nc, nr))
        for (_, p, d, _, _) in orders_local:
            if p not in seen or d not in seen:
                return False
        return True

    placed = 0
    for cell in candidates:
        if placed >= target_walls:
            break
        walls_local.add(cell)
        if still_playable(walls_local):
            placed += 1
        else:
            walls_local.remove(cell)

    sx = clamp(start_local[0], 0, grid_w - 1)
    sy = clamp(start_local[1], 0, grid_h - 1)
    start_local = (sx, sy)

    return start_local, walls_local, orders_local

#Seccion 9: generacion del mundo en modo barrios

def generate_world(grid_w: int, grid_h: int, seed=None, num_orders=8, wall_density=0.20): #genera todo el mundo del modo barrios
    if seed is not None:
        random.seed(seed)

    world_w = grid_w * WORLD_CHUNKS
    world_h = grid_h * WORLD_CHUNKS

    start_chunk = (0, 0)
    start_local = (2, 2)
    start_world = local_to_world(start_chunk[0], start_chunk[1], start_local[0], start_local[1], grid_w, grid_h)

    all_world = [(c, r) for r in range(world_h) for c in range(world_w)]
    free_world = [cell for cell in all_world if cell != start_world]
    random.shuffle(free_world)

    used = {start_world}
    orders = []

    def take_free_world_cell(): #esta funcion encapsula la logica de obtener una celda valida
        while free_world:
            cell = free_world.pop()
            if cell not in used:
                used.add(cell)
                return cell
        raise RuntimeError("No hay suficientes celdas libres en el mundo para generar ordenes.")

    for oid in range(num_orders):
        p = take_free_world_cell()
        d = take_free_world_cell()
        tip = random.randint(10, 70)
        deadline = random.uniform(6.0, 12.0)
        orders.append(Order(order_id=oid, pickup=p, dropoff=d, tip=tip, deadline=deadline))

    blocked = {start_world}
    for o in orders:
        blocked.add(o.pickup)
        blocked.add(o.dropoff)

    walls_world = set()
    target_walls = int(world_w * world_h * wall_density)

    candidates = [cell for cell in all_world if cell not in blocked]
    random.shuffle(candidates)

    def still_playable(walls_set):
        reachable = bfs_reachable_world(start_world, walls_set, world_w, world_h)
        for o in orders:
            if o.pickup not in reachable or o.dropoff not in reachable:
                return False
        return True

    placed = 0
    for cell in candidates:
        if placed >= target_walls:
            break
        walls_world.add(cell)
        if still_playable(walls_world):
            placed += 1
        else:
            walls_world.remove(cell)

    return start_world, walls_world, orders, (world_w, world_h)

#Seccion 10: funciones de dibujo

def cell_to_px(layout: Layout, col: int, row: int) -> tuple[int, int]: #convierte las coordenadas en pixeles
    x = layout.map_x + col * layout.cell
    y = layout.map_y + row * layout.cell
    return x, y

def draw_soft_bg(screen, w, h): #Fondo con viñeta suave
    overlay = pygame.Surface((w, h), pygame.SRCALPHA)
    
    cx, cy = w // 2, h // 2 #viñeta
    maxr = int(math.hypot(cx, cy))
    for i in range(0, 160, 8):
        r = int(maxr * (i / 160.0))
        a = int(120 * (i / 160.0))
        pygame.draw.circle(overlay, (0, 0, 0, a), (cx, cy), r)
    screen.blit(overlay, (0, 0))

def draw_grid(screen, layout: Layout): #dibuja el marco del mapa y suelo cuaddriculado
    panel_rect = pygame.Rect(layout.map_x - 10, layout.map_y - 10, layout.map_w + 20, layout.map_h + 20)
    pygame.draw.rect(screen, (18, 18, 26), panel_rect, border_radius=14)
    pygame.draw.rect(screen, (95, 95, 130), panel_rect, 2, border_radius=14)
    for row in range(layout.grid_h):
        for col in range(layout.grid_w):
            x, y = cell_to_px(layout, col, row)
            rect = pygame.Rect(x, y, layout.cell, layout.cell)
            base = TILE_A if (row + col) % 2 == 0 else TILE_B
            pygame.draw.rect(screen, base, rect)
            pygame.draw.rect(screen, GRID_LINE, rect, 1)

def draw_side_panel(screen, layout: Layout, title_font, small_font, mode_title: str): #dibuja el panel lateral derecho
    panel = pygame.Rect(layout.side_x, layout.side_y, layout.side_w, layout.side_h)
    pygame.draw.rect(screen, (14, 14, 18), panel, border_radius=16)
    pygame.draw.rect(screen, (75, 75, 100), panel, 2, border_radius=16)

    t = title_font.render("Panel", True, HUD_TEXT)
    screen.blit(t, (layout.side_x + 14, layout.side_y + 10))

    mt = small_font.render(f"Modo: {mode_title}", True, HUD_SUB)
    screen.blit(mt, (layout.side_x + 14, layout.side_y + 46))

def highlight_cell(screen, layout: Layout, col, row): #resalta la celda del gato
    x, y = cell_to_px(layout, col, row)
    rect = pygame.Rect(x, y, layout.cell, layout.cell)
    s = pygame.Surface((layout.cell, layout.cell), pygame.SRCALPHA)
    pygame.draw.rect(s, (255, 255, 255, 40), (0, 0, layout.cell, layout.cell), border_radius=7)
    pygame.draw.rect(s, (255, 255, 255, 90), (0, 0, layout.cell, layout.cell), 2, border_radius=7)
    screen.blit(s, rect.topleft)

def highlight_target(screen, layout: Layout, col, row): #indica el objeto recomendado
    x, y = cell_to_px(layout, col, row)
    rect = pygame.Rect(x, y, layout.cell, layout.cell)
    s = pygame.Surface((layout.cell, layout.cell), pygame.SRCALPHA)
    pygame.draw.rect(s, (255, 200, 90, 60), (0, 0, layout.cell, layout.cell), border_radius=7)
    pygame.draw.rect(s, (255, 200, 90, 140), (0, 0, layout.cell, layout.cell), 2, border_radius=7)
    screen.blit(s, rect.topleft)

def draw_marker(screen, layout: Layout, col, row, fill_color, letter, font): #dibuja los pickups y dropoffs
    x, y = cell_to_px(layout, col, row)
    cx = x + layout.cell // 2
    cy = y + layout.cell // 2

    rad = max(10, layout.cell // 3)
    pygame.draw.circle(screen, fill_color, (cx, cy), rad)
    pygame.draw.circle(screen, (18, 18, 22), (cx, cy), rad, 2)
    # brillo
    shine = pygame.Surface((rad * 2, rad * 2), pygame.SRCALPHA)
    pygame.draw.circle(shine, (255, 255, 255, 70), (int(rad * 0.7), int(rad * 0.7)), int(rad * 0.45))
    screen.blit(shine, (cx - rad, cy - rad))

    label = font.render(letter, True, (10, 10, 15))
    screen.blit(label, (cx - label.get_width() // 2, cy - label.get_height() // 2))

def draw_energy_station(screen, layout: Layout, col, row, font): #dibuja las estaciones de energia
    x, y = cell_to_px(layout, col, row)
    rect = pygame.Rect(x + 6, y + 6, layout.cell - 12, layout.cell - 12)
    pygame.draw.rect(screen, ENERGY_STATION_COLOR, rect, border_radius=10)
    pygame.draw.rect(screen, ENERGY_STATION_BORDER, rect, 2, border_radius=10)
    label = font.render("E", True, (10, 20, 12))
    screen.blit(label, (rect.centerx - label.get_width() // 2, rect.centery - label.get_height() // 2))

def draw_button(screen, font, btn: Button, mouse_pos): #dibuja los botones interactivos
    hover = btn.rect.collidepoint(mouse_pos)
    bg = (76, 76, 115) if hover else (56, 56, 88)
    pygame.draw.rect(screen, bg, btn.rect, border_radius=14)
    pygame.draw.rect(screen, (165, 165, 210), btn.rect, 2, border_radius=14)
    # brillo sutil arriba
    shine = pygame.Surface((btn.rect.w, btn.rect.h), pygame.SRCALPHA)
    pygame.draw.rect(shine, (255, 255, 255, 18), (2, 2, btn.rect.w - 4, btn.rect.h // 2), border_radius=12)
    screen.blit(shine, btn.rect.topleft)

    label = font.render(btn.text, True, (240, 240, 255))
    screen.blit(label, (btn.rect.centerx - label.get_width() // 2, btn.rect.centery - label.get_height() // 2))

def get_clicked_button(buttons, mouse_pos): #devuelve el boton clickeado
    for b in buttons:
        if b.rect.collidepoint(mouse_pos):
            return b
    return None

def draw_paw_print(screen, x, y, scale=1.0, alpha=160): #patitas decorativas del gato
    s = pygame.Surface((int(80 * scale), int(70 * scale)), pygame.SRCALPHA)
    col = (210, 210, 255, alpha)
    line = (60, 60, 90, min(200, alpha + 30))

    base_r = int(20 * scale)
    toe_r = int(10 * scale)

    pygame.draw.circle(s, col, (int(40 * scale), int(44 * scale)), base_r)
    pygame.draw.circle(s, col, (int(22 * scale), int(22 * scale)), toe_r)
    pygame.draw.circle(s, col, (int(40 * scale), int(16 * scale)), toe_r)
    pygame.draw.circle(s, col, (int(58 * scale), int(22 * scale)), toe_r)
    # borde suave
    pygame.draw.circle(s, line, (int(40 * scale), int(44 * scale)), base_r, 2)
    pygame.draw.circle(s, line, (int(22 * scale), int(22 * scale)), toe_r, 2)
    pygame.draw.circle(s, line, (int(40 * scale), int(16 * scale)), toe_r, 2)
    pygame.draw.circle(s, line, (int(58 * scale), int(22 * scale)), toe_r, 2)

    screen.blit(s, (x, y))

#Seccion 11: dibujos del gato

def draw_cat_sprite(screen, center_x, center_y, size): #sprite del gato dentro del mapa
    cx, cy = int(center_x), int(center_y)
    size = max(18, int(size))
    #sombra
    sh = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, 70), (size * 0.25, size * 1.05, size * 1.5, size * 0.55))
    screen.blit(sh, (cx - size, cy - size))
    #colita
    tail = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
    pygame.draw.arc(tail, CAT_FUR_2, (int(size * 0.6), int(size * 0.5), int(size * 1.0), int(size * 1.0)), 0.8, 2.7, max(3, size // 6))
    pygame.draw.arc(tail, CAT_LINE, (int(size * 0.6), int(size * 0.5), int(size * 1.0), int(size * 1.0)), 0.8, 2.7, 2)
    screen.blit(tail, (cx - size, cy - size))
    #cuerpo
    body_w = int(size * 1.15)
    body_h = int(size * 0.95)
    body = pygame.Rect(cx - body_w // 2, cy - body_h // 2 + int(size * 0.35), body_w, body_h)
    pygame.draw.ellipse(screen, CAT_FUR_2, body)
    pygame.draw.ellipse(screen, CAT_LINE, body, 2)
    #cabeza
    head_r = int(size * 0.55)
    head_cy = cy - int(size * 0.15)
    pygame.draw.circle(screen, CAT_FUR, (cx, head_cy), head_r)
    pygame.draw.circle(screen, CAT_LINE, (cx, head_cy), head_r, 2)
    #orejitas
    e = int(head_r * 0.85)
    ear1 = [(cx - int(head_r * 0.75), head_cy - int(head_r * 0.25)),
            (cx - int(head_r * 0.15), head_cy - e),
            (cx - int(head_r * 0.05), head_cy - int(head_r * 0.10))]
    ear2 = [(cx + int(head_r * 0.75), head_cy - int(head_r * 0.25)),
            (cx + int(head_r * 0.15), head_cy - e),
            (cx + int(head_r * 0.05), head_cy - int(head_r * 0.10))]
    pygame.draw.polygon(screen, CAT_FUR, ear1)
    pygame.draw.polygon(screen, CAT_FUR, ear2)
    pygame.draw.polygon(screen, CAT_LINE, ear1, 2)
    pygame.draw.polygon(screen, CAT_LINE, ear2, 2)
    #ojos
    eye_dx = int(head_r * 0.45)
    eye_y = head_cy + int(head_r * 0.10)
    pygame.draw.circle(screen, CAT_EYE, (cx - eye_dx, eye_y), int(head_r * 0.22))
    pygame.draw.circle(screen, CAT_EYE, (cx + eye_dx, eye_y), int(head_r * 0.22))
    pygame.draw.circle(screen, CAT_PUPIL, (cx - eye_dx, eye_y), int(head_r * 0.10))
    pygame.draw.circle(screen, CAT_PUPIL, (cx + eye_dx, eye_y), int(head_r * 0.10))
    #nariz y boca
    nose = (cx, head_cy + int(head_r * 0.32))
    pygame.draw.polygon(screen, CAT_NOSE, [(nose[0], nose[1]), (nose[0] - 5, nose[1] + 4), (nose[0] + 5, nose[1] + 4)])
    pygame.draw.arc(screen, CAT_LINE, (cx - 12, nose[1] + 2, 12, 10), 3.4, 5.2, 2)
    pygame.draw.arc(screen, CAT_LINE, (cx, nose[1] + 2, 12, 10), 4.2, 6.0, 2)
    #bigotes
    wy = head_cy + int(head_r * 0.32)
    for i in (-1, 0, 1):
        pygame.draw.line(screen, CAT_WHISK, (cx - 5, wy + i * 3), (cx - head_r - 2, wy + i * 3 - 2), 2)
        pygame.draw.line(screen, CAT_WHISK, (cx + 5, wy + i * 3), (cx + head_r + 2, wy + i * 3 - 2), 2)

def draw_cat_logo(screen, center_x, center_y, size): #gato para el logo del splash o pantalla de inicio
    cx, cy = int(center_x), int(center_y)
    size = max(80, int(size))
    #brillo de detrás
    glow = pygame.Surface((size * 3, size * 3), pygame.SRCALPHA)
    pygame.draw.circle(glow, (255, 200, 120, 40), (size * 1, size * 1), int(size * 0.95))
    pygame.draw.circle(glow, (255, 200, 120, 20), (size * 1, size * 1), int(size * 1.20))
    screen.blit(glow, (cx - size, cy - size))
    #cara
    face_r = int(size * 0.55)
    pygame.draw.circle(screen, CAT_FUR, (cx, cy), face_r)
    pygame.draw.circle(screen, CAT_LINE, (cx, cy), face_r, 3)
    # orejas grandes
    ear_h = int(face_r * 0.95)
    ear_w = int(face_r * 0.85)
    ear1 = [(cx - int(face_r * 0.75), cy - int(face_r * 0.15)),
            (cx - int(face_r * 0.20), cy - ear_h),
            (cx - int(face_r * 0.05), cy - int(face_r * 0.10))]
    ear2 = [(cx + int(face_r * 0.75), cy - int(face_r * 0.15)),
            (cx + int(face_r * 0.20), cy - ear_h),
            (cx + int(face_r * 0.05), cy - int(face_r * 0.10))]
    pygame.draw.polygon(screen, CAT_FUR, ear1)
    pygame.draw.polygon(screen, CAT_FUR, ear2)
    pygame.draw.polygon(screen, CAT_LINE, ear1, 3)
    pygame.draw.polygon(screen, CAT_LINE, ear2, 3)
    # ojos grandes
    eye_r = int(face_r * 0.18)
    eye_dx = int(face_r * 0.38)
    eye_y = cy + int(face_r * 0.05)
    pygame.draw.circle(screen, CAT_EYE, (cx - eye_dx, eye_y), eye_r)
    pygame.draw.circle(screen, CAT_EYE, (cx + eye_dx, eye_y), eye_r)
    pygame.draw.circle(screen, CAT_PUPIL, (cx - eye_dx, eye_y), int(eye_r * 0.45))
    pygame.draw.circle(screen, CAT_PUPIL, (cx + eye_dx, eye_y), int(eye_r * 0.45))
    # nariz
    ny = cy + int(face_r * 0.32)
    pygame.draw.polygon(screen, CAT_NOSE, [(cx, ny), (cx - 8, ny + 7), (cx + 8, ny + 7)])
    pygame.draw.arc(screen, CAT_LINE, (cx - 18, ny + 4, 18, 14), 3.4, 5.2, 3)
    pygame.draw.arc(screen, CAT_LINE, (cx, ny + 4, 18, 14), 4.2, 6.0, 3)
    # bigotes
    for i in (-1, 0, 1):
        pygame.draw.line(screen, CAT_WHISK, (cx - 10, ny + 2 + i * 6), (cx - face_r - 18, ny - 2 + i * 6), 3)
        pygame.draw.line(screen, CAT_WHISK, (cx + 10, ny + 2 + i * 6), (cx + face_r + 18, ny - 2 + i * 6), 3)

#Seccion 12: como se ven las paredes

WALL_PALETTE = [ #lista de colores
    (90, 110, 255), (255, 120, 150), (120, 255, 185),  #azul, rosa y verde
    (255, 200, 90), (200, 140, 255), (90, 230, 255),]   #amarillo, violeta y cyan

def color_for_wall(state, wall_cell_world): # color fijo por celda (para que no "parpadee")
    return state["wall_colors"].get(wall_cell_world, (90, 90, 120))

def draw_walls_local(screen, layout: Layout, state, walls_local: set[tuple[int, int]], walls_world_local_map: dict): #dibuja las paredes posibles
    for (col, row) in walls_local:
        wc_wr = walls_world_local_map.get((col, row))
        c = color_for_wall(state, wc_wr) if wc_wr else (90, 90, 120)
        x, y = cell_to_px(layout, col, row)
        rect = pygame.Rect(x + 5, y + 5, layout.cell - 10, layout.cell - 10)

        pygame.draw.rect(screen, (24, 24, 34), rect, border_radius=10)
        inner = rect.inflate(-6, -6)
        pygame.draw.rect(screen, c, inner, border_radius=9)
        pygame.draw.rect(screen, (18, 18, 22), inner, 2, border_radius=9)

#Seccion 13: HUD

def draw_hud_centered(screen, layout: Layout, font, small_font, #dibuja el HUD centrado horizontalmente
                      fps, score, carrying, carry_max, level,
                      time_text, mode_key, hint_text, extra_line=""):
    base_w = layout.width #ancho total de la ventana
    y0 = layout.hud_y

    title = font.render("Cat Delivery", True, HUD_TEXT)
    sub = small_font.render("WASD/Flechas: mover  |  P/Espacio: Pausa  |  ESC: Salir  |  F11: Fullscreen", True, HUD_SUB)

    line_main = small_font.render(
        f"Nivel: {level}  |  Tiempo: {time_text}  |  FPS: {int(fps)}  |  Score: {score}  |  Cargando: {len(carrying)}/{carry_max}",
        True, HUD_SUB)

    line_mode = small_font.render(f"Modo: {mode_key}  |  {hint_text}", True, (210, 210, 255))
    line_extra = small_font.render(extra_line, True, HUD_SUB) if extra_line else None

    def blit_center(surf, y):
        screen.blit(surf, (base_w // 2 - surf.get_width() // 2, y))

    blit_center(title, y0 + 6)
    blit_center(sub, y0 + 44)
    blit_center(line_main, y0 + 72)
    blit_center(line_mode, y0 + 100)
    if line_extra:
        blit_center(line_extra, y0 + 128)

#Seccion 14: dibujar el minimapa en el modo de barrios

def draw_minimap_barrios(screen, small_font, state, layout: Layout): #funcion de dibujo
    if state["mode"].key != "cluster":
        return
    pad = 14
    right_x = layout.side_x
    right_y = layout.side_y
    right_w = layout.side_w
    right_h = layout.side_h

    mm_size = clamp(min(210, right_w - pad * 2), 150, 220) # minimapa adaptable al ancho del panel
    cell = mm_size // 3

    header_h = 78 # espacio reservado arriba para títulos del panel
    if right_h < header_h + mm_size + 40:
        return

    x0 = right_x + (right_w - mm_size) // 2
    y0 = right_y + header_h

    barrios_p = set()
    barrios_d = set()

    for o in state["orders"]:
        oid = o.order_id
        if oid in state["expired"]:
            continue
        if oid not in state["picked"] and oid not in state["delivered"]:
            bx, by, _, _ = world_to_chunk_local(o.pickup[0], o.pickup[1], layout.grid_w, layout.grid_h)
            barrios_p.add((bx, by))
        if oid not in state["delivered"]:
            bx, by, _, _ = world_to_chunk_local(o.dropoff[0], o.dropoff[1], layout.grid_w, layout.grid_h)
            barrios_d.add((bx, by))

    panel = pygame.Rect(x0 - 12, y0 - 46, mm_size + 24, mm_size + 66)
    pygame.draw.rect(screen, (18, 18, 26), panel, border_radius=14)
    pygame.draw.rect(screen, (95, 95, 130), panel, 2, border_radius=14)

    title = small_font.render("Barrios (P/D)", True, HUD_TEXT)
    subtitle = small_font.render("P=Pickups, D=Dropoffs", True, HUD_SUB)
    screen.blit(title, (panel.x + 14, panel.y + 10))
    screen.blit(subtitle, (panel.x + 14, panel.y + 30))

    for gy in range(3):
        for gx in range(3):
            chunk_x = gx + CHUNK_MIN
            chunk_y = gy + CHUNK_MIN
            r = pygame.Rect(
                x0 + gx * cell,
                y0 + gy * cell,
                cell - 4,
                cell - 4)

            is_current = (chunk_x == state["chunk_x"] and chunk_y == state["chunk_y"])
            base = (72, 72, 105) if is_current else (42, 42, 64)

            pygame.draw.rect(screen, base, r, border_radius=8)
            pygame.draw.rect(screen, (140, 140, 185), r, 2, border_radius=8)

            p = (chunk_x, chunk_y) in barrios_p
            d = (chunk_x, chunk_y) in barrios_d

            txt = "P/D" if (p and d) else ("P" if p else ("D" if d else ""))
            if txt:
                lab = small_font.render(txt, True, (235, 235, 255))
                screen.blit(lab, (r.centerx - lab.get_width() // 2, r.centery - lab.get_height() // 2))

#Seccion 15: modos y algoritmos

def get_modes(): #lista con modos de juego disponibles
    return [
        ModeConfig(
            key="classic",
            title="Modo Clasico",
            description="Modo simple: entrega paquetes antes de que se acabe el tiempo global. Sin brillos ni recomendaciones.",
            carry_max=2, time_max=40.0, time_gain=4.0, num_orders_start=3, wall_density_start=0.20),
        ModeConfig(
            key="deadlines",
            title="Modo Deadlines",
            description="Solo 1 paquete a la vez. Al recoger, empieza el timer del paquete (max 12s). Si expira, pierdes un strike.",
            carry_max=1, time_max=60.0, time_gain=4.0, num_orders_start=4, wall_density_start=0.22),
        ModeConfig(
            key="energy",
            title="Modo Energia",
            description="Sin tiempo global. Cada movimiento consume energia. Entregar da energia, y hay puntos de recarga (E).",
            carry_max=2, time_max=0.0, time_gain=0.0, num_orders_start=3, wall_density_start=0.20 ),
        ModeConfig(
            key="cluster",
            title="Modo Barrios (3x3)",
            description="Mundo 3x3. Los pedidos pueden estar en barrios distintos. Mini-mapa indica dónde hay pickups/dropoffs.",
            carry_max=3, time_max=180.0, time_gain=4.0, num_orders_start=8, wall_density_start=0.18),]

def order_by_id(orders: list[Order], oid: int): #busca ordener por su ID
    for o in orders:
        if o.order_id == oid:
            return o
    return None

def world_dims_for_mode(mode_key: str, grid_w: int, grid_h: int) -> tuple[int, int]: #devuelve las dimensiones reales del mundo
    if mode_key == "cluster":
        return grid_w * WORLD_CHUNKS, grid_h * WORLD_CHUNKS
    return grid_w, grid_h

def get_cat_world_cell(state, grid_w: int, grid_h: int) -> tuple[int, int]: #devuelve la posicion del gato en coordenadas globales
    if state["mode"].key == "cluster":
        return local_to_world(state["chunk_x"], state["chunk_y"], state["cat_col"], state["cat_row"], grid_w, grid_h)
    return state["cat_col"], state["cat_row"]

def cost_between(state, a: tuple[int, int], b: tuple[int, int]) -> float: #calcula el costo minimo entre dos celdas
    world_w, world_h = state["world_w"], state["world_h"]
    return dijkstra_cost_generic(a, b, state["walls_world"], state["traffic"], world_w, world_h)

def recommend_none(state): #no da recomendaciones (usada en modo clasico)
    return None, ""

def recommend_greedy(state, grid_w: int, grid_h: int): #utiliza greedy para maximizar la recompensa por costo
    cat = get_cat_world_cell(state, grid_w, grid_h)
    eps = 1e-6
    if state["carrying"]:
        best = None
        best_score = -1e9
        for oid in state["carrying"]:
            o = order_by_id(state["orders"], oid)
            if not o:
                continue
            c = cost_between(state, cat, o.dropoff)
            sc = (25 + o.tip) / (c + eps)
            if sc > best_score:
                best_score = sc
                best = (oid, o.dropoff, sc)
        if best:
            oid, target, sc = best
            return target, f"Entrega O{oid} (score={sc:.2f})"

    if len(state["carrying"]) < state["mode"].carry_max:
        best = None
        best_score = -1e9
        for o in state["orders"]:
            oid = o.order_id
            if oid in state["picked"] or oid in state["delivered"] or oid in state["expired"]:
                continue
            c1 = cost_between(state, cat, o.pickup)
            c2 = cost_between(state, o.pickup, o.dropoff)
            total = c1 + c2
            sc = (25 + o.tip) / (total + eps)
            if sc > best_score:
                best_score = sc
                best = (oid, o.pickup, sc)
        if best:
            oid, target, sc = best
            return target, f"Recoge O{oid} (score={sc:.2f})"
    return None, ""

def recommend_deadlines(state, grid_w: int, grid_h: int): #estrategia para los deadlines
    cat = get_cat_world_cell(state, grid_w, grid_h)
    eps = 1e-6
    active = state.get("active_oid")
    if active is not None:
        o = order_by_id(state["orders"], active)
        if o:
            return o.dropoff, f"Entrega O{active} (paquete={state.get('active_time',0.0):.1f}s)"
    best = None
    best_metric = float("inf")
    for o in state["orders"]:
        oid = o.order_id
        if oid in state["picked"] or oid in state["delivered"] or oid in state["expired"]:
            continue
        t = float(o.deadline)
        c1 = cost_between(state, cat, o.pickup)
        c2 = cost_between(state, o.pickup, o.dropoff)
        total = c1 + c2
        metric = (t + 0.1) / (total + eps)
        if metric < best_metric:
            best_metric = metric
            best = (oid, o.pickup, t)

    if best:
        oid, target, t = best
        return target, f"Recoge O{oid} (deadline={t:.1f}s)"
    return None, ""

def compute_hint(state, grid_w: int, grid_h: int): #decide que algoritmo usar segun el modo
    key = state["mode"].key
    if key == "classic":
        return recommend_none(state)
    if key == "deadlines":
        return recommend_deadlines(state, grid_w, grid_h)
    if key == "energy":
        return recommend_greedy(state, grid_w, grid_h)
    if key == "cluster":
        return recommend_greedy(state, grid_w, grid_h)
    return None, ""

def update_deadlines(state, dt): #actualiza el tiempo del paquete activo
    if state["mode"].key != "deadlines":
        return
    oid = state.get("active_oid")
    if oid is None:
        return
    state["active_time"] = max(0.0, state["active_time"] - dt)
    if state["active_time"] <= 0.0:
        state["expired"].add(oid)

        if oid in state["carrying"]:
            state["carrying"].remove(oid)
        if oid in state["picked"]:
            state["picked"].remove(oid)

        state["active_oid"] = None
        state["active_time"] = 0.0
        state["active_time_max"] = 0.0

        state["score"] = max(0, state["score"] - 30)
        state["combo"] = 1

        state["strikes"] += 1
        if state["strikes"] >= state["max_strikes"]:
            state["game_over"] = True

#Seccion 16: main

def main(start_mode_key="classic"): #funcion principal del juego
    pygame.init() #inicia todos los modulos en pygame
    GRID_W = 22 #dimensiones base del grid (no en pixeles)
    GRID_H = 14
    fullscreen = True #estado de la pantalla

    def set_display(fs: bool): #funcion interna - cambia entre pantalla completa y ventana
        nonlocal fullscreen #permite modificar el fullscreen fuera de la funcion
        fullscreen = fs #actualiza el estado
        if fs: #si se quiere pantalla completa
            info = pygame.display.Info() #se obtiene resolucion del monitos
            w, h = info.current_w, info.current_h
            try: #intenta modo fullscreen
                scr = pygame.display.set_mode((w, h), pygame.FULLSCREEN | pygame.SCALED)
            except pygame.error: #sallback si falla
                scr = pygame.display.set_mode((w, h), pygame.FULLSCREEN)
        else: #si se quiere modo ventana
            scr = pygame.display.set_mode((1100, 760), pygame.RESIZABLE)
        return scr #vuelve a la superficie principal

    screen = set_display(True) #inicia el juego en pantalla completa
    pygame.display.set_caption("Cat Delivery") #titulo de la ventana
    clock = pygame.time.Clock() #controla fps y dt
    font = pygame.font.SysFont("Segoe UI", 34, bold=True) #estas son las fuentes del juego
    big_font = pygame.font.SysFont("Segoe UI", 58, bold=True)
    small_font = pygame.font.SysFont("Segoe UI", 18)
    title_font = pygame.font.SysFont("Segoe UI", 22, bold=True)
    paused = False #el juego no empieza pausado
    current_screen = Screen.Splash 
    modes = get_modes() #obtiene la lista de ModeConfig
    selected_mode = next((m for m in modes if m.key == start_mode_key), modes[0]) #selecciona el modo inicial

    splash_start_btn = None #aqui estan las variables de los botones usados
    menu_buttons = []
    back_btn = None
    start_btn = None
    pause_buttons = [] #botones contextuales del juego
    game_over_buttons = []
    level_continue_btn = None #votones del modo barrios al completar nivel
    level_menu_btn = None
    level_complete_buttons = []

    state = { #diccionario central que guarda todo lo mutable del juego
        "mode": selected_mode, "level": 1, "score": 0, "combo": 1,#datos basicos del jugador
        "time_left": selected_mode.time_max, "game_over": False,
        "level_complete": False, #solo se usa en barrios
        "cat_col": 0, "cat_row": 0, "chunk_x": 0, "chunk_y": 0, #posicion logica del gato y barrio actual
        "cat_px_x": 0.0, "cat_px_y": 0.0, "target_px_x": 0.0, "target_px_y": 0.0, #posicion en pixeles
        "world_w": GRID_W, "world_h": GRID_H, "walls_world": set(), "wall_colors": {}, #dimensiones del mundo
        "orders": [], "order_colors": {}, #lista y colores de las ordenes
        "traffic": {}, "traffic_cd": 0.0, #mapa de costos
        "carrying": [], "picked": set(), "delivered": set(), "expired": set(),  #ciclo de una orden
        "active_oid": None, "active_time": 0.0, "active_time_max": 0.0,
        "strikes": 0, "max_strikes": 3,#control del modo deadlines
        "energy": 0, "energy_max": 0, "energy_stations": set(), "energy_used": set(), #control modo energia
        "full_msg_time": 0.0, "hint_target": None, "hint_text": "", #mensajes temporales
    }
    SMOOTH = 16.0 #suavizado del movimiento

    def rebuild_ui(layout: Layout): #aqui se construye los botones segun el tamano
        nonlocal splash_start_btn, menu_buttons, back_btn, start_btn
        nonlocal pause_buttons, game_over_buttons
        nonlocal level_continue_btn, level_menu_btn, level_complete_buttons
        #Splash
        splash_start_btn = Button(
            pygame.Rect(layout.width // 2 - 210, int(layout.height * 0.62), 420, 58),
            "Iniciar","start")
        #Menu
        btn_w = min(760, layout.width - 200)
        btn_h = 54
        start_y = 190
        gap = 14
        x = layout.width // 2 - btn_w // 2
        menu_buttons = [
            Button(pygame.Rect(x, start_y + i * (btn_h + gap), btn_w, btn_h), m.title, m)
            for i, m in enumerate(modes)]
        back_btn = Button(pygame.Rect(layout.width // 2 - 260, layout.height - 105, 220, 54), "Back", "back")
        start_btn = Button(pygame.Rect(layout.width // 2 + 40, layout.height - 105, 220, 54), "Start", "start")
        # Pausa / Game over
        pause_resume_btn = Button(pygame.Rect(layout.width // 2 - 190, layout.height // 2 - 50, 380, 54), "Resume", "resume")
        pause_restart_btn = Button(pygame.Rect(layout.width // 2 - 190, layout.height // 2 + 18, 380, 54), "Restart", "restart")
        pause_menu_btn = Button(pygame.Rect(layout.width // 2 - 190, layout.height // 2 + 86, 380, 54), "Menu", "menu")
        pause_buttons = [pause_resume_btn, pause_restart_btn, pause_menu_btn]
        game_over_buttons = [pause_restart_btn, pause_menu_btn]
        # Nivel completado (Barrios)
        level_continue_btn = Button(pygame.Rect(layout.width // 2 - 190, layout.height // 2 + 10, 380, 54), "Continue", "continue")
        level_menu_btn = Button(pygame.Rect(layout.width // 2 - 190, layout.height // 2 + 78, 380, 54), "Menu", "menu")
        level_complete_buttons = [level_continue_btn, level_menu_btn]

    def snap_cat(layout: Layout): #esto sincroniza al gato de forma logica y visual
        x, y = cell_to_px(layout, state["cat_col"], state["cat_row"])
        state["cat_px_x"] = x + layout.cell / 2
        state["cat_px_y"] = y + layout.cell / 2
        state["target_px_x"] = state["cat_px_x"]
        state["target_px_y"] = state["cat_px_y"]

    def place_energy_stations(mode_key: str, walls_world: set[tuple[int, int]], orders: list[Order], world_w: int, world_h: int, k: int): #se colocan las estaciones de energia
        if mode_key != "energy":
            return set()
        blocked = set(walls_world)
        for o in orders:
            blocked.add(o.pickup)
            blocked.add(o.dropoff)
        candidates = [(c, r) for r in range(world_h) for c in range(world_w) if (c, r) not in blocked]
        random.shuffle(candidates)
        stations = set()
        for cell in candidates:
            stations.add(cell)
            if len(stations) >= k:
                break
        return stations

    def assign_wall_colors(): # color fijo por celda de pared       
        state["wall_colors"] = {}
        for w in state["walls_world"]:
            # usa hash simple para elegir color estable
            idx = (w[0] * 31 + w[1] * 17 + state["level"] * 13) % len(WALL_PALETTE)
            state["wall_colors"][w] = WALL_PALETTE[idx]

    def spawn_level(level: int, keep_time_bonus: float = 0.0): #aqui se generan los niveles
        mode = state["mode"]
        state["world_w"], state["world_h"] = world_dims_for_mode(mode.key, GRID_W, GRID_H)
        if mode.key == "cluster":
            num_orders = min(mode.num_orders_start + (level - 1) // 2, 14)
            wall_density = min(mode.wall_density_start + 0.01 * (level - 1), 0.28)

            start_world, walls_world, orders, (ww, wh) = generate_world(
                GRID_W, GRID_H, seed=None, num_orders=num_orders, wall_density=wall_density)
            state["world_w"], state["world_h"] = ww, wh
            state["walls_world"] = walls_world
            state["orders"] = orders

            cx, cy, lc, lr = world_to_chunk_local(start_world[0], start_world[1], GRID_W, GRID_H)
            state["chunk_x"], state["chunk_y"] = cx, cy
            state["cat_col"], state["cat_row"] = lc, lr
        else:
            num_orders = min(mode.num_orders_start + (level - 1) // 2, 10)
            wall_density = min(mode.wall_density_start + 0.02 * (level - 1), 0.35)

            start_local, walls_local, orders_local = generate_level_local(
                GRID_W, GRID_H, seed=None, num_orders=num_orders, wall_density=wall_density)

            state["walls_world"] = set((c, r) for (c, r) in walls_local)

            orders = []
            for (oid, p, d, tip, base_deadline) in orders_local:
                if mode.key == "deadlines":
                    hi = 12.0
                    lo = max(6.0, 12.0 - (level - 1) * 0.8)
                    dl = random.uniform(lo, hi)
                else:
                    dl = base_deadline
                orders.append(Order(order_id=oid, pickup=(p[0], p[1]), dropoff=(d[0], d[1]), tip=tip, deadline=float(dl)))

            state["orders"] = orders
            state["chunk_x"], state["chunk_y"] = 0, 0
            state["cat_col"], state["cat_row"] = start_local

        # colores
        state["order_colors"] = {o.order_id: ORDER_COLORS[o.order_id % len(ORDER_COLORS)] for o in state["orders"]}
        assign_wall_colors()

        state["carrying"].clear()
        state["picked"].clear()
        state["delivered"].clear()
        state["expired"].clear()
        state["active_oid"] = None
        state["active_time"] = 0.0
        state["active_time_max"] = 0.0

        if mode.key in ("deadlines", "cluster"):
            state["traffic"] = generate_traffic_generic(state["walls_world"], level=level, world_w=state["world_w"], world_h=state["world_h"])
            state["traffic_cd"] = 6.0
        else:
            state["traffic"] = {}
            state["traffic_cd"] = 0.0

        if mode.key == "energy":
            state["energy_max"] = 18 + 3 * len(state["orders"]) + level * 2
            state["energy"] = state["energy_max"]
            state["energy_used"].clear()
            k = clamp(2 + (level // 2), 2, 4)
            state["energy_stations"] = place_energy_stations(mode.key, state["walls_world"], state["orders"], state["world_w"], state["world_h"], k)
        else:
            state["energy_max"] = 0
            state["energy"] = 0
            state["energy_stations"].clear()
            state["energy_used"].clear()

        # TIEMPO GLOBAL
        if mode.key == "energy":
            state["time_left"] = 0.0
        else:
            # En modos con tiempo global, reinicia SIEMPRE al comenzar el nivel
            state["time_left"] = mode.time_max

        state["hint_target"] = None
        state["hint_text"] = ""
        state["full_msg_time"] = 0.0
        state["game_over"] = False

    def reset_run(mode: ModeConfig): #aqui para reiniciar la partida
        state["mode"] = mode
        state["level"] = 1
        state["score"] = 0
        state["combo"] = 1
        state["strikes"] = 0
        state["game_over"] = False
        state["level_complete"] = False
        state["full_msg_time"] = 0.0
        state["time_left"] = mode.time_max
        spawn_level(level=1, keep_time_bonus=0.0)

    def move_cluster_wrap(new_col: int, new_row: int, grid_w: int, grid_h: int): #esta es para la transicion entre barrios
        cx, cy = state["chunk_x"], state["chunk_y"]
        if new_col < 0:
            if cx > CHUNK_MIN:
                cx -= 1
                new_col = grid_w - 1
            else:
                new_col = 0
        elif new_col >= grid_w:
            if cx < CHUNK_MAX:
                cx += 1
                new_col = 0
            else:
                new_col = grid_w - 1
        if new_row < 0:
            if cy > CHUNK_MIN:
                cy -= 1
                new_row = grid_h - 1
            else:
                new_row = 0
        elif new_row >= grid_h:
            if cy < CHUNK_MAX:
                cy += 1
                new_row = 0
            else:
                new_row = grid_h - 1
        return cx, cy, new_col, new_row

    def try_move_and_interact(new_col, new_row, layout: Layout): #este es el nucleo del gameplay
        mode = state["mode"]
        if mode.key == "cluster":
            cx, cy, new_col, new_row = move_cluster_wrap(new_col, new_row, GRID_W, GRID_H)
        else:
            cx, cy = 0, 0
            new_col = clamp(new_col, 0, GRID_W - 1)
            new_row = clamp(new_row, 0, GRID_H - 1)
        new_world = local_to_world(cx, cy, new_col, new_row, GRID_W, GRID_H) if mode.key == "cluster" else (new_col, new_row)
        if new_world in state["walls_world"]:
            return
        if mode.key == "energy":
            if (new_col, new_row) != (state["cat_col"], state["cat_row"]):
                state["energy"] = max(0, state["energy"] - 1)
                if state["energy"] <= 0:
                    state["game_over"] = True
                    return
        state["chunk_x"], state["chunk_y"] = cx, cy
        state["cat_col"], state["cat_row"] = new_col, new_row

        x, y = cell_to_px(layout, new_col, new_row)
        state["target_px_x"] = x + layout.cell / 2
        state["target_px_y"] = y + layout.cell / 2

        cur_world = get_cat_world_cell(state, GRID_W, GRID_H)

        if mode.key == "energy":
            if cur_world in state["energy_stations"] and cur_world not in state["energy_used"]:
                state["energy_used"].add(cur_world)
                state["energy"] = min(state["energy_max"], state["energy"] + 12)
        #recogida
        for o in state["orders"]:
            oid = o.order_id
            if oid in state["picked"] or oid in state["delivered"] or oid in state["expired"]:
                continue

            if o.pickup == cur_world:
                if mode.key == "deadlines" and state["active_oid"] is not None:
                    state["full_msg_time"] = 0.8
                    break

                if len(state["carrying"]) < mode.carry_max:
                    state["carrying"].append(oid)
                    state["picked"].add(oid)

                    if mode.key == "deadlines":
                        base = float(o.deadline)
                        state["active_oid"] = oid
                        state["active_time"] = base
                        state["active_time_max"] = base
                else:
                    state["full_msg_time"] = 0.8
                break
        #entrega
        for o in state["orders"]:
            oid = o.order_id
            if oid in state["delivered"] or oid in state["expired"]:
                continue
            if o.dropoff == cur_world and oid in state["carrying"]:
                state["carrying"].remove(oid)
                state["delivered"].add(oid)

                gained = int((25 + o.tip) * state["combo"])
                state["score"] += gained

                if mode.key != "energy":
                    if state["time_left"] > (mode.time_max * 0.4):
                        state["combo"] = min(state["combo"] + 1, 5)
                    else:
                        state["combo"] = 1

                if mode.key not in ("energy",):
                    state["time_left"] = min(mode.time_max, state["time_left"] + mode.time_gain)

                if mode.key == "energy":
                    state["energy"] = min(state["energy_max"], state["energy"] + 5)

                if mode.key == "deadlines" and state.get("active_oid") == oid:
                    state["active_oid"] = None
                    state["active_time"] = 0.0
                    state["active_time_max"] = 0.0

                break

    def advance_level_if_done(): #estoe s para avanzar de nivel si completamos
        mode_key = state["mode"].key
        if mode_key == "deadlines":
            resolved = len(state["delivered"]) + len(state["expired"])
            if resolved == len(state["orders"]) and len(state["carrying"]) == 0 and not state["game_over"]:
                state["combo"] = 1
                state["level"] += 1
                state["score"] += 80
                spawn_level(level=state["level"], keep_time_bonus=0.0)
            return
        if mode_key == "cluster":
            if (not state["level_complete"]) and (not state["game_over"]):
                if len(state["delivered"]) == len(state["orders"]) and len(state["carrying"]) == 0:
                    state["level_complete"] = True
            return
        if len(state["delivered"]) == len(state["orders"]) and len(state["carrying"]) == 0 and not state["game_over"]:
            state["combo"] = 1
            state["level"] += 1
            state["score"] += 100
            spawn_level(level=state["level"], keep_time_bonus=0.0)

    reset_run(selected_mode) #genera el primer nivel

    last_size = (-1, -1)
    layout = compute_layout(*screen.get_size(), GRID_W, GRID_H) #construye el layout inicial
    rebuild_ui(layout) #constuye UI
    snap_cat(layout) #coloca al gato de forma visual

    running = True #loop principal del juego
    while running:
        dt = clock.tick(60) / 1000.0 #tiempo entre frames en segundos
        fps = clock.get_fps() #fps para HUD
        mouse_pos = pygame.mouse.get_pos()

        width, height = screen.get_size()
        if (width, height) != last_size: #detecta el cambio e tamano de la ventana y recalcula el size
            last_size = (width, height)
            layout = compute_layout(width, height, GRID_W, GRID_H)
            rebuild_ui(layout)
            snap_cat(layout)

        frozen = paused or state["level_complete"] or state["game_over"] #no se actualiza el juego solo el UI si esta pausado o perdio el juego

        if current_screen == Screen.Game and (not frozen):
            mode_key = state["mode"].key

            if mode_key in ("deadlines", "cluster"):
                state["traffic_cd"] -= dt
                if state["traffic_cd"] <= 0:
                    state["traffic"] = generate_traffic_generic(
                        state["walls_world"], level=state["level"], world_w=state["world_w"], world_h=state["world_h"]
                    )
                    state["traffic_cd"] = 6.0

            update_deadlines(state, dt)

            if state["full_msg_time"] > 0:
                state["full_msg_time"] = max(0.0, state["full_msg_time"] - dt)

            if mode_key not in ("energy",):
                state["time_left"] -= dt
                if state["time_left"] <= 0:
                    state["time_left"] = 0
                    state["game_over"] = True

        if current_screen == Screen.Game and (not paused) and (not state["level_complete"]):
            tgt, htxt = compute_hint(state, GRID_W, GRID_H)
            state["hint_target"] = tgt
            state["hint_text"] = htxt

        #aqui se encuentran los eventos, me maneja todo input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue

            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                screen = set_display(not fullscreen)
                last_size = (-1, -1)
                continue

            # Splash
            if current_screen == Screen.Splash:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                    continue

                if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    current_screen = Screen.Menu
                    continue

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if splash_start_btn.rect.collidepoint(event.pos):
                        current_screen = Screen.Menu
                continue

            # MENU
            if current_screen == Screen.Menu:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                    continue
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    b = get_clicked_button(menu_buttons, event.pos)
                    if b:
                        selected_mode = b.payload
                        current_screen = Screen.Rules
                continue

            #reglas
            if current_screen == Screen.Rules:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    current_screen = Screen.Menu
                    continue
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if back_btn.rect.collidepoint(event.pos):
                        current_screen = Screen.Menu
                    elif start_btn.rect.collidepoint(event.pos):
                        paused = False
                        reset_run(selected_mode)
                        snap_cat(layout)
                        current_screen = Screen.Game
                continue

            #juego
            if current_screen == Screen.Game:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                    continue

                if state["level_complete"]:
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        b = get_clicked_button(level_complete_buttons, event.pos)
                        if b:
                            if b.payload == "continue":
                                state["level_complete"] = False
                                state["combo"] = 1
                                state["level"] += 1
                                state["score"] += 120
                                spawn_level(level=state["level"], keep_time_bonus=0.0)
                                snap_cat(layout)
                            elif b.payload == "menu":
                                state["level_complete"] = False
                                paused = False
                                reset_run(state["mode"])
                                current_screen = Screen.Menu
                    continue

                if event.type == pygame.KEYDOWN:
                    if (event.key == pygame.K_p or event.key == pygame.K_SPACE) and (not state["game_over"]):
                        paused = not paused
                        continue

                if state["game_over"]:
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        b = get_clicked_button(game_over_buttons, event.pos)
                        if b:
                            if b.payload == "restart":
                                paused = False
                                reset_run(state["mode"])
                                snap_cat(layout)
                            elif b.payload == "menu":
                                paused = False
                                reset_run(state["mode"])
                                current_screen = Screen.Menu
                    continue

                if paused:
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        b = get_clicked_button(pause_buttons, event.pos)
                        if b:
                            if b.payload == "resume":
                                paused = False
                            elif b.payload == "restart":
                                paused = False
                                reset_run(state["mode"])
                                snap_cat(layout)
                            elif b.payload == "menu":
                                paused = False
                                reset_run(state["mode"])
                                current_screen = Screen.Menu
                    continue

                # movimiento
                if event.type == pygame.KEYDOWN:
                    new_col, new_row = state["cat_col"], state["cat_row"]
                    if event.key in (pygame.K_w, pygame.K_UP):
                        new_row -= 1
                    elif event.key in (pygame.K_s, pygame.K_DOWN):
                        new_row += 1
                    elif event.key in (pygame.K_a, pygame.K_LEFT):
                        new_col -= 1
                    elif event.key in (pygame.K_d, pygame.K_RIGHT):
                        new_col += 1
                    else:
                        continue
                    try_move_and_interact(new_col, new_row, layout)

        #animacion
        if current_screen == Screen.Game:
            state["cat_px_x"] += (state["target_px_x"] - state["cat_px_x"]) * (1 - math.exp(-SMOOTH * dt))
            state["cat_px_y"] += (state["target_px_y"] - state["cat_px_y"]) * (1 - math.exp(-SMOOTH * dt))
            if (not paused) and (not state["game_over"]) and (not state["level_complete"]):
                advance_level_if_done()

        #dibujo
        screen.fill(BG_COLOR)
        draw_soft_bg(screen, layout.width, layout.height)

        if current_screen == Screen.Splash:
            # Logo arriba y texto debajo
            logo_y = int(layout.height * 0.30)
            draw_cat_logo(screen, layout.width // 2, logo_y, size=int(min(layout.width, layout.height) * 0.22))

            t1 = big_font.render("Cat Delivery", True, HUD_TEXT)
            t2 = small_font.render("Un juego de entregas con modos diferentes", True, HUD_SUB)
            t3 = small_font.render("F11: Pantalla completa / ventana", True, HUD_SUB)

            y_text = int(layout.height * 0.44)
            screen.blit(t1, (layout.width // 2 - t1.get_width() // 2, y_text))
            screen.blit(t2, (layout.width // 2 - t2.get_width() // 2, y_text + 54))
            screen.blit(t3, (layout.width // 2 - t3.get_width() // 2, y_text + 78))

            draw_button(screen, font, splash_start_btn, mouse_pos)

        elif current_screen == Screen.Menu:
            # patitas decorativas
            draw_paw_print(screen, 40, 40, scale=1.2, alpha=90)
            draw_paw_print(screen, layout.width - 140, 40, scale=1.2, alpha=90)
            draw_paw_print(screen, 40, layout.height - 140, scale=1.2, alpha=70)
            draw_paw_print(screen, layout.width - 140, layout.height - 140, scale=1.2, alpha=70)

            t = font.render("Selecciona un modo", True, HUD_TEXT)
            screen.blit(t, (layout.width // 2 - t.get_width() // 2, 105))
            for b in menu_buttons:
                draw_button(screen, small_font, b, mouse_pos)

        elif current_screen == Screen.Rules:
            # patitas laterales (3 por lado)
            base_y = 110
            for i in range(3):
                draw_paw_print(screen, 35, base_y + i * 160, scale=1.05, alpha=60)
                draw_paw_print(screen, layout.width - 135, base_y + i * 160, scale=1.05, alpha=60)

            t = font.render(selected_mode.title, True, HUD_TEXT)
            screen.blit(t, (layout.width // 2 - t.get_width() // 2, 95))

            maxw = min(860, layout.width - 220)
            lines = wrap_text(selected_mode.description, small_font, maxw)
            y = 185
            for line in lines:
                img = small_font.render(line, True, HUD_SUB)
                screen.blit(img, (layout.width // 2 - img.get_width() // 2, y))
                y += 24

            extra = small_font.render(
                f"Carga max: {selected_mode.carry_max} | Tiempo max: {('—' if selected_mode.key=='energy' else f'{selected_mode.time_max:.0f}s')} | +Tiempo/entrega: {selected_mode.time_gain:.0f}s",
                True, HUD_SUB)
            screen.blit(extra, (layout.width // 2 - extra.get_width() // 2, y + 24))

            draw_button(screen, small_font, back_btn, mouse_pos)
            draw_button(screen, small_font, start_btn, mouse_pos)

        elif current_screen == Screen.Game:
            draw_grid(screen, layout)
            draw_side_panel(screen, layout, title_font, small_font, state["mode"].title)

            #paredes
            walls_local = set()
            walls_world_local_map = {}

            if state["mode"].key == "cluster":
                for (wc, wr) in state["walls_world"]:
                    cx, cy, lc, lr = world_to_chunk_local(wc, wr, GRID_W, GRID_H)
                    if cx == state["chunk_x"] and cy == state["chunk_y"]:
                        walls_local.add((lc, lr))
                        walls_world_local_map[(lc, lr)] = (wc, wr)
            else:
                for (wc, wr) in state["walls_world"]:
                    walls_local.add((wc, wr))
                    walls_world_local_map[(wc, wr)] = (wc, wr)

            # highlight objetivo
            if (not state["game_over"]) and (not state["level_complete"]):
                if state["mode"].key == "deadlines":
                    if state.get("active_oid") is not None:
                        o = order_by_id(state["orders"], state["active_oid"])
                        if o:
                            cx, cy, lc, lr = world_to_chunk_local(o.dropoff[0], o.dropoff[1], GRID_W, GRID_H)
                            if state["mode"].key != "cluster" or (cx == state["chunk_x"] and cy == state["chunk_y"]):
                                highlight_target(screen, layout, lc, lr)
                    else:
                        if state["hint_target"] is not None:
                            cx, cy, lc, lr = world_to_chunk_local(state["hint_target"][0], state["hint_target"][1], GRID_W, GRID_H)
                            if state["mode"].key != "cluster" or (cx == state["chunk_x"] and cy == state["chunk_y"]):
                                highlight_target(screen, layout, lc, lr)

                elif state["mode"].key in ("cluster",):
                    if state["hint_target"] is not None:
                        cx, cy, lc, lr = world_to_chunk_local(state["hint_target"][0], state["hint_target"][1], GRID_W, GRID_H)
                        if cx == state["chunk_x"] and cy == state["chunk_y"]:
                            highlight_target(screen, layout, lc, lr)

            highlight_cell(screen, layout, state["cat_col"], state["cat_row"])
            draw_walls_local(screen, layout, state, walls_local, walls_world_local_map)

            #estaciones de energia
            if state["mode"].key == "energy":
                for (wc, wr) in state["energy_stations"]:
                    if (wc, wr) in state["energy_used"]:
                        continue
                    cx, cy, lc, lr = world_to_chunk_local(wc, wr, GRID_W, GRID_H)
                    if state["mode"].key != "cluster" or (cx == state["chunk_x"] and cy == state["chunk_y"]):
                        draw_energy_station(screen, layout, lc, lr, small_font)

            #marcadores visibles
            for o in state["orders"]:
                oid = o.order_id
                if oid in state["expired"]:
                    continue

                if oid not in state["picked"] and oid not in state["delivered"]:
                    cx, cy, lc, lr = world_to_chunk_local(o.pickup[0], o.pickup[1], GRID_W, GRID_H)
                    if state["mode"].key != "cluster" or (cx == state["chunk_x"] and cy == state["chunk_y"]):
                        color = state["order_colors"][oid]
                        draw_marker(screen, layout, lc, lr, color, "P", small_font)

                if oid not in state["delivered"]:
                    cx, cy, lc, lr = world_to_chunk_local(o.dropoff[0], o.dropoff[1], GRID_W, GRID_H)
                    if state["mode"].key != "cluster" or (cx == state["chunk_x"] and cy == state["chunk_y"]):
                        color = state["order_colors"][oid]
                        draw_marker(screen, layout, lc, lr, color, "D", small_font)

            # gato 
            draw_cat_sprite(screen, state["cat_px_x"], state["cat_px_y"], size=layout.cell * 0.60)

            # HUD
            if state["mode"].key == "energy":
                time_text = "—"
            else:
                time_text = f"{state['time_left']:.1f}s"

            extra_line = ""
            if state["mode"].key == "deadlines":
                if state.get("active_oid") is None:
                    extra_line = f"Paquete: -  |  Failed: {len(state['expired'])}  |  Strikes: {state['strikes']}/{state['max_strikes']}"
                else:
                    extra_line = f"Paquete O{state['active_oid']}: {state['active_time']:.1f}s  |  Failed: {len(state['expired'])}  |  Strikes: {state['strikes']}/{state['max_strikes']}"
            elif state["mode"].key == "energy":
                remaining = len(state["energy_stations"]) - len(state["energy_used"])
                extra_line = f"Energia: {state['energy']}/{state['energy_max']}  |  Recargas disponibles: {remaining}"
            elif state["mode"].key == "cluster":
                extra_line = f"Barrio: {barrio_name(state['chunk_x'], state['chunk_y'])}  |  Mundo: 3x3"

            draw_hud_centered(
                screen, layout, font, small_font,
                fps, state["score"], state["carrying"], state["mode"].carry_max, state["level"],
                time_text, state["mode"].key, state["hint_text"], extra_line)

            draw_minimap_barrios(screen, small_font, state, layout)

            if state["full_msg_time"] > 0:
                warn = font.render("LLENO", True, (255, 200, 80))
                screen.blit(warn, (layout.map_x + layout.map_w - warn.get_width(), layout.hud_y + 6))

            #overlay de pausado
            if paused:
                overlay = pygame.Surface((layout.width, layout.height), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 160))
                screen.blit(overlay, (0, 0))
                t = font.render("PAUSADO", True, (255, 255, 255))
                screen.blit(t, (layout.width // 2 - t.get_width() // 2, layout.height // 2 - 140))
                for b in pause_buttons:
                    draw_button(screen, small_font, b, mouse_pos)

            #overlay de nivel completado
            if state["level_complete"]:
                overlay = pygame.Surface((layout.width, layout.height), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180))
                screen.blit(overlay, (0, 0))
                t1 = font.render(f"NIVEL {state['level']} COMPLETADO", True, (255, 255, 255))
                t2 = small_font.render("¿Continuar al siguiente nivel o volver al menu?", True, HUD_SUB)
                screen.blit(t1, (layout.width // 2 - t1.get_width() // 2, layout.height // 2 - 120))
                screen.blit(t2, (layout.width // 2 - t2.get_width() // 2, layout.height // 2 - 85))
                for b in level_complete_buttons:
                    draw_button(screen, small_font, b, mouse_pos)

            #juego perdido overlay
            if state["game_over"]:
                overlay = pygame.Surface((layout.width, layout.height), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180))
                screen.blit(overlay, (0, 0))
                t1 = font.render("GAME OVER", True, (255, 255, 255))
                t2 = small_font.render("Elige una opcion:", True, HUD_SUB)
                screen.blit(t1, (layout.width // 2 - t1.get_width() // 2, layout.height // 2 - 120))
                screen.blit(t2, (layout.width // 2 - t2.get_width() // 2, layout.height // 2 - 85))
                for b in game_over_buttons:
                    draw_button(screen, small_font, b, mouse_pos)

        pygame.display.flip()

    pygame.quit() #cierra pygame
    sys.exit() #cierra el proceso

if __name__ == "__main__": #es una buena practica y permite ejecutar el archivo directamente
    main()