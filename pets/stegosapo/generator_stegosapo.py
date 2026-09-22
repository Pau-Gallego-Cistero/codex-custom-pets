import os
import json
import numpy as np
from PIL import Image

def cargar_imagen(nombre_base):
    extensiones = [".jpg", ".jpeg", ".png", ".webp", ".JPG", ".PNG"]
    for ext in extensiones:
        path = nombre_base + ext
        if os.path.exists(path):
            return path
    carpeta = os.path.dirname(nombre_base) or "."
    nombre_archivo = os.path.basename(nombre_base).lower()
    for f in os.listdir(carpeta):
        nom, ext = os.path.splitext(f)
        if nom.lower() == nombre_archivo and ext.lower() in extensiones:
            return os.path.join(carpeta, f)
    return None

def limpiar_fondo(img_path, umbral_blanco=225, umbral_negro=30):
    img = Image.open(img_path).convert("RGBA")
    arr = np.array(img, dtype=np.uint8)

    esquinas = [
        arr[0, 0, :3],
        arr[0, -1, :3],
        arr[-1, 0, :3],
        arr[-1, -1, :3]
    ]
    promedio_esquinas = np.mean(esquinas)

    if promedio_esquinas > 128:
        mascara = (
            (arr[:, :, 0] >= umbral_blanco)
            & (arr[:, :, 1] >= umbral_blanco)
            & (arr[:, :, 2] >= umbral_blanco)
        )
    else:
        mascara = (
            (arr[:, :, 0] <= umbral_negro)
            & (arr[:, :, 1] <= umbral_negro)
            & (arr[:, :, 2] <= umbral_negro)
        )

    arr[mascara, 3] = 0
    img_clean = Image.fromarray(arr)

    bbox = img_clean.getbbox()
    if bbox:
        img_clean = img_clean.crop(bbox)
    return img_clean

def ajustar_a_casilla(img, cell_w=192, cell_h=208, max_h=96, offset_x=0, offset_y=0):
    """
    Escala el sprite y asegura con márgenes de seguridad que NINGUNA parte
    del cuerpo, cabeza o cola sea cortada por los bordes de la casilla.
    """
    ratio = max_h / float(img.height)
    new_w = int(img.width * ratio)
    new_h = int(img.height * ratio)

    # Margen horizontal de seguridad para que la cabeza nunca se corte
    max_permitido_w = cell_w - 24
    if new_w > max_permitido_w:
        ratio_w = max_permitido_w / float(new_w)
        new_w = int(new_w * ratio_w)
        new_h = int(new_h * ratio_w)

    img_scaled = img.resize((new_w, new_h), Image.Resampling.NEAREST)

    base_x = (cell_w - new_w) // 2
    base_y = cell_h - new_h - 10

    pos_x = base_x + offset_x
    pos_y = base_y - offset_y

    # BLOQUEO ESTRICTO ANTI-RECORTES (Mínimo 8px de margen en todos los lados)
    margin = 8
    pos_x = max(margin, min(pos_x, cell_w - new_w - margin))
    pos_y = max(margin, min(pos_y, cell_h - new_h - margin))

    celda = Image.new("RGBA", (cell_w, cell_h), (0, 0, 0, 0))
    celda.paste(img_scaled, (pos_x, pos_y), img_scaled)
    return celda

def casilla_vacia(cell_w=192, cell_h=208):
    """Devuelve una casilla transparente (como los huecos vacíos en Wall-E)."""
    return Image.new("RGBA", (cell_w, cell_h), (0, 0, 0, 0))

