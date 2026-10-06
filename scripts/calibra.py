"""Calibracao da camera a partir das fotos do semaforo (7x7 cantos)."""
import argparse
import glob
import os

import cv2
import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="imgs/semaforo")
    ap.add_argument("--padrao", default="7x7")
    ap.add_argument("--lado", type=float, default=1.0,
                    help="lado do quadrado (unidade real quando souber os mm)")
    ap.add_argument("--saida", default="imgs/semaforo/calibracao.npz")
    ap.add_argument("--excluir", default="",
                    help="basenames separados por virgula a ignorar")
    args = ap.parse_args()
    nx, ny = (int(v) for v in args.padrao.split("x"))

    objp = np.zeros((nx * ny, 3), np.float32)
    objp[:, :2] = np.mgrid[0:nx, 0:ny].T.reshape(-1, 2) * args.lado
    criterios = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    obj, imgp, formas = [], [], None
    usadas = []
    fora = {e.strip() for e in args.excluir.split(",") if e.strip()}
    for fn in sorted(glob.glob(os.path.join(args.dir, "sem*.jpg"))):
        if os.path.basename(fn) in fora:
            continue
        g = cv2.imread(fn, cv2.IMREAD_GRAYSCALE)
        formas = g.shape[::-1]
        flags = cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE
        ok, cantos = cv2.findChessboardCorners(g, (nx, ny), flags=flags)
        if ok:
            cv2.cornerSubPix(g, cantos, (11, 11), (-1, -1), criterios)
            obj.append(objp)
            imgp.append(cantos)
            usadas.append(os.path.basename(fn))
    print(f"{len(usadas)}/{len(glob.glob(os.path.join(args.dir, 'sem*.jpg')))} usadas")

    ret, K, dist, rvecs, tvecs = cv2.calibrateCamera(obj, imgp, formas, None, None)
    # erro medio de reprojecao
    err, n = 0.0, 0
    for o, ip, r, t in zip(obj, imgp, rvecs, tvecs):
        proj, _ = cv2.projectPoints(o, r, t, K, dist)
        err += cv2.norm(ip, proj, cv2.NORM_L2) ** 2
        n += len(o)
    rmse = (err / n) ** 0.5
    print("K =\n", K)
    print("dist =", dist.ravel())
    print(f"rmse reprojecao = {rmse:.3f} px")
    np.savez(args.saida, K=K, dist=dist, rvecs=np.array(rvecs),
             tvecs=np.array(tvecs), usadas=np.array(usadas),
             rmse=rmse, lado=args.lado)
    print("salvo:", args.saida)

    # exemplo de undistort na primeira usada
    img = cv2.imread(os.path.join(args.dir, usadas[0]))
    h, w = img.shape[:2]
    nK, _ = cv2.getOptimalNewCameraMatrix(K, dist, (w, h), 1, (w, h))
    cv2.imwrite(os.path.join(args.dir, "undistort_exemplo.jpg"),
                cv2.undistort(img, K, dist, None, nK))
    print("exemplo undistort salvo")


if __name__ == "__main__":
    raise SystemExit(main())
