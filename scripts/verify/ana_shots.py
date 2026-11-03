"""'도면 분석' 탭·보드 스크린샷 (임시 Chrome 프로필, 실제 브라우저 데이터와 섞이지 않음).

먼저 레포 루트에서 테스트 서버:  python -m http.server 8766 --bind localhost
사용: python scripts/verify/ana_shots.py sample   → screenshots/after_v6_ana_{desktop_1280,mobile_390}.png, after_v6_board_sample.png
      python scripts/verify/ana_shots.py 813      → screenshots/process/v6_813_*.png (네이버 도면 → git 제외 폴더에만)
평면도는 앱의 '평면도 올리기'와 같은 경로(파일 입력)로 넣고, 축척은 도면 치수로 맞춘다.
"""
import json, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image

REPO = Path(__file__).resolve().parents[2]          # 이 파일 위치 기준
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
BASE = "http://localhost:8766"
CASES = {
    # 예시: 원본 1260px 에서 100px = 1m → 앱 저장 이미지 900px, 칸 3px
    "sample": dict(img="/samples/plan_sample_color.png", out=REPO / "screenshots", prefix="after_v6_", scale="3 / (100 * im.width / 1260)",
                   listing=dict(id="sc", name="예시 투룸", region="동작구 상도동", deposit=9000, rent=60, fee=10, area=45, rooms=2, basement=False,
                                loanOk=True, usage="주거용", station="상도역", walk=8, commute=35, facing="S")),
    # 301호: 바깥 벽 끝~끝 가로 9,800mm
    "813": dict(img="/screenshots/process/plans/p1_2d.jpg", out=REPO / "screenshots" / "process", prefix="v6_813_", scale="9.8 / (A.box[2] - A.box[0])",
                listing=dict(id="k", name="한강오피스텔 301호", region="마포구 공덕동", deposit=3000, rent=95, fee=15, area=38.51, rooms=1, basement=False,
                             loanOk=True, usage="업무용", station="공덕역", walk=5, commute=67, facing=None)),
}

def page(case, mode, w, h):
    c = CASES[case]
    seed = dict(settings=dict(myCash=5000, rate=3, work="여의도", budget=95, budgetFail=False, commuteMax=None, commuteWarn=True, commuteFail=False),
                people=[dict(id="p1", name="남편", w=dict(price=5, area=5, commute=5, station=5))], listings=[c["listing"]], selectedId=c["listing"]["id"], furniture=[])
    return f"""<!doctype html><meta charset="utf-8"><body style="margin:0;background:#1C1A19">
<script>
(async () => {{
  const W = ms => new Promise(r => setTimeout(r, ms));
  localStorage.setItem('newlywed-home-v1', {json.dumps(json.dumps(seed, ensure_ascii=False))}); localStorage.setItem('suitable-intro', '1');
  const f = document.createElement('iframe'); f.style.cssText = 'border:0;display:block;width:{w}px;height:{h}px'; f.src = '/index.html#studio'; document.body.append(f);
  await new Promise(ok => f.onload = ok); await W(1500);
  const d = f.contentDocument, fw = f.contentWindow;
  const blob = await (await fetch('{c["img"]}')).blob(), dt = new DataTransfer(); dt.items.add(new File([blob], 'plan', {{ type: blob.type }}));
  const inp = d.querySelector('#planFile'); inp.files = dt.files; inp.dispatchEvent(new Event('change', {{ bubbles: true }}));
  for (let i = 0; i < 40 && !fw.eval('!!state.listings[0].plan'); i++) await W(250);   // 인식이 끝날 때까지
  await W(500);
  const l = fw.eval('state.listings[0]'), A = await fw.__ana.analyze(l), im = new Image(); im.src = l.plan.img; await im.decode();
  l.plan.scaleM = {c["scale"]}; l.plan.v++; fw.eval('save(); render();'); await W(800);
  d.querySelector('#stTabAna').click(); await W(1500);
  const hr = d.querySelector('#anaHour'); hr.value = 15; hr.dispatchEvent(new Event('input')); await W(500);
  if ('{mode}' === 'board') {{
    let b; const oc = URL.createObjectURL; fw.URL.createObjectURL = x => {{ b = x; return 'blob:x'; }}; fw.HTMLAnchorElement.prototype.click = function () {{}};
    d.querySelector('#anaBoard').click(); await W(3000);
    document.body.innerHTML = ''; document.body.style.background = '#000'; const img = new Image(); img.src = oc.call(URL, b); img.style.display = 'block'; document.body.append(img); return;
  }}
  const top = d.querySelector('#anaPane').getBoundingClientRect().top + fw.scrollY - 140; fw.scrollTo({{ top, behavior: 'instant' }});
}})();
</script>"""

def shoot(case, mode, win_w, w, h, name):
    out = CASES[case]["out"] / f"{CASES[case]['prefix']}{name}.png"
    tmp_page = REPO / "screenshots" / "process" / "_ana_shot.html"
    tmp_page.write_text(page(case, mode, w, h), encoding="utf-8")
    try:
        with tempfile.TemporaryDirectory() as prof:
            subprocess.run([CHROME, "--headless=new", f"--user-data-dir={prof}", "--hide-scrollbars", "--enable-unsafe-swiftshader",
                            "--virtual-time-budget=20000", f"--window-size={win_w},{h}", f"--screenshot={out}", f"{BASE}/screenshots/process/_ana_shot.html"],
                           capture_output=True, timeout=180)
    finally:
        tmp_page.unlink(missing_ok=True)
    im = Image.open(out)
    if w < win_w: im = im.crop((0, 0, w, h)); im.save(out)
    if mode == "board":   # 보드 높이는 도면 비율에 따라 달라진다 → 아래 검은 빈 줄 잘라내기
        rgb = im.convert("RGB"); px = rgb.load(); y = rgb.height - 1
        while y > 0 and all(px[x, y] == (0, 0, 0) for x in range(0, rgb.width, 50)): y -= 1
        im = im.crop((0, 0, rgb.width, y + 1)); im.save(out)
    print(out.relative_to(REPO), im.size)

if __name__ == "__main__":
    case = sys.argv[1] if len(sys.argv) > 1 else "sample"
    shoot(case, "page", 1280, 1280, 1500, "ana_desktop_1280")
    shoot(case, "page", 500, 390, 1800, "ana_mobile_390")
    shoot(case, "board", 2400, 2400, 2300, "board")   # 보드 높이는 도면 비율에 따라 달라 넉넉히 찍고 잘라낸다
