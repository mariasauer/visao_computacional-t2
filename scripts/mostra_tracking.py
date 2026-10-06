"""Figura do tracking: cantos detectados x reprojetados em cada foto do semaforo."""
import glob
import os

import cv2
import numpy as np

DIR = "imgs/semaforo"
NX, NY = 7, 7
LADO = 50.0

cal = np.load(os.path.join(DIR, "calibracao.npz"))
K, dist = cal["K"], cal["dist"]
usadas = list(cal["usadas"])
rvecs, tvecs = cal["rvecs"], cal["tvecs"]

objp = np.zeros((NX * NY, 3), np.float32)
objp[:, :2] = np.mgrid[0:NX, 0:NY].T.reshape(-1, 2) * LADO
crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
flags = cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE

minis = []
for fn in sorted(glob.glob(os.path.join(DIR, "sem*.jpg"))):
    base = os.path.basename(fn)
    img = cv2.imread(fn)
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ok, cantos = cv2.findChessboardCorners(g, (NX, NY), flags=flags)
    if ok and base in usadas:
        cv2.cornerSubPix(g, cantos, (11, 11), (-1, -1), crit)
        i = usadas.index(base)
        proj, _ = cv2.projectPoints(objp, rvecs[i], tvecs[i], K, dist)
        rmse = cv2.norm(cantos, proj, cv2.NORM_L2) / len(objp) ** 0.5
        cv2.drawChessboardCorners(img, (NX, NY), cantos, True)
        for p in proj.reshape(-1, 2).astype(int):
            cv2.circle(img, tuple(p), 4, (0, 0, 255), -1)
        msg, cor = f"{base} err={rmse:.2f}px", (0, 255, 0)
        print(f"{base}: RMSE={rmse:.3f} px")
    else:
        if ok:
            cv2.drawChessboardCorners(img, (NX, NY), cantos, True)
            msg, cor = f"{base} EXCLUIDA (outlier)", (255, 165, 0)
        else:
            msg, cor = f"{base} SEM TRACKING", (0, 0, 255)
        print(f"{base}: {msg}")
    cv2.putText(img, msg, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, cor, 2)
    minis.append(cv2.resize(img, (426, 240)))

cols = 5
linhas = [minis[i:i + cols] for i in range(0, len(minis), cols)]
grade = np.vstack([np.hstack(l) for l in linhas])
out = os.path.join(DIR, "tracking.jpg")
cv2.imwrite(out, grade)
print("grade:", out)
