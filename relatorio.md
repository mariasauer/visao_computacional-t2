---
title: "Relatório T2 - Visão Computacional"
author:
  - Heric Camargo — GRR 20203959
  - Maria Sauer — GRRXXXXXXXX
lang: pt-BR
geometry: margin=2.5cm
urlcolor: blue
header-includes:
  - \usepackage{graphicx}
---

# Relatório T2 - Visão Computacional

Heric Camargo - GRR 20203959
Maria Sauer - GRRXXXXXXXX

> Link do código: <https://github.com/mariasauer/visao_computacional-t2>

## 1. Introdução

Calibração de câmera com o método de Zhang usando tabuleiro quadriculado
8x8 casas (7x7 cantos internos, quadrado de 50 mm). Câmera Logitech C920
a 1280x720 (MJPEG), fixa. Objetivos: obter as matrizes intrínseca e de
distorção, demonstrar a remoção da distorção e validar a projeção de
pontos 3D conhecidos nas imagens.

## 2. Método

Primeira tentativa com rajada temporizada (20 fotos a cada 4 s) rendeu só
2/20 aproveitáveis: tabuleiro cortado e borrado por movimento. Trocamos
por um "semáforo" (`scripts/semaforo.py`): preview anotado ao vivo no
monitor da câmera, que só salva fotos com os 7x7 cantos inteiros e
nitidez acima do limiar, até 15 fotos (`imgs/semaforo/`).

A calibração (`scripts/calibra.py`, OpenCV `calibrateCamera`, refino
`cornerSubPix`) usou 12 das 15 fotos, excluindo 2 outliers com erro de
reprojeção acima de 1,5 px. O experimento 3D para 2D
(`scripts/experimento_3d2d.py`) estima a pose por `solvePnP`, reprojeta
os 49 cantos e desenha um cubo virtual de 100 mm sobre o tabuleiro.

## 3. Resultados

Matriz intrínseca e distorção obtidas:

```
K = [[990,   0, 649],
     [  0, 989, 391],
     [  0,   0,   1]]
dist = [0.073, -0.714, 0.0087, 0.0037, 2.56]
```

Erro médio de reprojeção da calibração: **0,27 px**. Por foto, 12 fotos
entre 0,20 e 0,34 px (figura 1: cantos detectados em verde, reprojeção
em vermelho).

![Tracking por foto: cantos detectados e reprojetados](imgs/semaforo/tracking.jpg){ width=95% }

A remoção da distorção foi aplicada com `getOptimalNewCameraMatrix` +
`undistort` (figura 2).

![Original e com distorção removida](imgs/semaforo/undistort_exemplo.jpg){ width=90% }

No experimento 3D para 2D, com o tabuleiro a
t = [381, 181, 2132] mm da câmera, os 49 cantos 3D foram reprojetados
com **RMSE de 0,27 px**, e o cubo virtual de 100 mm assentou sobre o
tabuleiro (figura 3). Um GIF com o cubo rastreado em vídeo
(`imgs/cubo.gif`, 21/80 quadros com pose) está no repositório.

![Cubo virtual de 100 mm projetado sobre o tabuleiro](imgs/experimento/foto02_cubo.jpg){ width=90% }

## 4. Conclusão

A calibração por Zhang com 12 fotos rendeu intrínsecos coerentes
(fx ~ fy, centro próximo ao meio do sensor) e erro de 0,27 px. O
experimento 3D para 2D confirmou a cadeia completa: pontos 3D conhecidos
projetam-se nos pixels corretos. O gargalo prático foi a captura —
validação automática no ato (semáforo) resolveu o que a rajada cega não
conseguiu. Como extensão, o setup permite estéreo com duas câmeras.

## Referências

- ZHANG, Z. A flexible new technique for camera calibration. IEEE
  Transactions on Pattern Analysis and Machine Intelligence, 2000
  (`refs/zhang-2000-A_flexible_new_technique_for_camera_calibration.pdf`).
- Tutoriais de calibração do OpenCV, série 4.x
  (`refs/10-compVis-camera-calibration.pdf`).
