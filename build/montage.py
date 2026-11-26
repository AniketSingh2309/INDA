import os, sys, math, numpy as np, cv2
from bgremove import cutout_rgba
GUNS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "guns"))
keys = sys.argv[1:]
cell = 300
cols = 4
rows = math.ceil(len(keys)/cols)
# dark stage bg with label strip
canvas = np.full((rows*cell, cols*cell, 3), 28, np.uint8)
for i,key in enumerate(keys):
    r,c = divmod(i, cols)
    y0,x0 = r*cell, c*cell
    tile = np.full((cell,cell,3), 22, np.uint8)
    path=None
    for ext in (".jpg",".png"):
        p=os.path.join(GUNS,key+ext)
        if os.path.exists(p): path=p; break
    if path:
        rgba,frac = cutout_rgba(path, maxdim=cell-60)
        if rgba is not None:
            h,w = rgba.shape[:2]
            yo,xo = (cell-h)//2, (cell-w)//2
            if yo<0 or xo<0:
                rgba=rgba[:cell,:cell]; h,w=rgba.shape[:2]; yo,xo=max(0,(cell-h)//2),max(0,(cell-w)//2)
            a = rgba[:,:,3:4].astype(float)/255
            rgb = cv2.cvtColor(rgba[:,:,:3], cv2.COLOR_RGB2BGR).astype(float)
            region = tile[yo:yo+h, xo:xo+w].astype(float)
            tile[yo:yo+h, xo:xo+w] = (rgb*a + region*(1-a)).astype(np.uint8)
            cv2.putText(tile, f"{key} {frac:.2f}", (8,cell-12), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (90,200,255), 1, cv2.LINE_AA)
        else:
            cv2.putText(tile, f"{key} FAIL", (8,cell-12), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (80,80,230), 1, cv2.LINE_AA)
    else:
        cv2.putText(tile, f"{key} MISSING", (8,cell-12), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (80,80,230), 1, cv2.LINE_AA)
    canvas[y0:y0+cell, x0:x0+cell] = tile
out=os.path.join(GUNS,"_montage.png")
cv2.imwrite(out, canvas)
print(out, canvas.shape)
