import os
from PIL import Image
import numpy as np

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_IMG = os.path.join(RAIZ, "Oblivium", "assets", "npc", "cavaleiro spritesheet.webp")
DEST_DIR = os.path.join(RAIZ, "Oblivium", "assets", "npc", "guarda_doran")

os.makedirs(os.path.join(DEST_DIR, "idle"), exist_ok=True)
os.makedirs(os.path.join(DEST_DIR, "walk"), exist_ok=True)
os.makedirs(os.path.join(DEST_DIR, "dialogue"), exist_ok=True)

im = Image.open(SRC_IMG).convert("RGBA")
arr = np.array(im)
bg_color = np.array([162, 162, 162])

def process_frame(bbox):
    # bbox = (x, y, w, h)
    x, y, w, h = bbox
    crop = arr[y:y+h, x:x+w].copy()
    diff = np.sqrt(np.sum((crop[:, :, :3].astype(float) - bg_color)**2, axis=2))
    
    # Transparency mask
    alpha = np.ones((h, w), dtype=np.uint8) * 255
    alpha[diff < 15] = 0
    # Soft edge
    blend = (diff >= 15) & (diff < 30)
    alpha[blend] = ((diff[blend] - 15) / 15.0 * 255).astype(np.uint8)
    crop[:, :, 3] = alpha
    
    # Trim empty margins inside crop
    non_zero = np.where(crop[:, :, 3] > 10)
    if len(non_zero[0]) > 0:
        y_min, y_max = non_zero[0].min(), non_zero[0].max() + 1
        x_min, x_max = non_zero[1].min(), non_zero[1].max() + 1
        trimmed = crop[y_min:y_max, x_min:x_max]
    else:
        trimmed = crop
    
    return Image.fromarray(trimmed)

# Idle boxes (Row 0: 4 frames)
idle_boxes = [
    (387, 47, 74, 110),
    (501, 47, 75, 110),
    (616, 47, 74, 110),
    (730, 47, 74, 110)
]

for i, box in enumerate(idle_boxes, 1):
    f_img = process_frame(box)
    out_path = os.path.join(DEST_DIR, "idle", f"guarda_doran_idle_{i:02d}.png")
    f_img.save(out_path)
    print("Salvo:", out_path, f_img.size)

# Walk boxes (Row 1: 8 frames)
walk_boxes = [
    (387, 173, 69, 110),
    (500, 175, 74, 108),
    (617, 175, 83, 108),
    (744, 173, 72, 110),
    (877, 175, 79, 109),
    (966, 175, 75, 109),
    (1075, 173, 74, 110),
    (1192, 173, 76, 110)
]

for i, box in enumerate(walk_boxes, 1):
    f_img = process_frame(box)
    out_path = os.path.join(DEST_DIR, "walk", f"guarda_doran_walk_{i:02d}.png")
    f_img.save(out_path)
    print("Salvo:", out_path, f_img.size)

# Dialogue boxes (Row 4: 5 frames)
dialogue_boxes = [
    (387, 683, 74, 110),
    (500, 683, 101, 110),
    (674, 683, 76, 110),
    (809, 683, 57, 110),
    (925, 685, 77, 108)
]

for i, box in enumerate(dialogue_boxes, 1):
    f_img = process_frame(box)
    out_path = os.path.join(DEST_DIR, "dialogue", f"guarda_doran_dialogue_{i:02d}.png")
    f_img.save(out_path)
    print("Salvo:", out_path, f_img.size)

print("Recorte concluído com sucesso!")
