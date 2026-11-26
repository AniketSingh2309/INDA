import os, sys, math, numpy as np, cv2
GUNS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "guns"))
FINAL = os.path.join(GUNS, "_final")
keys = sys.argv[1:]
cell = 290; cols = 5
rows = math.ceil(len(keys)/cols)
canvas = np.full((rows*cell, cols*cell, 3), 26, np.uint8)
for i,key in enumerate(keys):
    r,c = divmod(i, cols); y0,x0 = r*cell, c*cell
    tile = np.full((cell,cell,3), 20, np.uint8)
    p = os.path.join(FINAL, key+".png")
    if os.path.exists(p):
        rgba = cv2.imread(p, cv2.IMREAD_UNCHANGED)
        if rgba is not None and rgba.ndim==3 and rgba.shape[2]==4:
            h,w = rgba.shape[:2]; s=min((cell-56)/w,(cell-56)/h,1.0)
            if s<1: rgba=cv2.resize(rgba,(int(w*s),int(h*s)),interpolation=cv2.INTER_AREA)
            h,w=rgba.shape[:2]; yo,xo=(cell-h)//2,(cell-w)//2
            a=rgba[:,:,3:4].astype(float)/255; bgr=rgba[:,:,:3].astype(float)
            reg=tile[yo:yo+h,xo:xo+w].astype(float)
            tile[yo:yo+h,xo:xo+w]=(bgr*a+reg*(1-a)).astype(np.uint8)
            cv2.putText(tile,key,(8,cell-12),cv2.FONT_HERSHEY_SIMPLEX,0.5,(90,200,255),1,cv2.LINE_AA)
        else:
            cv2.putText(tile,key+" ?",(8,cell-12),cv2.FONT_HERSHEY_SIMPLEX,0.5,(80,80,230),1,cv2.LINE_AA)
    else:
        cv2.putText(tile,key+" MISSING",(8,cell-12),cv2.FONT_HERSHEY_SIMPLEX,0.5,(80,80,230),1,cv2.LINE_AA)
    canvas[y0:y0+cell,x0:x0+cell]=tile
out=os.path.join(GUNS,"_montage_final.png"); cv2.imwrite(out,canvas); print(out,canvas.shape)
