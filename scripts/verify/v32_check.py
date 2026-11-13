"""v32 매물 지도 모아 보기 검사 (2026-11-13): 리포트 > 입지 장 '모아 보기' — 구별 동그라미(개수) · 매물 핀 · 통과만/전체 · 대략 위치 · 한 곳 보기 그대로.
임시 Chrome 프로필 + localhost:8766 (실제 저장 데이터와 섞이지 않음). 가짜 매물(seed_v8)만 쓰고, 위치 검색은 하지 않는다(좌표를 미리 넣어 둠).
먼저 레포 루트에서:  python -m http.server 8766 --bind localhost
사용: python scripts/verify/v32_check.py
"""
import json, re, subprocess, sys, tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
BASE = "http://localhost:8766"

JS = r"""
const asc = o => JSON.stringify(o).replace(/[<>&]/g, c => '\\u' + c.charCodeAt(0).toString(16).padStart(4, '0'));
const W = ms => new Promise(r => setTimeout(r, ms)), out = [], ok = (name, cond, got) => { out.push([cond ? 'OK' : 'NG', name, String(got ?? '')]); document.title = 'AT ' + asc(out); };
async function frame(w, hash) { const f = document.createElement('iframe'); f.style.cssText = `border:0;width:${w}px;height:900px`; f.src = '/index.html' + hash; document.body.append(f); await new Promise(r => f.onload = r); await W(1200); return f; }
(async () => {
  localStorage.setItem('newlywed-home-v1', SEED); localStorage.setItem('suitable-intro', '1');
  for (const w of [1280, 390]) {
    const f = await frame(w, '#home'), d = f.contentDocument, fw = f.contentWindow, q = s => d.querySelector(s), qa = s => [...d.querySelectorAll(s)];
    const errs = []; fw.addEventListener('error', e => errs.push(e.message));
    let nomi = 0; const of = fw.fetch; fw.fetch = (u, o) => { if (String(u).includes('nominatim')) { nomi++;  return Promise.reject(new Error('검색 안 함')); } return of(u, o); };
    // 좌표 미리 넣기: 매물 주소마다 다른 점 (구마다 묶이게) · 첫 매물은 상세 주소 못 찾음 → 지역 위치(대략 위치)
    fw.eval('geoQueue.clear()');   // 처음 열 때 쌓인 검색(가짜 fetch 전)은 버림
    fw.eval(`(() => { const ls = state.listings; ls.forEach((l, i) => { state.geo[homeQuery(l)] = [37.5 + i * 0.01, 126.9 + i * 0.01]; if (l.region) state.geo[l.region] = [37.5 + i * 0.01 + 0.002, 126.9 + i * 0.01]; });
      state.geo[homeQuery(ls[1])] = { miss: Date.now() }; state.geo[state.settings.work] = [37.52, 126.92]; render(); })()`);
    fw.location.hash = 'report/location'; await W(1500);
    const rafFit = () => fw.eval('locMap && locMap._fitLater && (f => (locMap._fitLater = null, f()))(locMap._fitLater)');   // 하네스 iframe 에선 requestAnimationFrame 이 안 돌 때가 있어 화면 전환 때 맞춤을 직접 부름
    rafFit(); await W(1200);
    const ev = fw.eval('evaluate(state)'), rough = fw.eval('state.listings[1]');
    ok(`${w}: 입지 장 기본 = 모아 보기 · 버튼(모아 보기·한 곳 보기·통과만 ${ev.passed.length}·전체 ${ev.all.length}) · 매물 고르기 칩 숨김 · 지도 보임`,
      q('[data-locmode="all"]').getAttribute('aria-pressed') === 'true' && q('[data-locpass="1"]').textContent.includes(String(ev.passed.length)) && q('[data-locpass="0"]').textContent.includes(String(ev.all.length))
      && q('#locChips').hidden && !q('#locMap').hidden && q('#locSvg').hasAttribute('hidden'), q('#locModes').textContent);
    const m = fw.eval('locMap'); m._zoomAnimated = false;   // 확대 애니메이션도 requestAnimationFrame 을 써서 하네스에선 끔
    const guN = () => qa('#locMap .loc-gu').map(e => e.textContent), sumN = () => guN().reduce((s, t) => s + +t.match(/\d+$/)[0], 0);
    ok(`${w}: 통과만 → 구별 동그라미 숫자 합 = 통과 매물 수 ${ev.passed.length} · 매물 핀 없음(멀리) · 직장 핀`, m.getZoom() < 13 && sumN() === ev.passed.length && !qa('#locMap .loc-pin i:not(.work)').length && qa('#locMap .loc-pin i.work').length === 1, `${guN().join(' / ')} · zoom ${m.getZoom()}`);
    const gus = Object.entries(ev.passed.reduce((a, l) => (a[fw.eval('guOfL')(l)] = (a[fw.eval('guOfL')(l)] || 0) + 1, a), {}));
    ok(`${w}: 구 이름 = 지역 칸의 'OO구' · 오른쪽 목록도 구별`, gus.every(([g, n]) => guN().includes(g + n)) && gus.every(([g]) => qa('#locFacts dt').some(e => e.textContent === g)), JSON.stringify(gus));
    ok(`${w}: 상세 주소 못 찾은 매물 → 지역 위치에 '대략 위치' (목록·안내 문구)`, !ev.passed.some(l => l.id === rough.id) || (/대략 위치/.test(q('#locFacts').textContent) && /대략 위치/.test(q('#locLead').textContent)), q('#locFacts').textContent.replace(/\s+/g, ' ').slice(0, 200));
    // 동그라미 누르면 확대 → 매물 핀
    const big = qa('#locMap .loc-gu').sort((a, b) => +b.textContent.match(/\d+$/)[0] - +a.textContent.match(/\d+$/)[0])[0], bigN = +big.textContent.match(/\d+$/)[0];
    big.click(); await W(1500);
    const pins = qa('#locMap .loc-pin i:not(.work)').length, tips = qa('#locMap .leaflet-tooltip').map(e => e.textContent);
    ok(`${w}: 동그라미 누름 → 확대(13 이상) · 매물 핀 + '이름 · 월 N만원' 이름표 (그 구 ${bigN}곳 포함)`, m.getZoom() >= 13 && pins >= bigN && tips.some(t => /· 월 [\d.]+만원/.test(t)), `zoom ${m.getZoom()} · 핀 ${pins} · ${tips.join(' | ').slice(0, 160)}`);
    // 핀 누르면 자세히 보기(시트)
    const pin = qa('#locMap .leaflet-marker-icon.loc-pin').find(e => !e.querySelector('.work')), title = pin.title;
    pin.click(); await W(800);
    ok(`${w}: 핀 누름 → 그 매물 자세히 보기 시트`, !q('#sheet').hidden && title.startsWith(fw.eval('state.listings.find(l => l.id === state.selectedId).name')), title);
    fw.history.back(); await W(600);
    // 전체
    q('[data-locpass="0"]').click(); await W(1200); rafFit(); await W(800);
    ok(`${w}: '전체' → 숫자 합 = 전체 매물 ${ev.all.length} (멀리서 보면)`, (fw.eval('locMap').getZoom() >= 13 ? (m.setZoom(11), true) : true) && await W(800).then(() => sumN() === ev.all.length), guN().join(' / '));
    // 한 곳 보기 = 예전 입지 지도
    const nomiAll = nomi; q('[data-locmode="one"]').click(); await W(1200);
    ok(`${w}: '한 곳 보기' → 매물 고르기 칩 보임 · 통과만/전체 버튼 숨김 · 동그라미 없음 · 예전 화면(가까운 역·직장)`, !q('#locChips').hidden && !q('[data-locpass]') && !qa('#locMap .loc-gu').length && /가까운 역/.test(q('#locFacts').textContent), q('#locFacts').textContent.replace(/\s+/g, ' ').slice(0, 120));
    q('[data-locmode="all"]').click(); await W(1200);
    ok(`${w}: 다시 모아 보기 → 동그라미 돌아옴`, qa('#locMap .loc-gu').length > 0 || qa('#locMap .loc-pin i:not(.work)').length > 0, guN().join(' / '));
    ok(`${w}: 모아 보기는 위치 검색(Nominatim) 안 부름 (좌표 저장값만) · 콘솔 오류 0`, nomiAll === 0 && !errs.length, `${nomiAll} · ${errs.join(' | ')}`);
    ok(`${w}: 가로 넘침 없음`, d.documentElement.scrollWidth <= w, d.documentElement.scrollWidth);
    f.remove();
  }
  // 통과 매물 0 → 안내
  { const f = await frame(1280, '#home'), fw = f.contentWindow, q = s => f.contentDocument.querySelector(s);
    fw.eval("state.settings.budget = 1; state.settings.budgetFail = true; render()");
    fw.location.hash = 'report/location'; await W(800);
    const ev = fw.eval('evaluate(state)');
    ok('통과 매물 0곳(월 부담 상한 1만 · 넘으면 탈락) → 지도 대신 "전체를 누르면…" 안내', ev.passed.length === 0 && ev.all.length > 0 && /전체/.test(q('#locFacts').textContent) && q('#locMap').hidden, `${ev.passed.length} · ${q('#locFacts').textContent}`); }
  document.title = 'DONE ' + asc(out);
})().catch(e => { out.push(['NG', '하네스 오류', e.message + ' ' + (e.stack || '').split('\n')[1]]); document.title = 'DONE ' + asc(out); });
"""

