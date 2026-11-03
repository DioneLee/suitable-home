"""index.html 전체 페이지 스크린샷 (데스크톱 1280, 모바일 390).

사용: python scripts/verify/screenshot.py <접두어> [대상html] [화면,화면,...]
  예: python scripts/verify/screenshot.py after_                     → screenshots/after_desktop_1280.png, after_mobile_390.png (홈)
      python scripts/verify/screenshot.py after_ index.html home,report → after_home_desktop_1280.png, after_report_… (화면별)
Chrome 헤드리스로 찍는다. 주소 끝 #shot=<화면높이> 로 히어로 높이를 그 기기 화면 높이로 고정하고
등장 효과를 꺼서, 아주 긴 창으로 찍어도 실제 첫 화면 비율이 유지된다. 아래쪽 빈 여백은 잘라낸다.

주의: 헤드리스 Chrome은 창 폭이 최소 500px이라 --window-size=390 은 실제로 500px로 그려진다.
그래서 모바일은 폭 390px iframe 안에 페이지를 띄워 찍고 왼쪽 390px만 잘라낸다.
"""
import subprocess, sys, tempfile
from pathlib import Path
from PIL import Image

REPO = Path(__file__).resolve().parents[2]          # 이 파일 위치 기준 (호출한 폴더 기준 아님)
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
# 이름, 페이지 폭, 찍을 높이, 히어로를 맞출 기기 화면 높이
TARGETS = [("desktop_1280", 1280, 9000, 800), ("mobile_390", 390, 16000, 844)]
MIN_WINDOW = 500

def trim(path: Path, width: int) -> int:
    im = Image.open(path).convert("RGB").crop((0, 0, width, Image.open(path).height))
    w, h = im.size
    px = im.load()
    bg = px[w - 1, h - 1]
    y = h - 1
    near = lambda c: max(abs(c[i] - bg[i]) for i in range(3)) <= 14     # 배경과 거의 같은 색(옅은 격자선 등)은 빈 줄로 본다
    while y > 0 and all(near(px[x, y]) for x in range(0, w, 7)):
        y -= 1
    im.crop((0, 0, w, min(h, y + 40))).save(path)
    return y + 40

def main():
    prefix = sys.argv[1] if len(sys.argv) > 1 else "shot_"
    html = (REPO / (sys.argv[2] if len(sys.argv) > 2 else "index.html")).resolve()
    views = sys.argv[3].split(",") if len(sys.argv) > 3 else [None]      # None = 화면 지정 없음(첫 화면)
    out_dir = REPO / "screenshots"
    out_dir.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for view, (name, w, h, vh) in [(v, t) for v in views for t in TARGETS]:
            out = out_dir / f"{prefix}{view + '_' if view else ''}{name}.png"
            url = f"{html.as_uri()}#shot={vh}{'-' + view if view else ''}"
            if w < MIN_WINDOW:     # 좁은 화면: iframe 으로 실제 폭을 맞춘다
                frame = Path(tmp) / f"frame_{name}.html"
                frame.write_text(f'<!doctype html><body style="margin:0;background:#fff">'
                                 f'<iframe src="{url}" style="border:0;display:block;width:{w}px;height:{h}px"></iframe>',
                                 encoding="utf-8")
                url = frame.as_uri()
            subprocess.run([CHROME, "--headless=new", f"--user-data-dir={Path(tmp) / 'profile'}", "--hide-scrollbars",
                            "--enable-unsafe-swiftshader", "--allow-file-access-from-files", "--virtual-time-budget=9000",
                            f"--window-size={max(w, MIN_WINDOW)},{h}", f"--screenshot={out}", url],
                           check=True, capture_output=True, timeout=120)
            print(f"{out.relative_to(REPO)}  {w}x{trim(out, w)}")

if __name__ == "__main__":
    main()
