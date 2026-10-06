"""Experimento 3D->2D: pose via solvePnP e projecao de pontos 3D conhecidos.

Usa o tabuleiro 7x7 (quadrado 50mm) como referencial 3D: estima a pose
da camera, reprojeta os cantos (conferencia) e desenha um cubo virtual
de aresta 100mm sobre o tabuleiro.
"""
import argparse
import os

import cv2
import numpy as np

LADO = 50.0  # mm
NX, NY = 7, 7


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--foto", required=True, help="imagem com o tabuleiro parado")
    ap.add_argument("--npz", default="imgs/semaforo/calibracao.npz")
    ap.add_argument("--saida", default="imgs/experimento")
    args = ap.parse_args()
    os.makedirs(args.saida, exist_ok=True)
    cal = np.load(args.npz)
    K, dist = cal["K"], cal["dist"]

    img = cv2.imread(args.foto)
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    flags = cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE
    ok, cantos = cv2.findChessboardCorners(g, (NX, NY), flags=flags)
    if not ok:
        raise SystemExit("tabuleiro 7x7 nao detectado na foto")
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    cv2.cornerSubPix(g, cantos, (11, 11), (-1, -1), crit)

    objp = np.zeros((NX * NY, 3), np.float32)
    objp[:, :2] = np.mgrid[0:NX, 0:NY].T.reshape(-1, 2) * LADO
    ok, rvec, tvec = cv2.solvePnP(objp, cantos, K, dist)
    print("tvec (mm) =", tvec.ravel().round(1))

    # conferencia: reprojeta os 49 cantos 3D e compara com os detectados
    proj, _ = cv2.projectPoints(objp, rvec, tvec, K, dist)
    err = cv2.norm(cantos, proj, cv2.NORM_L2) / len(objp) ** 0.5
    print(f"49 cantos reprojetados: RMSE = {err:.3f} px")

    # cubo virtual: base no tabuleiro (cantos 1..3), altura 100mm
    a = 2 * LADO
    cubo = np.float32([[0, 0, 0], [a, 0, 0], [a, a, 0], [0, a, 0],
                       [0, 0, -a], [a, 0, -a], [a, a, -a], [0, a, -a]])
    pc, _ = cv2.projectPoints(cubo, rvec, tvec, K, dist)
    pc = pc.reshape(-1, 2).astype(int)
    vis = img.copy()
    cv2.drawChessboardCorners(vis, (NX, NY), proj, True)  # reprojecao: verde
    for i, j in [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7),
                 (7, 4), (0, 4), (1, 5), (2, 6), (3, 7)]:
        cv2.line(vis, tuple(pc[i]), tuple(pc[j]), (255, 0, 0), 3)
    base = os.path.splitext(os.path.basename(args.foto))[0]
    out = os.path.join(args.saida, base + "_cubo.jpg")
    cv2.imwrite(out, vis)
    print("overlay:", out)


if __name__ == "__main__":
    raise SystemExit(main())
