import cv2, numpy as np, base64, os

def _largest_fg(alpha):
    """keep only the largest connected foreground blob; fill interior holes."""
    fg = (alpha > 127).astype(np.uint8)
    n, lbl, stats, _ = cv2.connectedComponentsWithStats(fg, 8)
    if n <= 1:
        return alpha
    # label 0 is background; pick largest among 1..n-1
    big = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    keep = (lbl == big).astype(np.uint8) * 255
    # fill holes: flood background from border on the inverted mask
    inv = (keep == 0).astype(np.uint8)
    ff = inv.copy()
    h, w = ff.shape
    m = np.zeros((h + 2, w + 2), np.uint8)
    cv2.floodFill(ff, m, (0, 0), 0)  # border-connected bg -> 0
    holes = ((inv == 1) & (ff == 1)).astype(np.uint8)  # enclosed holes
    keep[holes == 1] = 255
    return keep

def cutout_rgba(path, maxdim=500, tol=13):
    """Return (rgba ndarray HxWx4, fg_fraction). Transparent where background."""
    raw = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if raw is None:
        return None, 0.0
    # already has usable alpha?
    if raw.ndim == 3 and raw.shape[2] == 4 and raw[:, :, 3].min() < 240:
        bgr = raw[:, :, :3]; alpha = raw[:, :, 3]
    else:
        bgr = raw[:, :, :3] if raw.ndim == 3 else cv2.cvtColor(raw, cv2.COLOR_GRAY2BGR)
        bgr = np.ascontiguousarray(bgr)
        h, w = bgr.shape[:2]
        mask = np.zeros((h + 2, w + 2), np.uint8)
        flags = 4 | (255 << 8) | cv2.FLOODFILL_MASK_ONLY  # floating range
        seeds = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1),
                 (w // 2, 0), (w // 2, h - 1), (2, h // 2), (w - 3, h // 2),
                 (3, 3), (w - 4, 3), (3, h - 4), (w - 4, h - 4)]
        for (x, y) in seeds:
            cv2.floodFill(bgr, mask, (x, y), 255, (tol, tol, tol), (tol, tol, tol), flags)
        bg = mask[1:-1, 1:-1]
        alpha = np.where(bg > 0, 0, 255).astype(np.uint8)
        alpha = cv2.morphologyEx(alpha, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        alpha = cv2.morphologyEx(alpha, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
        alpha = _largest_fg(alpha)

    frac = float((alpha > 127).mean())
    # if removal clearly failed (almost everything kept), signal caller
    # crop to content
    ys, xs = np.where(alpha > 10)
    if len(xs) == 0:
        return None, 0.0
    pad = 10
    y0, y1 = max(0, ys.min() - pad), min(alpha.shape[0], ys.max() + pad + 1)
    x0, x1 = max(0, xs.min() - pad), min(alpha.shape[1], xs.max() + pad + 1)
    bgr = np.ascontiguousarray(bgr[y0:y1, x0:x1]); alpha = np.ascontiguousarray(alpha[y0:y1, x0:x1])
    # soften edge: erode 1px then slight blur to kill white halo
    alpha = cv2.erode(alpha, np.ones((2, 2), np.uint8), iterations=1)
    alpha = cv2.GaussianBlur(alpha, (3, 3), 0)
    # resize
    h, w = alpha.shape
    s = maxdim / max(h, w)
    if s < 1:
        bgr = cv2.resize(bgr, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
        alpha = cv2.resize(alpha, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    rgba = np.dstack([rgb, alpha])
    return rgba, frac

def to_data_uri(path, maxdim=500, tol=13):
    rgba, frac = cutout_rgba(path, maxdim, tol)
    if rgba is None:
        return None, 0.0
    from PIL import Image
    im = Image.fromarray(rgba, "RGBA")
    import io
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode(), frac

if __name__ == "__main__":
    import sys
    GUNS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "guns"))
    for key in sys.argv[1:]:
        for ext in (".jpg", ".png"):
            p = os.path.join(GUNS, key + ext)
            if os.path.exists(p):
                rgba, frac = cutout_rgba(p)
                if rgba is not None:
                    from PIL import Image
                    Image.fromarray(rgba, "RGBA").save(os.path.join(GUNS, "test_" + key + ".png"))
                    print(f"{key}: fg={frac:.2f} size={rgba.shape[1]}x{rgba.shape[0]}")
                break
