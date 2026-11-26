import os
# weapon imgkey -> best REAL photo (with background), path relative to guns/
GUNS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "guns"))
PHOTO = {
 "insas":      "insas.jpg",
 "excalibur":  "insas.jpg",
 "ak203":      "cand/ak203__0.jpg",      # real Indian Army AK-203
 "sig716":     "cand/sig716__2.jpg",     # SIG rifle
 "tavor":      "tavor.jpg",
 "akm":        "akm.jpg",
 "m4":         "m4.jpg",
 "jvpc":       "jvpc.png",
 "msmc":       "msmc.png",
 "asmi":       "asmi.jpg",
 "mp5":        "mp5.jpg",
 "svd":        "svd.jpg",
 "sako":       "cand/sako__0.jpg",       # Sako TRG-42
 "galil":      "galil.png",
 "vidhwansak": "vidhwansak.jpg",
 "m82":        "m82.jpg",                # Barrett
 "negev":      "cand/negev__0.jpg",      # white studio Negev
 "pkm":        "pkm.jpg",
 "auto9mm":    "cand/auto9mm__3.jpg",    # Pistol Auto 9mm 1A (Kolkata)
 "glock":      "cand/glock__0.jpg",      # full Glock pistol
 "carlg":      "carlg.png",
 "rpg7":       "rpg7.jpg",
 "milan":      "cand/milan__1.jpg",      # Euromissile Milan
}
def photo_path(key):
    rel = PHOTO.get(key)
    if not rel: return None
    p = os.path.join(GUNS, rel)
    return p if os.path.exists(p) else None
