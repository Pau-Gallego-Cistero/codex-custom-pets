
import os
import json
import numpy as np
from PIL import Image

def limpiar_fondo_blanco(img_path, umbral=235):
    """Elimina el fondo blanco y recorta el sprite a su silueta exacta."""
    img = Image.open(img_path).convert("RGBA")
    arr = np.array(img, dtype=np.uint8)
    es_blanco = (
        (arr[:, :, 0] >= umbral)
        & (arr[:, :, 1] >= umbral)
        & (arr[:, :, 2] >= umbral)
    )
    arr[es_blanco, 3] = 0
    img_clean = Image.fromarray(arr)

    bbox = img_clean.getbbox()
    if bbox:
        img_clean = img_clean.crop(bbox)
    return img_clean

def ajustar_a_suelo(img, cell_w=192, cell_h=208, max_h=106, offset_x=0):
    """
    Escala el sprite (reducido ~18% respecto a la versión anterior) y permite
    aplicar desplazamiento horizontal para dar sensación de avance.
    """
    ratio = max_h / float(img.height)
    new_w = int(img.width * ratio)
    new_h = int(img.height * ratio)

    if new_w > cell_w - 20:
        ratio_w = (cell_w - 20) / float(new_w)
        new_w = int(new_w * ratio_w)
        new_h = int(new_h * ratio_w)

    img_scaled = img.resize((new_w, new_h), Image.Resampling.NEAREST)

    celda = Image.new("RGBA", (cell_w, cell_h), (0, 0, 0, 0))
    pos_x = ((cell_w - new_w) // 2) + offset_x
    pos_y = cell_h - new_h - 6
    celda.paste(img_scaled, (pos_x, pos_y), img_scaled)
    return celda

def main():
    file_idle = "stegosapo.jpg"
    file_jump = "stegosapo_jump.jpg"

    if not os.path.exists(file_idle) or not os.path.exists(file_jump):
        print(f"Error: Faltan '{file_idle}' y '{file_jump}' en la carpeta.")
        return

    print("1. Limpiando fondos y aplicando reducción de tamaño (~18%)...")
    img_idle = limpiar_fondo_blanco(file_idle)
    img_jump = limpiar_fondo_blanco(file_jump)

    # Frame de respiración para que el sapo tenga vida en el suelo
    w_i, h_i = img_idle.size
    img_idle_breathe = img_idle.resize((w_i + 2, h_i - 2), Image.Resampling.NEAREST)

    CELL_W, CELL_H = 192, 208
    COLS, ROWS = 8, 11
    TOTAL_W = CELL_W * COLS
    TOTAL_H = CELL_H * ROWS
    SCALE_MAX_H = 106

    # --- CUADROS CON DESPLAZAMIENTO Y RESPIRACIÓN (DERECHA) ---

    idle_r1 = ajustar_a_suelo(
        img_idle, CELL_W, CELL_H,
        max_h=SCALE_MAX_H, offset_x=-10
    )

    idle_r2 = ajustar_a_suelo(
        img_idle_breathe, CELL_W, CELL_H,
        max_h=SCALE_MAX_H, offset_x=-10
    )

    # En el aire: salto de 4 frames avanzando hacia adelante
    jump_r_f1 = ajustar_a_suelo(
        img_jump, CELL_W, CELL_H,
        max_h=SCALE_MAX_H, offset_x=-4
    )

    jump_r_f2 = ajustar_a_suelo(
        img_jump, CELL_W, CELL_H,
        max_h=SCALE_MAX_H, offset_x=+2
    )

    jump_r_f3 = ajustar_a_suelo(
        img_jump, CELL_W, CELL_H,
        max_h=SCALE_MAX_H, offset_x=+8
    )

    jump_r_f4 = ajustar_a_suelo(
        img_jump, CELL_W, CELL_H,
        max_h=SCALE_MAX_H, offset_x=+14
    )

    # --- VERSIONES ESPEJADAS (IZQUIERDA) ---

    idle_l1 = idle_r1.transpose(Image.FLIP_LEFT_RIGHT)
    idle_l2 = idle_r2.transpose(Image.FLIP_LEFT_RIGHT)

    jump_l_f1 = jump_r_f1.transpose(Image.FLIP_LEFT_RIGHT)
    jump_l_f2 = jump_r_f2.transpose(Image.FLIP_LEFT_RIGHT)
    jump_l_f3 = jump_r_f3.transpose(Image.FLIP_LEFT_RIGHT)
    jump_l_f4 = jump_r_f4.transpose(Image.FLIP_LEFT_RIGHT)

    # --- COMPOSICIÓN DE FILAS ---

    # Animación normal de movimiento SIN salto
    fila_movimiento_normal_r = [
        idle_r1, idle_r2, idle_r1, idle_r2,
        idle_r1, idle_r2, idle_r1, idle_r2
    ]

    fila_movimiento_normal_l = [
        idle_l1, idle_l2, idle_l1, idle_l2,
        idle_l1, idle_l2, idle_l1, idle_l2
    ]

    # ÚNICA fila que contiene el salto.
    # Conserva EXACTAMENTE los 4 frames originales:
    # jump_f1 → jump_f2 → jump_f3 → jump_f4
    fila_movimiento_r = [
        idle_r1, idle_r2, idle_r1, idle_r2,
        jump_r_f1, jump_r_f2, jump_r_f3, jump_r_f4
    ]

    fila_movimiento_l = [
        idle_l1, idle_l2, idle_l1, idle_l2,
        jump_l_f1, jump_l_f2, jump_l_f3, jump_l_f4
    ]

    # Idle (reposo vivo)
    fila_idle_r = [
        idle_r1, idle_r2, idle_r1, idle_r2,
        idle_r1, idle_r2, idle_r1, idle_r2
    ]

    fila_idle_l = [
        idle_l1, idle_l2, idle_l1, idle_l2,
        idle_l1, idle_l2, idle_l1, idle_l2
    ]

    # --- ASIGNACIÓN A LAS 11 FILAS ---
    #
    # El salto aparece SOLO en la fila 1.
    # Las demás filas NO contienen los frames de salto.

    mapa_filas = [
        fila_idle_r,             # 0: Idle
        fila_movimiento_r,       # 1: Walk right → ÚNICO SALTO
        fila_movimiento_normal_l,# 2: Walk left
        fila_movimiento_normal_r,# 3: Run right
        fila_movimiento_normal_l,# 4: Run left
        fila_movimiento_normal_r,# 5: Jump right
        fila_movimiento_normal_l,# 6: Jump left
        fila_idle_r,             # 7: Waiting
        fila_idle_l,             # 8: Review
        fila_idle_r,             # 9: Look right
        fila_idle_l              # 10: Look left
    ]

    print(f"2. Guardando spritesheet ajustado de {TOTAL_W}x{TOTAL_H} px...")
    spritesheet = Image.new(
        "RGBA",
        (TOTAL_W, TOTAL_H),
        (0, 0, 0, 0)
    )

    for row_idx, fila in enumerate(mapa_filas):
        for col_idx in range(COLS):
            frame = fila[col_idx]
            spritesheet.paste(
                frame,
                (col_idx * CELL_W, row_idx * CELL_H),
                frame
            )

    spritesheet.save(
        "spritesheet.webp",
        format="WEBP",
        lossless=True
    )

    print(
        "✓ 'spritesheet.webp' generado: tamaño reducido ~18%, "
        "respiración activa y un único salto de 4 frames en toda la cuadrícula."
    )

    manifest = {
        "id": "stegosapo",
        "displayName": "Stegosapo",
        "description": "Stegosapo escalado y animado para Codex Pet",
        "spriteVersionNumber": 2,
        "spritesheetPath": "spritesheet.webp"
    }

    with open("pet.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print("✓ 'pet.json' actualizado.")

if __name__ == "__main__":
    main()
