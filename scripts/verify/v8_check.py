"""v8 한눈에 비교·거래 유형 자동 검사 (임시 Chrome 프로필 + localhost:8766, 실제 브라우저 데이터와 섞이지 않음).

먼저 레포 루트에서:  python -m http.server 8766 --bind localhost
사용: python scripts/verify/v8_check.py [seed.json]   (기본 scripts/verify/seed_v8.json)
결과: 검사 항목별 OK/NG 와 콘솔 경고·에러(selfTest 의 Assertion failed 포함)를 출력한다.
"""
import json, re, subprocess, sys, tempfile
from urllib.parse import unquote
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]          # 이 파일 위치 기준
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
BASE = "http://localhost:8766"

JS = r"""
const W = ms => new Promise(r => setTimeout(r, ms)), out = [], ok = (name, cond, got) => { out.push([cond ? 'OK' : 'NG', name, String(got ?? '')]); document.title = 'AT ' + out.length + ' ' + name; };
async function frame(w, hash) {
  const f = document.createElement('iframe'); f.style.cssText = `border:0;width:${w}px;height:900px`; f.src = '/index.html' + hash; document.body.append(f);
  await new Promise(r => f.onload = r); await W(1200); return f;
}
(async () => {
  localStorage.setItem('newlywed-home-v1', SEED); localStorage.setItem('suitable-intro', '1');
  // 데스크톱 1280
  let f = await frame(1280, '#home'), d = f.contentDocument, fw = f.contentWindow;
  const ev = fw.eval('evaluate(state)'), by = id => ev.all.find(l => l.id === id);
  const exp = { cur: 110, m1: 75, m2: 67.5, m3: 75.5, j1: 47.5, b1: 15 + 27500 * (0.04 / 12) / (1 - (1 + 0.04 / 12) ** -360) };
  for (const [k, v] of Object.entries(exp)) ok(`월 부담 ${k} = ${v.toFixed(2)}`, Math.abs(by(k).monthly - v) < 0.01, by(k).monthly.toFixed(2));
  ok('매매 이자/원금 나눔', /이자 91\.7만 \+ 원금 39\.6만/.test(fw.eval("split(evaluate(state).all.find(l => l.id === 'b1'))")), fw.eval("split(evaluate(state).all.find(l => l.id === 'b1'))"));
  ok('전입신고 불가 탈락', by('m3').reasons.includes('전입신고 불가'), by('m3').reasons.join(','));
  ok('전세 2억 통과(상한 2억 5천)', !by('j1').reasons.length, by('j1').reasons.join(','));
  ok('매매 예산 초과 경고', by('b1').over, by('b1').over);
  // v25: 전체 표는 매물 화면에만 · 홈은 숫자 카드 + 적합도 상위 3곳
  ok('홈: 전체 표 없음 · 상위 3곳', !d.querySelector('[data-view="home"] [data-glance]') && d.querySelectorAll('#topList a').length === Math.min(3, ev.passed.length), d.querySelector('#topList').innerText.replace(/\n/g, ' ').slice(0, 120));
  fw.location.hash = 'listings'; await W(500);
  const home = d.querySelector('#glanceList'), list = home;
  const heads = () => [...home.querySelectorAll('.gl-table thead th .gl-name b')].map(b => b.textContent);
  ok('지금 집 맨 왼쪽', /지금 집/.test(heads()[0]) && home.querySelector('.gl-table thead th.cur'), heads()[0]);
  // v27: 탈락(m3)은 표에서 빼고 '탈락 N곳 보기'에만
  ok('PC 표에 탈락 매물 없음 · 탈락 보기에 있음', !home.querySelector('.gl-table [data-card="m3"]') && home.querySelector('.gl-failed [data-card="m3"]') && /탈락 1곳 보기/.test(home.querySelector('.gl-failed summary').textContent), '');
  ok("탈락 카드에 '전입신고 불가'", home.querySelector('.gl-failed [data-card="m3"]').textContent.includes('전입신고 불가'), '');
  const orders = { price: 'm2,m1,j1,b1', monthly: 'j1,m2,m1,b1', commute: 'b1,j1,m2,m1', area: 'b1,j1,m1,m2' };
  for (const [k, v] of Object.entries(orders)) {
    home.querySelector(`[data-gsort="${k}"]`).click(); await W(100);
    const ids = [...home.querySelectorAll('.gl-table td [data-detail]')].map(b => b.dataset.detail).slice(1).join(',');
    ok(`정렬 ${k}`, ids === v, ids);
  }
  const tx = home.querySelector('.gl-table').innerText;
  for (const t of ['월세', '보증금 1억 3,000 / 50', '전세', '2억', '매매', '3억 2,500', '전입신고 미확인', '원문 링크 없음', '11월 1일 저장', '경로 미입력', '3/5층', '지금 집보다 −35.0만원'])
    ok(`표에 '${t}'`, tx.includes(t), '');
  const ext = [...home.querySelectorAll('.gl-table a[target="_blank"]')];
  ok('외부 링크 모두 새 창 + noopener', ext.length && ext.every(a => /noopener/.test(a.rel)), ext.length);
  ok('주소 → 네이버지도 검색', ext.some(a => a.href.startsWith('https://map.naver.com/p/search/') && decodeURIComponent(a.href).includes('동작구 상도동 상도로 200')), '');
  ok('원문 링크', ext.some(a => a.href === 'https://new.land.naver.com/rooms?articleId=0000000001'), '');
  ok('히어로 2칸: 최저 월 부담 + 조건', /전세 2억/.test(d.querySelector('#stCostSub').textContent), d.querySelector('#stCostSub').textContent);
  ok('히어로 3칸: 가장 가까운 집', d.querySelector('#stScoreSub').textContent === '가장 가까운 집 · 신길동 매매 · 편도 25분', d.querySelector('#stScoreSub').textContent);
  ok('홈 상위 3곳에 적합도·실제 월', /적합도 \d+점 · 실제 월 .+ · 통근/.test(d.querySelector('#topList .gv').textContent), d.querySelector('#topList .gv').textContent);
  fw.location.hash = 'home'; await W(500);
  const h3 = d.querySelector('#heroStats a:nth-child(3)');
  ok('히어로 3칸: 링크(Tab 으로 닿음)', h3.tagName === 'A' && h3.tabIndex === 0 && h3.getAttribute('href') === '#report/commute', h3.getAttribute('href'));
  d.documentElement.style.scrollBehavior = 'auto';   // 헤드리스 가상 시간에서는 부드러운 스크롤이 진행되지 않아 위치 확인만 즉시 스크롤로
  h3.click(); await W(1000);
  ok('히어로 3칸 클릭 → 리포트 통근 탭', fw.location.hash === '#report/commute' && !d.querySelector('#ch3').hidden && d.querySelector('#ch1').hidden && d.querySelector('[data-rptab="commute"]').getAttribute('aria-current') === 'page', fw.location.hash);
  const mg = fw.eval("migrate({ listings: [{ deal: '<b>x</b>', moveIn: 'x', loanYears: '<i>', repay: 'x' }] }).listings[0]");
  ok('불러오기 값 검사(거래 유형 등)', mg.deal === '월세' && mg.moveIn === null && mg.loanYears === 30 && mg.repay === 'amort', JSON.stringify(mg));
  fw.location.hash = 'home'; await W(500);
  // 자세히 보기 (데스크톱) → 같은 매물 시트를 오른쪽 패널로 (화면은 그대로)
  fw.location.hash = 'listings'; await W(500);
  home.querySelector('.gl-table [data-detail="j1"]').click(); await W(600);
  const sf = d.querySelector('#shFacts').innerText;
  ok('자세히 보기 → 오른쪽 매물 시트', fw.location.hash === '#listings' && !d.querySelector('#sheet').hidden && d.querySelector('#sheet').dataset.id === 'j1' && /전세/.test(sf) && /원문 보기/.test(sf), sf.replace(/\n/g, ' / ').slice(0, 120));
  ok('시트 조건 + 계산식', /계산: 47\.5 = 관리비 10 \+ \(2억 − 내 돈 5,000\) × 3% ÷ 12/.test(d.querySelector('#shFormula').textContent), d.querySelector('#shFormula').textContent);
  const pr = d.querySelector('.sheet-panel').getBoundingClientRect();
  ok('PC 패널: 오른쪽 560px', Math.round(pr.width) === 560 && pr.right >= 1279, Math.round(pr.left) + '+' + Math.round(pr.width));
  d.querySelector('[data-sheet-close]').click(); await W(800);
  ok('닫으면 방금 본 매물 강조', d.querySelector('#sheet').hidden && d.querySelector('.gl-table th[data-card="j1"]').classList.contains('flash'), '');
  ok('매물 메뉴 맨 위에 한눈에 비교 (매물 타입 칸 없음)', list.closest('.view').firstElementChild === list && !d.querySelector('#type') && !d.querySelector('#manageList'), '');
  const acts = [...home.querySelectorAll('.gl-table td [data-detail]')].map(b => [...b.parentElement.querySelectorAll('button')].map(x => x.textContent).join('/'));
  ok('표 매물마다 자세히·수정·3D·삭제', acts.length === ev.all.length - ev.all.filter(l => !l.current && l.reasons.length).length && acts.every(a => a === '자세히 보기/수정/3D/삭제'), acts[0]);
  fw.location.hash = 'report'; await W(800);
  ok('순위표 조건', [...d.querySelectorAll('#rankTable .cond')].length === ev.passed.length, d.querySelector('#rankTable .cond')?.textContent);
  ok('리포트 결론 조건', /\(전세 2억/.test(d.querySelector('#c1').textContent), d.querySelector('#c1').textContent.slice(0, 80));
  ok('차트 라벨 두 줄(조건)', Array.isArray(fw.eval('costChart.data.labels[0]')) && fw.eval('costChart.data.labels').some(x => /매매 3억 2,500/.test(x[1])), JSON.stringify(fw.eval('costChart.data.labels[0]')));
  ok('각주에 유형별 계산식', /전세: 관리비/.test(d.querySelector('#ch1 .ch-foot').textContent) && /원리금균등/.test(d.querySelector('#ch1 .ch-foot').textContent), '');
  // 폼: 거래 유형 전환
  fw.eval("startEdit('b1')"); await W(500);
  ok('수정 폼: 매매 칸', d.querySelector('#fDepLabel').textContent === '매매가' && !d.querySelector('[name=loanYears]').closest('label').hidden && d.querySelector('[name=rent]').closest('label').hidden, d.querySelector('#fDepLabel').textContent);
  // 휴대폰 390
  f.remove(); f = await frame(390, '#home'); d = f.contentDocument; fw = f.contentWindow;
  fw.location.hash = 'listings'; await W(500);
  ok('휴대폰: 카드로 표시', d.querySelector('#glanceList .gl-cards').offsetHeight > 0 && d.querySelector('#glanceList .gl-table').offsetHeight === 0, '');
  ok('휴대폰: 지금 집 맨 위', d.querySelector('#glanceList .gl-cards > li').classList.contains('cur'), '');
  const c1 = d.querySelector('#glanceList .gl-cards > li:not(.cur)');
  ok('휴대폰: 카드는 접혀서 시작 (이름 · 실제 월 · 통근 · 통과/탈락)', !c1.querySelector('details').open && /실제 월 .+ · 통근 .+분/.test(c1.querySelector('summary').innerText) && /통과|탈락/.test(c1.querySelector('summary').innerText), c1.querySelector('summary').innerText.replace(/\n/g, ' / '));
  ok('휴대폰: 탈락은 "탈락 N곳 보기"로 접힘', d.querySelector('.gl-failed summary').textContent === `탈락 ${ev.failed.length}곳 보기` && !d.querySelector('.gl-failed').open, d.querySelector('.gl-failed summary').textContent);
  ok('휴대폰: 가로 넘침 없음', d.documentElement.scrollWidth <= 390, d.documentElement.scrollWidth);
  d.querySelector('#glanceList [data-detail="b1"]:not(.gl-table *)').click(); await W(700);
  ok('휴대폰: 자세히 보기 → 시트', !d.querySelector('#sheet').hidden && d.querySelector('#sheet').dataset.id === 'b1' && /매매/.test(d.querySelector('#shFacts').innerText) && /원금/.test(d.querySelector('#shCond').textContent) && /원리금균등 · 연 4% → 이자 91\.7 \+ 원금 39\.6/.test(d.querySelector('#shFormula').textContent), d.querySelector('#shFormula').textContent);
  document.title = 'DONE'; document.body.innerHTML = '<pre id="r">' + encodeURIComponent(JSON.stringify(out)) + '</pre>';
})().catch(e => { document.body.innerHTML = '<pre id="r">' + encodeURIComponent(JSON.stringify([['NG', 'script error', e.message + ' ' + e.stack]])) + '</pre>'; });
"""

