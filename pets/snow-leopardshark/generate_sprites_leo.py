import os
import glob
from PIL import Image, ImageDraw

SHEET_WIDTH = 1536
SHEET_HEIGHT = 1872
COLS = 8
CELL_W = 192
CELL_H = 208

# Buscar la imagen
archivos = glob.glob("*leopard*")
archivos = [a for a in archivos if a.endswith((".png", ".jpg", ".jpeg"))]
if not archivos:
    print("ERROR: No se encuentra la imagen.")
    exit()

img_path = [a for a in archivos if "shark" in a] or archivos
img_path = img_path[0]
print(f"Procesando imagen: {img_path}")

img = Image.open(img_path).convert("RGBA")
w, h = img.size

# 1. Limpiar fondo blanco
for x in range(0, w, 15):
    try:
        ImageDraw.floodfill(img, (x, 0), (0, 0, 0, 0), thresh=75)
        ImageDraw.floodfill(img, (x, h - 1), (0, 0, 0, 0), thresh=75)
    except Exception: pass
for y in range(0, h, 15):
    try:
        ImageDraw.floodfill(img, (0, y), (0, 0, 0, 0), thresh=75)
        ImageDraw.floodfill(img, (w - 1, y), (0, 0, 0, 0), thresh=75)
    except Exception: pass

# 2. Borrar cualquier pixel residual debajo de la cola (zona inferior izquierda)
pix = img.load()
for y in range(int(h * 0.75), h):
    for x in range(0, int(w * 0.28)):
        pix[x, y] = (0, 0, 0, 0)

# 3. Eliminar islas flotantes
alpha = img.getchannel('A')
visited = bytearray(w * h)
alpha_bytes = alpha.tobytes()
components = []

for y in range(h):
    for x in range(w):
        idx = y * w + x
        if alpha_bytes[idx] > 0 and not visited[idx]:
            comp = []
            queue = [(x, y)]
            visited[idx] = 1
            while queue:
                cx, cy = queue.pop()
                comp.append((cx, cy))
                for nx, ny in ((cx+1, cy), (cx-1, cy), (cx, cy+1), (cx, cy-1)):
                    if 0 <= nx < w and 0 <= ny < h:
                        nidx = ny * w + nx
                        if alpha_bytes[nidx] > 0 and not visited[nidx]:
                            visited[nidx] = 1
                            queue.append((nx, ny))
            components.append(comp)

if components:
    cuerpo = max(components, key=len)
    limpio = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    orig_px = img.load()
    limpio_px = limpio.load()
    for x, y in cuerpo:
        limpio_px[x, y] = orig_px[x, y]
    img = limpio

bbox = img.getbbox()
if bbox:
    img = img.crop(bbox)

img.thumbnail((168, 140), Image.Resampling.NEAREST)

base = Image.new("RGBA", (CELL_W, CELL_H), (0, 0, 0, 0))
base.paste(img, ((CELL_W - img.width) // 2, CELL_H - img.height - 18), img)

def mover(frame, dx, dy):
    res = Image.new("RGBA", (CELL_W, CELL_H), (0, 0, 0, 0))
    res.paste(frame, (dx, dy), frame)
    return res

def rotar(frame, angulo, dy=0):
    rot = frame.rotate(angulo, resample=Image.Resampling.NEAREST, expand=False)
    if dy != 0:
        res = Image.new("RGBA", (CELL_W, CELL_H), (0, 0, 0, 0))
        res.paste(rot, (0, dy), rot)
        return res
    return rot

def crear_fila(b, tipo):
    frames = []
    if tipo == "idle":
        for s in [0, 0, 1, 1, 2, 1, 0, 0]: frames.append(mover(b, 0, s))
    elif tipo == "run_r":
        for i in range(8): frames.append(rotar(b, -2 if i % 2 == 0 else 2, -2 if i in (1, 3, 5, 7) else 0))
    elif tipo == "run_l":
        flip = b.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        for i in range(8): frames.append(rotar(flip, 2 if i % 2 == 0 else -2, -2 if i in (1, 3, 5, 7) else 0))
    elif tipo == "wave":
        for a in [0, 1, 3, 1, 0, -1, -2, -1]: frames.append(rotar(b, a, 0))
    elif tipo == "jump":
        for y in [1, 2, -8, -16, -20, -14, -6, 0]: frames.append(mover(b, 0, y))
    elif tipo == "fail":
        for i in range(8): frames.append(mover(b, 0, min(i, 4)))
    elif tipo == "wait":
        for a in [0, 1, 1, 0, 0, -1, -1, 0]: frames.append(rotar(b, a, 0))
    elif tipo == "run":
        for b_y in [0, -3, 0, -2, 0, -3, 0, -2]: frames.append(mover(b, 0, b_y))
    elif tipo == "review":
        for n in [0, 1, 2, 2, 1, 0, 0, 0]: frames.append(mover(b, 0, n))
    return frames

sheet = Image.new("RGBA", (SHEET_WIDTH, SHEET_HEIGHT), (0, 0, 0, 0))
filas = ["idle", "run_r", "run_l", "wave", "jump", "fail", "wait", "run", "review"]

for row_idx, tipo in enumerate(filas):
    frames = crear_fila(base, tipo)
    for col_idx in range(COLS):
        sheet.paste(frames[col_idx], (col_idx * CELL_W, row_idx * CELL_H), frames[col_idx])

# Guardamos con un nombre nuevo para obligar a VS Code a ignorar la cache
sheet.save("spritesheet_clean.webp", "WEBP", lossless=True)
print("\nLISTO: spritesheet_clean.webp generado con exito.")
