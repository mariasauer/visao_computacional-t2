"""Valida detecção de cantos do tabuleiro nas fotos de calibração."""
import argparse
import glob
import os
import sys

import cv2
import numpy as np


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, help="pasta com img*.jpg")
    ap.add_argument("--padrao", default="7x7", help="cantos internos, ex. 7x7")
    ap.add_argument("--saida", default="",
                    help="grade de contato anotada (jpg). '' = <dir>/contato.jpg")
    args = ap.parse_args()
    nx, ny = (int(v) for v in args.padrao.split("x"))
    padrao = (nx, ny)

    fns = sorted(glob.glob(os.path.join(args.dir, "img*.jpg")))
    if not fns:
        print("nenhuma imagem encontrada", file=sys.stderr)
        return 1

    boas, miniaturas = [], []
    for fn in fns:
        img = cv2.imread(fn, cv2.IMREAD_GRAYSCALE)
        ok, cantos = cv2.findChessboardCorners(img, padrao)
        base = os.path.basename(fn)
        if ok:
            boas.append(base)
            mini = cv2.drawChessboardCorners(
                cv2.cvtColor(img, cv2.COLOR_GRAY2BGR), padrao, cantos, ok)
            tag = "OK"
        else:
            mini = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            tag = "FALHOU"
        cv2.putText(mini, f"{base} {tag}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                    (0, 255, 0) if ok else (0, 0, 255), 2)
        miniaturas.append(cv2.resize(mini, (426, 240)))
        print(f"{base}: {'OK' if ok else 'FALHOU'}")

    print(f"\n{len(boas)}/{len(fns)} boas: {boas}")
    cols = 4
    linhas = [miniaturas[i:i + cols] for i in range(0, len(miniaturas), cols)]
    while len(linhas[-1]) < cols:
        linhas[-1].append(np.zeros_like(miniaturas[0]))
    contato = np.vstack([np.hstack(l) for l in linhas])
    saida = args.saida or os.path.join(args.dir, "contato.jpg")
    cv2.imwrite(saida, contato)
    print(f"contato: {saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
