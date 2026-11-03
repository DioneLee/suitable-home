"""예시 평면도(바닥 색 포함) 그리기 → samples/plan_sample_color.png

투룸, 벽 중심선 기준 9.0m × 5.0m = 45㎡. 생활(원목)·수면(연베이지)·서비스(욕실 하늘색, 현관 체크, 수납 회색 X)를
네이버 2D 평면도와 비슷한 색으로 칠해 '도면 분석'의 조닝·동선을 시험·시연하는 데 쓴다. 저작권 문제 없는 직접 그린 도면.
사용: python scripts/verify/make_plan_sample_color.py
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[2]
S = 100                      # px / m
OX, OY = 170, 150             # 집 바깥 왼쪽 위 (여백에 치수선, 네이버 도면처럼 넉넉히)
WO, WI = 0.20, 0.12          # 바깥벽·안벽 두께 (m)
W, D = 9.0, 5.0              # 벽 중심선 기준 가로·세로 (m)
WALL, WOOD, WOOD2, BEIGE, BLUE, TILE1, TILE2, STORE = (25, 25, 25), (226, 160, 95), (214, 149, 88), (246, 236, 210), (220, 236, 244), (237, 237, 237), (251, 251, 251), (238, 238, 238)
COUNTER, TEXT, DIM = (150, 110, 80), (95, 95, 95), (130, 130, 130)

img = Image.new("RGB", (int(OX * 2 + (W + WO) * S), int(OY * 2 + (D + WO) * S)), "white")
g = ImageDraw.Draw(img)
font = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 20)
small = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 14)
P = lambda x, y: (OX + (x + WO / 2) * S, OY + (y + WO / 2) * S)          # 중심선 좌표(m) → 픽셀
def rect(x0, y0, x1, y1, fill): g.rectangle([*P(x0, y0), *P(x1, y1)], fill=fill)

# 바닥 (중심선 좌표, 벽 밑까지 칠하고 벽을 위에 그린다)
rect(3.2, 0, 9.0, 5.0, WOOD)                                    # 거실·주방
for i in range(0, 60):                                          # 원목 결
    y = i * 0.09
    if y < 5.0: g.line([P(3.2, y), P(9.0, y)], fill=WOOD2, width=1)
rect(0, 0, 3.2, 2.6, BEIGE); rect(0, 2.6, 3.2, 5.0, BEIGE)      # 침실 1, 2
rect(6.8, 0, 9.0, 2.2, BLUE)                                    # 욕실
for j in range(5):                                              # 현관 체크 (0.28m 칸)
    for i in range(5):
        x0, y0 = 7.6 + i * 0.28, 3.6 + j * 0.28
        rect(x0, y0, min(x0 + 0.28, 9.0), min(y0 + 0.28, 5.0), TILE1 if (i + j) % 2 else TILE2)
rect(6.8, 3.6, 7.6, 5.0, STORE)                                 # 신발장
g.line([P(6.8, 3.6), P(7.6, 5.0)], fill=DIM, width=2); g.line([P(7.6, 3.6), P(6.8, 5.0)], fill=DIM, width=2)
rect(0.1, 4.3, 1.5, 4.9, STORE)                                 # 침실2 붙박이장
g.line([P(0.1, 4.3), P(1.5, 4.9)], fill=DIM, width=2); g.line([P(1.5, 4.3), P(0.1, 4.9)], fill=DIM, width=2)
rect(3.4, 0.06, 6.6, 0.66, COUNTER)                             # 주방 카운터

# 벽: 바깥벽 + 안벽, 문은 틈으로
def wall_h(x0, x1, y, t): g.rectangle([*P(x0 - t / 2, y - t / 2), *P(x1 + t / 2, y + t / 2)], fill=WALL)
def wall_v(x, y0, y1, t): g.rectangle([*P(x - t / 2, y0 - t / 2), *P(x + t / 2, y1 + t / 2)], fill=WALL)
wall_h(0, 9.0, 0, WO); wall_h(0, 9.0, 5.0, WO); wall_v(0, 0, 5.0, WO)
wall_v(9.0, 0, 3.75, WO); wall_v(9.0, 4.65, 5.0, WO)            # 오른쪽 바깥벽: 현관문 틈 0.9m
wall_v(3.2, 0, 1.4, WI); wall_v(3.2, 2.3, 3.2, WI); wall_v(3.2, 4.1, 5.0, WI)   # 침실 1·2 문 틈
wall_h(0, 3.2, 2.6, WI)                                         # 침실 1 | 침실 2
wall_v(6.8, 0, 2.2, WI); wall_h(6.8, 7.2, 2.2, WI); wall_h(8.1, 9.0, 2.2, WI)  # 욕실 (문 틈 7.2~8.1)
wall_h(6.8, 9.0, 3.6, WI); wall_v(6.8, 3.6, 5.0, WI)            # 신발장·현관 칸 (현관은 거실 쪽으로 열림)
g.rectangle([*P(7.6, 3.6 - WI / 2), *P(8.6, 3.6 + WI / 2)], fill=TILE2)      # 현관 → 거실 열린 부분
g.rectangle([*P(6.8 - WI / 2, 3.6), *P(6.8 + WI / 2, 5.0)], fill=WALL)

# 이름
for x, y, t in [(1.6, 1.3, "침실 1"), (1.6, 3.6, "침실 2"), (5.3, 2.8, "거실"), (5.0, 1.1, "주방"), (7.9, 1.1, "욕실"), (8.3, 4.3, "현관")]:
    g.text(P(x, y), t, fill=TEXT, font=font, anchor="mm")

# 치수선 (벽 중심선 기준, mm)
def dim_h(x0, x1, y, label):
    g.line([P(x0, y), P(x1, y)], fill=DIM, width=1)
    for x in (x0, x1): g.line([(P(x, y)[0], P(x, y)[1] - 6), (P(x, y)[0], P(x, y)[1] + 6)], fill=DIM, width=1)
    g.text(((P(x0, y)[0] + P(x1, y)[0]) / 2, P(x0, y)[1] - 12), label, fill=TEXT, font=small, anchor="mm")
def dim_v(x, y0, y1, label):
    g.line([P(x, y0), P(x, y1)], fill=DIM, width=1)
    for y in (y0, y1): g.line([(P(x, y)[0] - 6, P(x, y)[1]), (P(x, y)[0] + 6, P(x, y)[1])], fill=DIM, width=1)
    g.text((P(x, y0)[0] - 26, (P(x, y0)[1] + P(x, y1)[1]) / 2), label, fill=TEXT, font=small, anchor="mm")
dim_h(0, 9.0, -0.55, "9,000"); dim_h(0, 3.2, -0.3, "3,200"); dim_h(3.2, 6.8, -0.3, "3,600"); dim_h(6.8, 9.0, -0.3, "2,200")
dim_v(-0.45, 0, 5.0, "5,000"); dim_v(-0.2, 0, 2.6, "2,600"); dim_v(-0.2, 2.6, 5.0, "2,400")
g.text((img.width / 2, img.height - 30), "예시 평면도 · 투룸 · 전용 45㎡ (벽 중심선 9.0 × 5.0m) · SUITABLE HOME 시연용", fill=DIM, font=small, anchor="mm")

out = REPO / "samples" / "plan_sample_color.png"
img.save(out)
print(out.relative_to(REPO), img.size)