def main():
    seed = json.dumps(json.loads((REPO / 'scripts/verify/seed_v8.json').read_text(encoding='utf-8')), ensure_ascii=False)
    html = '<!doctype html><meta charset="utf-8"><body><script>const SEED = ' + json.dumps(seed) + ';\n' + JS + '</scr' + 'ipt>'
    tmp = REPO / 'screenshots/process/_v32.html'; tmp.parent.mkdir(parents=True, exist_ok=True); tmp.write_text(html, encoding='utf-8')
    try:
        with tempfile.TemporaryDirectory() as prof:
            r = subprocess.run([CHROME, '--headless=new', f'--user-data-dir={prof}', '--virtual-time-budget=120000', '--dump-dom', f'{BASE}/screenshots/process/_v32.html'], capture_output=True, text=True, encoding='utf-8', timeout=300)
    finally:
        tmp.unlink(missing_ok=True)
    m = re.search(r'<title>(?:DONE|AT) (.*?)</title>', r.stdout, re.S)
    rows = json.loads(m.group(1).replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')) if m else [['NG', '결과 없음', r.stdout[-300:]]]
    bad = 0
    for st, name, got in rows:
        if st != 'OK': bad += 1
        print(f'[{st}] {name}' + (f'  → {got}' if st != 'OK' or '-v' in sys.argv else ''))
    print(f'\n{len(rows) - bad}/{len(rows)} 통과' + ('' if m and 'DONE' in r.stdout[m.start():m.start() + 12] else ' (끝까지 못 감)'))
    sys.exit(1 if bad or not rows else 0)

if __name__ == '__main__':
    main()
