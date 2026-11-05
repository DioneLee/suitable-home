"""화면별 세로 길이(화면 몇 개 분량) 재기 — 임시 Chrome 프로필 + localhost:8766 (실제 저장 데이터와 섞이지 않음).

먼저 레포 루트에서:  python -m http.server 8766 --bind localhost
사용: python scripts/verify/length_check.py [--page index_v25_backup.html]
결과: 화면 × (PC 1280×800 / 휴대폰 390×844) × (예시 3곳 / 가상 11곳) 의 문서 높이 ÷ 창 높이.
리포트에 탭이 있으면 탭마다(report/cost …) 따로 잰다.
"""
import json, re, subprocess, sys, tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
BASE = "http://localhost:8766"
VIEWS = ["home", "listings", "report", "report/cost", "report/space", "report/commute", "report/fit", "report/location", "criteria", "studio", "subs"]
SIZES = [("PC", 1280, 800), ("휴대폰", 390, 844)]

JS = r"""
const W = ms => new Promise(r => setTimeout(r, ms)), out = [];
(async () => {
  for (const [label, seed] of SEEDS) {
    localStorage.clear(); localStorage.setItem('suitable-intro', '1'); if (seed) localStorage.setItem('newlywed-home-v1', seed);
    for (const [dev, w, h] of SIZES) {
      const f = document.createElement('iframe'); f.style.cssText = `border:0;width:${w}px;height:${h}px`; f.src = PAGE + '#home'; document.body.append(f);
      await new Promise(r => f.onload = r); await W(1500);
      const d = f.contentDocument; d.documentElement.style.scrollBehavior = 'auto';
      for (const v of VIEWS) {
        f.contentWindow.location.hash = v; await W(700);
        if (v.includes('/') && !f.contentWindow.location.hash.includes('/')) continue;
        if (v.includes('/') && !d.querySelector('[data-rptab]')) continue;   // 탭 없는 예전 화면
        out.push([label, dev, v, +(d.documentElement.scrollHeight / h).toFixed(1)]);
      }
      f.remove();
    }
  }
  document.body.innerHTML = '<pre id="r">' + JSON.stringify(out) + '</pre>';
})().catch(e => { document.body.innerHTML = '<pre id="r">' + JSON.stringify([['ERR', e.message]]) + '</pre>'; });
"""

def run(page_name):
    seed11 = json.dumps(json.loads((REPO / "scripts/verify/seed_v25_11.json").read_text(encoding="utf-8")), ensure_ascii=False)
    page = REPO / "screenshots" / "process" / "_len.html"
    page.write_text('<!doctype html><meta charset="utf-8"><body><script>'
                    f'const PAGE = "/{page_name}", VIEWS = {json.dumps(VIEWS)}, SIZES = {json.dumps(SIZES, ensure_ascii=False)}, '
                    f'SEEDS = [["예시 3곳", null], ["가상 11곳", {json.dumps(seed11)}]];' + JS + '</script>', encoding="utf-8")
    try:
        with tempfile.TemporaryDirectory() as prof:
            r = subprocess.run([CHROME, "--headless=new", f"--user-data-dir={prof}", "--virtual-time-budget=120000", "--window-size=1400,1000",
                                "--dump-dom", f"{BASE}/screenshots/process/_len.html"], capture_output=True, timeout=300)
    finally:
        page.unlink(missing_ok=True)
    m = re.search(r'<pre id="r">(.*?)</pre>', r.stdout.decode("utf-8", "replace"), re.S)
    return json.loads(m.group(1)) if m else [["ERR", "결과 없음"]]

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    name = sys.argv[sys.argv.index("--page") + 1] if "--page" in sys.argv else "index.html"
    rows = run(name)
    print(json.dumps(rows, ensure_ascii=False))
    for r in rows: print("\t".join(map(str, r)))
