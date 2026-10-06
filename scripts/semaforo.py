"""Semaforo de calibracao: preview anotado via MJPEG + autosalvamento.

Roda na maquina da camera. Publica o video anotado em
http://127.0.0.1:8080/ (ver com mpv --vo=drm) e salva soh fotos
com 7x7 cantos + nitidez, ate META.
"""
import argparse
import http.server
import os
import threading
import time

import cv2
import numpy as np

PAD = (7, 7)
frame_jpg = None
trava = threading.Lock()
estado = {"salvas": 0, "msg": "AJUSTE O TABULEIRO", "ok": False,
          "parar": False}


class Servidor(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type",
                         "multipart/x-mixed-replace; boundary=frame")
        self.end_headers()
        while not estado["parar"]:
            with trava:
                jpg = frame_jpg
            if jpg is None:
                time.sleep(0.05)
                continue
            try:
                self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\n\r\n"
                                 + jpg + b"\r\n")
                time.sleep(0.05)
            except (BrokenPipeError, ConnectionResetError):
                break

    def log_message(self, *a):
        pass


def nitidez(gray):
    return cv2.Laplacian(gray, cv2.CV_64F).var()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--meta", type=int, default=15)
    ap.add_argument("--limiar", type=float, default=70.0)
    ap.add_argument("--saida", default="/tmp/semaforo")
    ap.add_argument("--porta", type=int, default=8901)
    args = ap.parse_args()
    os.makedirs(args.saida, exist_ok=True)

    cap = cv2.VideoCapture("/dev/video0", cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    if not cap.isOpened():
        raise SystemExit("camera nao abriu")

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", args.porta), Servidor)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    print(f"http://127.0.0.1:{args.porta}/ pronto", flush=True)

    salvas, centroides, ultimo = 0, [], 0.0
    while salvas < args.meta:
        ok, img = cap.read()
        if not ok:
            continue
        g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        lap = nitidez(g)
        flags = (cv2.CALIB_CB_ADAPTIVE_THRESH
                 + cv2.CALIB_CB_NORMALIZE_IMAGE)
        achou, cantos = cv2.findChessboardCorners(g, PAD, flags=flags)

        agora = time.time()
        if achou and lap >= args.limiar:
            centro = cantos.reshape(-1, 2).mean(axis=0)
            nova = all(np.linalg.norm(centro - c) > 40 for c in centroides)
            if nova and agora - ultimo > 2.5:
                salvas += 1
                ultimo = agora
                centroides.append(centro)
                cv2.imwrite(f"{args.saida}/sem{salvas:02d}.jpg", img)
                estado.update(salvas=salvas, msg=f"SALVA {salvas}/{args.meta}",
                              ok=True)
                print(f"SALVA {salvas}/{args.meta} nitidez={lap:.0f}",
                      flush=True)
            else:
                estado.update(msg="POSE REPETIDA - MUDE O ANGULO", ok=False)
            cv2.drawChessboardCorners(img, PAD, cantos, achou)
        else:
            motivo = ("SEGURE PARADO" if achou else "MOSTRE O TABULEIRO INTEIRO")
            estado.update(msg=motivo, ok=False)

        borda = (0, 255, 0) if estado["ok"] else (0, 0, 255)
        cv2.rectangle(img, (0, 0), (1279, 719), borda, 12)
        cv2.putText(img, f"{estado['msg']}  [{salvas}/{args.meta}]", (30, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.6, borda, 3)
        with trava:
            globals()["frame_jpg"] = cv2.imencode(
                ".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 80])[1].tobytes()
        estado["ok"] = False

    print("META ATINGIDA", flush=True)
    time.sleep(2)
    estado["parar"] = True
    srv.shutdown()


if __name__ == "__main__":
    main()
