"""GIF AR: cubo virtual fixo no tabuleiro, rastreado por solvePnP quadro a quadro.

Sem deteccao num quadro -> reusa a ultima pose boa.
Monta o GIF com ffmpeg (paleta) em 640x360.
"""
import argparse
import glob
import os
import subprocess

import cv2
import numpy as np

LADO = 50.0
NX, NY = 7, 7
A = 2 * LADO  # aresta do cubo: 100mm
CUBO = np.float32([[0, 0, 0], [A, 0, 0], [A, A, 0], [0, A, 0],
                   [0, 0, -A], [A, 0, -A], [A, A, -A], [0, A, -A]])
ARESTAS = [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7),
           (7, 4), (0, 4), (1, 5), (2, 6), (3, 7)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--npz", default="imgs/semaforo/calibracao.npz")
    ap.add_argument("--saida", default="imgs/cubo.gif")
    ap.add_argument("--fps", type=int, default=10)
    args = ap.parse_args()
    cal = np.load(args.npz)
    K, dist = cal["K"], cal["dist"]

    objp = np.zeros((NX * NY, 3), np.float32)
    objp[:, :2] = np.mgrid[0:NX, 0:NY].T.reshape(-1, 2) * LADO
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    flags = cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE

    cap = cv2.VideoCapture(args.video)
    vfps = cap.get(cv2.CAP_PROP_FPS) or 30
    passo = max(1, round(vfps / args.fps))
    tmp = os.path.join(os.path.dirname(args.saida), "_gif_frames")
    os.makedirs(tmp, exist_ok=True)
    for f in glob.glob(os.path.join(tmp, "*.png")):
        os.remove(f)

    rvec = tvec = None
    n_ok = n_total = i = 0
    while True:
        ok, img = cap.read()
        if not ok:
            break
        if i % passo:
            i += 1
            continue
        i += 1
        g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        achou, cantos = cv2.findChessboardCorners(g, (NX, NY), flags=flags)
        if achou:
            cv2.cornerSubPix(g, cantos, (11, 11), (-1, -1), crit)
            _, rvec, tvec = cv2.solvePnP(objp, cantos, K, dist)
            n_ok += 1
        n_total += 1
        if rvec is not None:
            pc, _ = cv2.projectPoints(CUBO, rvec, tvec, K, dist)
            pc = pc.reshape(-1, 2).astype(int)
            for a, b in ARESTAS:
                cv2.line(img, tuple(pc[a]), tuple(pc[b]), (255, 0, 0), 4)
            cv2.putText(img, "cubo 100mm", tuple(pc[4] + [10, -10]),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 0, 0), 2)
        img = cv2.resize(img, (640, 360))
        cv2.imwrite(os.path.join(tmp, f"f{n_total:03d}.png"), img)
    cap.release()
    print(f"poses ok: {n_ok}/{n_total}")

    pal = os.path.join(tmp, "pal.png")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(args.fps),
                    "-i", os.path.join(tmp, "f%03d.png"),
                    "-vf", "palettegen", pal], check=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(args.fps),
                    "-i", os.path.join(tmp, "f%03d.png"), "-i", pal,
                    "-lavfi", "paletteuse", args.saida], check=True)
    print("gif:", args.saida, os.path.getsize(args.saida) // 1024, "KB")


if __name__ == "__main__":
    raise SystemExit(main())
