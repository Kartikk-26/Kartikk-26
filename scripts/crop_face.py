"""
Crop a photo to a head-and-shoulders square -- run this BEFORE prep_photo.py if
your source is a full-body or wide shot.

The ascii art samples into a 100x53 character grid (~800x795 of canvas), so the
source wants to be roughly square with the head large in frame. Feed it a
full-body photo and the face lands in ~15 characters and reads as mush.

Head position comes from rembg's person mask rather than a Haar cascade: OpenCV 5
dropped CascadeClassifier, and the mask also copes with side profiles and partly
occluded faces (a cap, a phone) that a frontal cascade misses.

    python scripts/crop_face.py <input.jpg> source-photo.jpg
"""
import sys

import cv2
import numpy as np
from PIL import Image
from rembg import remove

INP = sys.argv[1]
OUT = sys.argv[2] if len(sys.argv) > 2 else "source-photo.jpg"

img = Image.open(INP).convert("RGB")
w, h = img.size

cut = remove(img.convert("RGBA"))
alpha = np.array(cut.split()[-1])
ys, xs = np.where(alpha > 40)
if len(ys) == 0:
    raise SystemExit("no subject found in the mask -- crop by hand")

top = ys.min()
subj_h = ys.max() - top

# the head is in the top slice of the subject; take that slice's horizontal
# centre of mass so we centre on the head, not on an outstretched arm
head_band = alpha[top:top + max(1, int(subj_h * 0.18))]
band_xs = np.where(head_band > 40)[1]
head_cx = int(band_xs.mean()) if len(band_xs) else (xs.min() + xs.max()) // 2

head_w = max(1, band_xs.max() - band_xs.min()) if len(band_xs) else subj_h // 5
side = int(np.clip(head_w * 2.6, subj_h * 0.30, min(h, w)))

x0 = int(np.clip(head_cx - side / 2, 0, w - side))
y0 = int(np.clip(top - side * 0.10, 0, max(0, h - side)))

crop = np.array(img)[y0:y0 + side, x0:x0 + side]
crop = cv2.resize(crop, (900, 900), interpolation=cv2.INTER_LANCZOS4)
Image.fromarray(crop).save(OUT, quality=95)
print(f"subject top={top} head_cx={head_cx} head_w={head_w} -> {side}px square "
      f"@({x0},{y0}); wrote {OUT}")
