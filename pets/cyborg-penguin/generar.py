import os
import glob
from PIL import Image, ImageDraw

SHEET_WIDTH = 1536
SHEET_HEIGHT = 1872
COLS = 8
CELL_W = 192
CELL_H = 208

# Buscar la imagen base automáticamente (sea .png o .jpg)
archivos = glob.glob("base*")
if not archivos:
    print("ERROR: No se encuentra ninguna imagen que empiece por 'base'")
    input("Pulsa Enter para salir...")
    exit()

img_path = archivos[0]
print(f"Cargando imagen: {img_path}")

img = Image.open(img_path).convert("RGBA")
w, h = img.size

# Limpiar fondo blanco exterior
for pt in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
    try:
        ImageDraw.floodfill(img, pt, (0, 0, 0, 0), thresh=30)
    except Exception:
        pass

bbox = img.getbbox()
if bbox:
    img = img.crop(bbox)

img.thumbnail((140, 168), Image.Resampling.NEAREST)
base = Image.new("RGBA", (CELL_W, CELL_H), (0, 0, 0, 0))
base.paste(img, ((CELL_W - img.width) // 2, CELL_H - img.height - 16), img)

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
        for s in [0, 0, 1, 2, 2, 1, 0, 0]: frames.append(mover(b, 0, s))
    elif tipo == "run_r":
        for i in range(8): frames.append(rotar(b, -3 if i % 2 == 0 else 3, -2 if i in (1, 3, 5, 7) else 0))
    elif tipo == "run_l":
        flip = b.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        for i in range(8): frames.append(rotar(flip, 3 if i % 2 == 0 else -3, -2 if i in (1, 3, 5, 7) else 0))
    elif tipo == "wave":
        for a in [0, 2, 4, 2, 0, -2, -4, -2]: frames.append(rotar(b, a, 0))
    elif tipo == "jump":
        for y in [1, 2, -6, -14, -18, -12, -4, 0]: frames.append(mover(b, 0, y))
    elif tipo == "fail":
        for i in range(8): frames.append(mover(b, 0, min(i, 4)))
    elif tipo == "wait":
        for a in [0, 1, 1, 0, 0, -1, -1, 0]: frames.append(rotar(b, a, 0))
    elif tipo == "run":
        for b_y in [0, -3, 0, -1, 0, -3, 0, -1]: frames.append(mover(b, 0, b_y))
    elif tipo == "review":
        for n in [0, 1, 2, 2, 1, 0, 0, 0]: frames.append(mover(b, 0, n))
    return frames

sheet = Image.new("RGBA", (SHEET_WIDTH, SHEET_HEIGHT), (0, 0, 0, 0))
filas = ["idle", "run_r", "run_l", "wave", "jump", "fail", "wait", "run", "review"]
for row_idx, tipo in enumerate(filas):
    frames = crear_fila(base, tipo)
    for col_idx in range(COLS):
        sheet.paste(frames[col_idx], (col_idx * CELL_W, row_idx * CELL_H), frames[col_idx])

sheet.save("spritesheet.webp", "WEBP", lossless=True)
print("\n¡EXITO! spritesheet.webp creado correctamente.")