def main():
    seed = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "scripts" / "verify" / "seed_v8.json"
    data = json.dumps(json.loads(seed.read_text(encoding="utf-8")), ensure_ascii=False)
    page = REPO / "screenshots" / "process" / "_v8_check.html"
    page.write_text('<!doctype html><meta charset="utf-8"><body><script>const SEED = ' + json.dumps(data) + ';' + JS + '</script>', encoding="utf-8")
    try:
        with tempfile.TemporaryDirectory() as prof:
            r = subprocess.run([CHROME, "--headless=new", f"--user-data-dir={prof}", "--enable-logging=stderr", "--v=0", "--virtual-time-budget=60000",
                                "--window-size=1400,1000", "--dump-dom", f"{BASE}/screenshots/process/_v8_check.html"], capture_output=True, timeout=180)
    finally:
        page.unlink(missing_ok=True)
    dom = r.stdout.decode("utf-8", "replace")
    m = re.search(r"<pre id=\"r\">(%5B.*?)</pre>", dom, re.S)
    rows = json.loads(unquote(m.group(1))) if m else [["NG", "결과 없음 (마지막: " + (re.search(r"<title>(.*?)</title>", dom) or [0, "?"])[1] + ")", ""]]
    for st, name, got in rows: print(f"{st}  {name}" + (f"  → {got}" if got else ""))
    logs = [l for l in r.stderr.decode("utf-8", "replace").splitlines() if "CONSOLE" in l and "index.html" in l]   # 앱이 찍은 콘솔 메시지 전부 (console.assert 실패는 'Assertion' 글자 없이 메시지만 찍힌다)
    print(f"\n앱 콘솔 메시지 {len(logs)}건"); [print("  " + l[:300]) for l in logs]
    print(f"\n{sum(1 for x in rows if x[0] == 'OK')}/{len(rows)} OK")

if __name__ == "__main__":
    main()
