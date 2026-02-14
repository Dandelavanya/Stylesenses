"""Skin tone detection from face region using OpenCV and NumPy."""
import cv2
import numpy as np
from pathlib import Path

from config import SKIN_TONES

# Approximate RGB ranges for skin tone categories (typical face region averages)
# Fair: light skin, Medium: mid, Olive: warm/green undertone, Deep: darker
FAIR_RANGE = (180, 220)      # R high
MEDIUM_RANGE = (140, 200)    # R mid
OLIVE_RANGE = (120, 170)     # R lower, G closer to R
DEEP_RANGE = (80, 140)       # R low

def _get_face_roi(gray, img_bgr):
    """Get first detected face region. Returns (x, y, w, h) or None."""
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(cascade_path)
    faces = face_cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
    )
    if len(faces) == 0:
        return None
    # Use largest face
    areas = [w * h for (_, _, w, h) in faces]
    i = int(np.argmax(areas))
    return faces[i]

def _expand_roi(x, y, w, h, img_shape, margin_ratio=0.2):
    """Expand ROI with margin, clamp to image."""
    H, W = img_shape[:2]
    mw = int(w * margin_ratio)
    mh = int(h * margin_ratio)
    x1 = max(0, x - mw)
    y1 = max(0, y - mh)
    x2 = min(W, x + w + mw)
    y2 = min(H, y + h + mh)
    return x1, y1, x2, y2

def _classify_skin_tone(r: float, g: float, b: float) -> str:
    """Map average RGB to Fair, Medium, Olive, or Deep."""
    # Use luminance and R dominance; simple thresholds
    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    if luminance >= 180 and r >= 170:
        return "Fair"
    if luminance >= 140:
        if g >= r * 0.92 and g <= r * 1.08:
            return "Olive"
        return "Medium"
    return "Deep"

def detect_skin_tone(image_path: str) -> dict:
    """
    Detect skin tone from face in image.
    Returns dict with keys: skin_tone, rgb, r, g, b, face_detected, message.
    """
    path = Path(image_path)
    if not path.is_file():
        return {
            "skin_tone": "Medium",
            "rgb": [150, 120, 100],
            "r": 150, "g": 120, "b": 100,
            "face_detected": False,
            "message": "Image file not found.",
        }
    img = cv2.imread(str(path))
    if img is None:
        return {
            "skin_tone": "Medium",
            "rgb": [150, 120, 100],
            "r": 150, "g": 120, "b": 100,
            "face_detected": False,
            "message": "Could not read image.",
        }
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    face_rect = _get_face_roi(gray, img)
    if face_rect is None:
        # No face: use center crop as fallback (often face is in center)
        h, w = img.shape[:2]
        x1, y1 = w // 4, h // 4
        x2, y2 = 3 * w // 4, 3 * h // 4
        roi = img[y1:y2, x1:x2]
        message = "No face detected; used center region for color."
    else:
        x, y, fw, fh = face_rect
        x1, y1, x2, y2 = _expand_roi(x, y, fw, fh, img.shape)
        roi = img[y1:y2, x1:x2]
        message = "Face detected; skin tone from face region."
    if roi.size == 0:
        return {
            "skin_tone": "Medium",
            "rgb": [150, 120, 100],
            "r": 150, "g": 120, "b": 100,
            "face_detected": False,
            "message": "Could not extract region.",
        }
    # BGR to RGB, then average
    roi_rgb = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)
    r = float(np.mean(roi_rgb[:, :, 0]))
    g = float(np.mean(roi_rgb[:, :, 1]))
    b = float(np.mean(roi_rgb[:, :, 2]))
    r, g, b = round(r, 1), round(g, 1), round(b, 1)
    skin_tone = _classify_skin_tone(r, g, b)
    return {
        "skin_tone": skin_tone,
        "rgb": [int(r), int(g), int(b)],
        "r": r, "g": g, "b": b,
        "face_detected": face_rect is not None,
        "message": message,
    }