def main():
    archivos = {
        "idle": cargar_imagen("stegosapo"),
        "crouch": cargar_imagen("stegos_prejump"),
        "stretch": cargar_imagen("stegosapo_forwarjump"),
        "jump": cargar_imagen("Stegosapo_jump"),
        "landing": cargar_imagen("stegosapo_landing"),
    }

    faltantes = [k for k, v in archivos.items() if v is None]
    if faltantes:
        print(f"Error: Faltan archivos: {faltantes}")
        return

    print("1. Limpiando imágenes y aplicando bordes de seguridad...")
    img_idle = limpiar_fondo(archivos["idle"])
    img_crouch = limpiar_fondo(archivos["crouch"])
    img_stretch = limpiar_fondo(archivos["stretch"])
    img_jump = limpiar_fondo(archivos["jump"])
    img_landing = limpiar_fondo(archivos["landing"])

    # Respiración suave
    w_i, h_i = img_idle.size
    img_idle_b1 = img_idle.resize((w_i + 2, h_i + 1), Image.Resampling.NEAREST)
    img_idle_b2 = img_idle.resize((w_i + 4, h_i + 2), Image.Resampling.NEAREST)

    CELL_W, CELL_H = 192, 208
    COLS, ROWS = 8, 11
    SCALE_MAX_H = 96  # Altura calibrada para permitir avance y vuelo sin recortes

    print("2. Construyendo la matriz idéntica a Wall-E con salto prolongado...")

    # --- POSES BASE DE SUELO ---
    idle_base = ajustar_a_casilla(img_idle, CELL_W, CELL_H, max_h=SCALE_MAX_H)
    idle_b1 = ajustar_a_casilla(img_idle_b1, CELL_W, CELL_H, max_h=SCALE_MAX_H)
    idle_b2 = ajustar_a_casilla(img_idle_b2, CELL_W, CELL_H, max_h=SCALE_MAX_H)
    crouch_floor = ajustar_a_casilla(img_crouch, CELL_W, CELL_H, max_h=SCALE_MAX_H)
    vacio = casilla_vacia(CELL_W, CELL_H)

    # --- CICLO DE SALTO DE LARGO VUELO (5 FOTOGRAMAS EN EL AIRE) ---
    # 0. Se agacha preparando impulso
    jump_f0 = ajustar_a_casilla(img_crouch, CELL_W, CELL_H, max_h=SCALE_MAX_H, offset_x=-16, offset_y=0)
    # 1. Despegue horizontal explosivo (sube 16px)
    jump_f1 = ajustar_a_casilla(img_stretch, CELL_W, CELL_H, max_h=SCALE_MAX_H, offset_x=-6, offset_y=16)
    # 2. Vuelo propulsado a máxima velocidad (sube 32px)
    jump_f2 = ajustar_a_casilla(img_stretch, CELL_W, CELL_H, max_h=SCALE_MAX_H, offset_x=+6, offset_y=32)
    # 3. Ápice parabólico en lo alto (altura máxima 40px)
    jump_f3 = ajustar_a_casilla(img_jump, CELL_W, CELL_H, max_h=SCALE_MAX_H, offset_x=+14, offset_y=40)
    # 4. Planeo en caída diagonal hacia el suelo (baja a 20px)
    jump_f4 = ajustar_a_casilla(img_jump, CELL_W, CELL_H, max_h=SCALE_MAX_H, offset_x=+20, offset_y=20)
    # 5. Contacto: patas delanteras tocan tierra (offset seguro para no cortar la cabeza)
    jump_f5 = ajustar_a_casilla(img_landing, CELL_W, CELL_H, max_h=SCALE_MAX_H, offset_x=+22, offset_y=0)
    # 6. Amortiguación profunda de impacto contra el suelo
    jump_f6 = ajustar_a_casilla(img_crouch, CELL_W, CELL_H, max_h=SCALE_MAX_H, offset_x=+12, offset_y=0)
    # 7. Regreso suave a reposo
    jump_f7 = ajustar_a_casilla(img_idle, CELL_W, CELL_H, max_h=SCALE_MAX_H, offset_x=0, offset_y=0)

    # --- VERSIONES ESPEJADAS (IZQUIERDA) ---
    idle_base_l = idle_base.transpose(Image.FLIP_LEFT_RIGHT)
    idle_b1_l = idle_b1.transpose(Image.FLIP_LEFT_RIGHT)
    idle_b2_l = idle_b2.transpose(Image.FLIP_LEFT_RIGHT)
    crouch_floor_l = crouch_floor.transpose(Image.FLIP_LEFT_RIGHT)

    jump_f0_l = jump_f0.transpose(Image.FLIP_LEFT_RIGHT)
    jump_f1_l = jump_f1.transpose(Image.FLIP_LEFT_RIGHT)
    jump_f2_l = jump_f2.transpose(Image.FLIP_LEFT_RIGHT)
    jump_f3_l = jump_f3.transpose(Image.FLIP_LEFT_RIGHT)
    jump_f4_l = jump_f4.transpose(Image.FLIP_LEFT_RIGHT)
    jump_f5_l = jump_f5.transpose(Image.FLIP_LEFT_RIGHT)
    jump_f6_l = jump_f6.transpose(Image.FLIP_LEFT_RIGHT)
    jump_f7_l = jump_f7.transpose(Image.FLIP_LEFT_RIGHT)

    # --- MATRIZ EXACTA SEGÚN EL ATLAS DE CODEX PET / WALL-E ---

    # Fila 0: Idle (6 frames como Wall-E, 2 últimos vacíos)
    fila_0_idle_r = [idle_base, idle_b1, idle_b2, idle_b1, idle_base, idle_base, vacio, vacio]
    fila_0_idle_l = [idle_base_l, idle_b1_l, idle_b2_l, idle_b1_l, idle_base_l, idle_base_l, vacio, vacio]

    # Fila 1: Walk right (8 frames completos de gran salto largo)
    fila_1_walk_r = [jump_f0, jump_f1, jump_f2, jump_f3, jump_f4, jump_f5, jump_f6, jump_f7]

    # Fila 2: Walk left (8 frames completos de gran salto a la izquierda)
    fila_2_walk_l = [jump_f0_l, jump_f1_l, jump_f2_l, jump_f3_l, jump_f4_l, jump_f5_l, jump_f6_l, jump_f7_l]

    # Fila 3: Waving / Acción especial (4 frames como Wall-E, 4 vacíos)
    fila_3_wave = [idle_base, idle_b1, idle_b2, idle_base, vacio, vacio, vacio, vacio]

    # Fila 4: Jumping / Celebración (5 frames como Wall-E: despegue y caída en el sitio)
    fila_4_jump = [jump_f0, jump_f1, jump_f3, jump_f5, jump_f6, vacio, vacio, vacio]

    # Fila 5: Failed / Dormido (8 frames: agachado contra el suelo descansando, como Wall-E en la caja)
    fila_5_failed = [crouch_floor, crouch_floor, crouch_floor, crouch_floor, crouch_floor, crouch_floor, crouch_floor, crouch_floor]

    # Fila 6: Waiting / Espera en suelo (6 frames como Wall-E)
    fila_6_waiting = [idle_base, idle_base, idle_b1, idle_base, idle_base, idle_b1, vacio, vacio]

    # Fila 7: Thinking / Run (6 frames como Wall-E)
    fila_7_running = [idle_base, idle_b1, idle_b2, idle_b1, idle_base, idle_base, vacio, vacio]

    # Fila 8: Review / Listo (6 frames como Wall-E)
    fila_8_review = [idle_base, idle_base, idle_b1, idle_b2, idle_b1, idle_base, vacio, vacio]

    # Filas 9 y 10: Look directions (6 frames en reposo)
    fila_9_look_r = [idle_base, idle_b1, idle_base, idle_base, idle_b1, idle_base, vacio, vacio]
    fila_10_look_l = [idle_base_l, idle_b1_l, idle_base_l, idle_base_l, idle_b1_l, idle_base_l, vacio, vacio]

    mapa_filas = [
        fila_0_idle_r,   # 0: Idle
        fila_1_walk_r,   # 1: Walk derecha (Salto de gran vuelo)
        fila_2_walk_l,   # 2: Walk izquierda
        fila_3_wave,     # 3: Waving (4 frames)
        fila_4_jump,     # 4: Jumping (5 frames)
        fila_5_failed,   # 5: Failed / Durmiendo en suelo (8 frames)
        fila_6_waiting,  # 6: Waiting (6 frames)
        fila_7_running,  # 7: Thinking (6 frames)
        fila_8_review,   # 8: Review (6 frames)
        fila_9_look_r,   # 9: Look derecha (6 frames)
        fila_10_look_l   # 10: Look izquierda (6 frames)
    ]

    print("3. Generando spritesheet.webp con la matriz exacta de Wall-E...")
    spritesheet = Image.new("RGBA", (CELL_W * COLS, CELL_H * ROWS), (0, 0, 0, 0))

    for row_idx, fila in enumerate(mapa_filas):
        for col_idx in range(COLS):
            frame = fila[col_idx]
            spritesheet.paste(frame, (col_idx * CELL_W, row_idx * CELL_H), frame)

    spritesheet.save("spritesheet.webp", format="WEBP", lossless=True)
    print("✓ 'spritesheet.webp' creado. Cabeza protegida y tiempos de Wall-E aplicados.")

if __name__ == "__main__":
    main()
