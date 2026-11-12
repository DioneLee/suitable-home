"""매물 등록 한 번에 검사 (2026-11-12 새 흐름): 매물 글 붙여넣기 → '등록' → Worker 로 정리(가짜 응답) → 빈 칸 채움 → 바로 저장.
Worker 를 못 쓰면 규칙 읽기(ruleListing)로 같은 글을 읽고 "일부 칸을 못 읽었어요 · 수정에서 채워 주세요".
화면에 AI 문구·AI 설정·내 키가 없는지, 기기에 남은 예전 키 값은 건드리지 않는지도 본다.
임시 Chrome 프로필 + localhost:8766 (실제 저장 데이터와 섞이지 않음). 실제 Worker·Gemini 는 부르지 않는다.
먼저 레포 루트에서:  python -m http.server 8766 --bind localhost
사용: python scripts/verify/ai_check.py
"""
import json, re, subprocess, tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
BASE = "http://localhost:8766"

JS = r"""
const asc = o => JSON.stringify(o).replace(/[<>&]/g, c => '\\u' + c.charCodeAt(0).toString(16).padStart(4, '0'));
const W = ms => new Promise(r => setTimeout(r, ms)), out = [], ok = (name, cond, got) => out.push([cond ? 'OK' : 'NG', name, String(got ?? '')]);
async function frame(w, hash) { const f = document.createElement('iframe'); f.style.cssText = `border:0;width:${w}px;height:900px`; f.src = '/index.html' + hash; document.body.append(f); await new Promise(r => f.onload = r); await W(1200); return f; }
(async () => {
  localStorage.setItem('newlywed-home-v1', SEED); localStorage.setItem('suitable-intro', '1');
  localStorage.setItem('suitable-gemini-key', 'TEST-ONLY-0000');   // 예전에 저장해 둔 키 값 (건드리지 않아야 함)
  const texts = (await (await fetch('/samples/listing_texts.json')).json()).items;
  let f = await frame(1280, '#listings'), d = f.contentDocument, fw = f.contentWindow, q = s => d.querySelector(s);
  const WK = fw.eval('AI_WORKER');
  // ---- 가짜 Worker (매물 글 정리)
  let wcalls = [], wplan = [], other = [];
  fw.fetch = async (url, o) => { if (url.startsWith(WK)) { wcalls.push({ url, body: o.body, headers: o.headers }); const p = wplan.shift() ?? { status: 503 };
      if (p.delay) await new Promise(r => setTimeout(r, p.delay)); if (p.net) throw new TypeError('net'); if (p.wait) return new Promise((_, rej) => o.signal.addEventListener('abort', () => rej(new DOMException('a', 'AbortError'))));
      return new fw.Response(JSON.stringify(p.status ? { error: 'x' } : { text: p.text }), { status: p.status || 200 }); }
    if (/generativelanguage|googleapis/.test(url)) other.push(url); return fetch(url, o); };
  const vtext = () => [q('#formDlg'), q('footer'), q('[data-view="listings"]')].map(e => e.innerText + ' ' + [...e.querySelectorAll('[aria-label],[placeholder],[title]')].map(x => x.getAttribute('aria-label') + x.getAttribute('placeholder') + x.getAttribute('title')).join(' ')).join(' ');
  // ---- 화면 문구
  ok('맨 아래: "계산은 이 브라우저에서만 · 데이터는 이 기기에만 · 매물 글은 정리를 위해 Google로 · 지도 주소는 OpenStreetMap으로 · 참고용 계산" · 청약 문장 없음 · 백업 링크',
    q('footer .wrap').firstChild.textContent.trim() === '계산은 이 브라우저에서만 · 데이터는 이 기기에만 · 매물 글은 정리를 위해 Google로 · 지도 주소는 OpenStreetMap으로 · 참고용 계산' && !/청약|공고/.test(q('footer').textContent) && q('footer a[href="#backup"]')?.textContent === '백업', q('footer').textContent);
  q('.nav [data-addform]').click(); await W(300);
  ok('화면에 AI 문구 없음 (AI로 읽기 · AI가 채움 · Gemini로 보내요 · 직접 붙여넣기 · 내 키 · AI 설정)', !/\bAI\b|Gemini|직접 붙여넣기|내 키|AI 설정/.test(vtext()) && !q('#aiSet') && !q('#aiKey') && !q('#manageSec'), vtext().match(/.{0,20}(\bAI\b|Gemini|직접 붙여넣기|내 키).{0,20}/)?.[0]);
  ok('등록 창: 맨 위 "매물 글 붙여넣기" → 접힌 "직접 입력"(칸들) → 버튼 "등록" · 필수 칸 없음 · 글 칸에 포커스',
    q('#formDlg').open && !!(q('#pasteBox').compareDocumentPosition(q('#formDirect')) & 4) && q('#formDirect').tagName === 'DETAILS' && !q('#formDirect').open && q('#formDirect').contains(q('#form [name=deposit]')) && q('#formDirect summary').textContent.startsWith('직접 입력')
    && q('#submitBtn').textContent === '등록' && !q('#form [required]') && d.activeElement === q('#lstText') && /매물 글 붙여넣기/.test(q('#pasteBox h4').textContent), d.activeElement?.id);
  const reg = async (text, plan, ms = 400) => { wplan = [...plan]; q('.nav [data-addform]').click(); await W(200); const n0 = fw.eval('state.listings.length'); q('#lstText').value = text; q('#submitBtn').click(); await W(ms);
    return fw.eval('state.listings.length') === n0 + 1 ? fw.eval('state.listings.at(-1)') : null; };
  const asG = e => { const g = { ...e }; if ('floor' in e) { g.basement = e.floor === '반지하'; delete g.floor; } return g; };
  const same = (l, e) => Object.entries(e).filter(([k]) => !['floor', 'moveIn', 'loan'].includes(k)).every(([k, v]) => String(l[k]) === String(v)) && (!('floor' in e) || l.basement === (e.floor === '반지하')) && (!('moveIn' in e) || l.moveIn === e.moveIn) && (!('loan' in e) || l.loanOk === (e.loan === '가능'));
  const added = [];
  for (const [k, it] of texts.entries()) {
    wcalls = []; const l = await reg(it.text, [{ text: JSON.stringify(k === 0 ? { ...asG(it.expect), rooms: 99 } : asG(it.expect)) }]); added.push(l?.id);
    ok(`가상 매물 글 ${k + 1}: '등록' 한 번 → Worker /listing 에 글만 보냄 → 바로 카드로 저장 · 값 ${Object.keys(it.expect).length}개 · 통근이 없어도 계산되는 카드` + (k === 0 ? ' (범위 밖 방 99 는 버리고 규칙 읽기 값 2)' : ''),
      !!l && wcalls.length === 1 && wcalls[0].url === WK + '/listing' && wcalls[0].body === it.text && !/goog|key/i.test(JSON.stringify(wcalls[0].headers)) && same(l, it.expect) && !q('#formDlg').open && fw.location.hash === '#listings' && !q(`.gl-pend [data-card="${l.id}"]`) && fw.eval(`evaluate(state).all.some(x => x.id === '${l.id}')`), JSON.stringify(l));
  }
  { const l = fw.eval('state.listings.at(-1)'); }
  const l0 = fw.eval(`state.listings.find(l => l.id === '${added[0]}')`);
  ok('이름 비우면 자동: 역 + 방 개수 ("망원역 투룸")', l0.name === '망원역 투룸', l0.name);
  { const c = q(`.gl-cards [data-card="${l0.id}"]`), ev = fw.eval('evaluate(state)'), e0 = ev.all.find(l => l.id === l0.id);
    ok('통근을 안 적어도 계산: 카드에 실제 월 부담 숫자 · "통근 미입력" 배지 · 값 미확인 아님 · 적합도 점수·순위 있음(통근 점수는 통과 매물 평균) · 자세히 보기·수정·3D·삭제 버튼 · 안내 없음',
      l0.commute == null && !!c && /실제 월 [\d.]+만원/.test(c.textContent) && /통근 미입력/.test(c.querySelector('.badge.warn')?.textContent || '') && !/값 미확인/.test(c.textContent) && !!e0 && Number.isFinite(e0.monthly)
      && (e0.reasons.length || Number.isFinite(e0.score) && e0.rank >= 1) && ['data-detail', 'data-act="edit"', 'data-act="view"', 'data-act="del"'].every(s => c.querySelector(`[${s}]`)) && q('#regMsg').textContent === '', c?.textContent.replace(/\s+/g, ' ').slice(0, 160)); }
  ok('카드 요약 한 줄: 거래 · 보증금/월세 · 관리비 · 면적 · 방 · 층 · 역 도보', q(`[data-card="${l0.id}"] .gl-line`).textContent === '월세 3,000 / 70 · 관리비 8만 · 전용 42.5㎡ · 방 2 · 3/5층 · 망원역 도보 6분', q(`[data-card="${l0.id}"] .gl-line`).textContent);
  // ---- Worker 를 못 쓰면 규칙 읽기 (같은 글)
  for (const [k, it] of texts.entries()) for (const [why, plan, ms] of [['꺼짐(503)', [{ status: 503 }], 400], ['붐빔(502) 두 번', [{ status: 502 }, { status: 502 }], 2600], ['연결 안 됨 두 번', [{ net: 1 }, { net: 1 }], 2600]]) {
    if (k > 0 && why !== '꺼짐(503)') continue;
    wcalls = []; const l = await reg(it.text, plan, ms); added.push(l?.id);
    ok(`Worker ${why} → 규칙 읽기로 글 ${k + 1} 의 값 그대로 저장 (${wcalls.length}번 부름) · 안내 "일부 칸을 못 읽었어요 · 수정에서 채워 주세요"`, !!l && same(l, it.expect) && wcalls.length === plan.length && q('#regMsg').textContent === '일부 칸을 못 읽었어요 · 수정에서 채워 주세요', JSON.stringify(l) + ' · ' + q('#regMsg').textContent);
  }
  { const l = await reg('투룸 3000/68, 관리비 8만, 전용 41㎡, 방2, 3층/5층, 흑석역 도보 5분', [{ status: 503 }]); added.push(l?.id);
    ok('지시서 예: "3000/68 · 관리비 8만 · 전용 41㎡ · 방2 · 3층/5층 · 흑석역 도보 5분" → 이름 "흑석역 투룸"', l?.name === '흑석역 투룸' && l.deposit === 3000 && l.rent === 68 && l.fee === 8 && l.area === 41 && l.rooms === 2 && l.floorNo === '3/5' && l.station === '흑석역' && l.walk === 5, JSON.stringify(l)); }
  { const l = await reg('좋은 집이에요 연락 주세요', [{ text: '{}' }]); added.push(l?.id);
    ok('값을 못 찾은 글도 저장 (모두 미확인 · 이름 "새 매물") · 안내', l?.name === '새 매물' && l.deposit == null && l.area == null && q('#regMsg').textContent === '일부 칸을 못 읽었어요 · 수정에서 채워 주세요' && /전용 미확인 · 방 미확인/.test(q(`[data-card="${l.id}"] .gl-line`).textContent), JSON.stringify(l)); }
  { wplan = [{ delay: 600, text: JSON.stringify({ deal: '전세', deposit: 21000 }) }]; q('.nav [data-addform]').click(); await W(200); const n0 = fw.eval('state.listings.length'); q('#lstText').value = texts[1].text; q('#submitBtn').click(); await W(200);
    ok('읽는 중: 버튼 "읽는 중…"(못 누름) · 안내', q('#submitBtn').disabled && q('#submitBtn').textContent === '읽는 중…' && /정리하는 중/.test(q('#lstMsg').textContent), q('#lstMsg').textContent);
    q('#formClose').click(); await W(800);
    ok('읽는 중에 창을 닫으면 저장 안 함', fw.eval('state.listings.length') === n0, fw.eval('state.listings.length')); }
  // 1분 제한 (시험에선 300ms)
  { const st = fw.setTimeout; fw.setTimeout = (fn, ms, ...a) => st(fn, ms === 60000 ? 300 : ms, ...a);
    const l = await reg(texts[1].text, [{ wait: 1 }], 900); fw.setTimeout = st; added.push(l?.id);
    ok('1분 안에 못 읽으면 끊고 규칙 읽기로 저장', !!l && l.deposit === 21000 && l.area === 59 && q('#regMsg').textContent === '일부 칸을 못 읽었어요 · 수정에서 채워 주세요', JSON.stringify(l)); }
  // ---- 직접 입력 (접힌 칸) · 글 없이
  q('.nav [data-addform]').click(); await W(200); wcalls = [];
  q('#submitBtn').click(); await W(200);
  ok('글도 칸도 비우고 등록 → 안내만 (저장 안 함)', q('#formDlg').open && /매물 글을 붙여넣거나, 직접 입력에 적어 주세요/.test(q('#lstMsg').textContent) && wcalls.length === 0, q('#lstMsg').textContent);
  q('#formDirect summary').click(); await W(100);
  const F = fw.eval('form'); F.name.value = '직접 입력 집'; F.deposit.value = 5000; F.rent.value = 50; F.area.value = 30; F.rooms.value = 1; F.commute.value = 40;
  q('#submitBtn').click(); await W(400);
  { const l = fw.eval('state.listings.at(-1)'); added.push(l.id);
    ok('직접 입력만 → Worker 안 부르고 저장 · 값이 다 있으면 순위 계산에 들어감 · 안내 없음', l.name === '직접 입력 집' && wcalls.length === 0 && fw.eval(`evaluate(state).all.some(x => x.id === '${l.id}')`) && q('#regMsg').textContent === '' && !q('.gl-pend [data-card="' + l.id + '"]'), JSON.stringify(l)); }
  // ---- 수정: 붙여넣기 칸 숨김 · 직접 입력 펼침 · 통근 채우면 배지 사라짐
  q(`.gl-cards [data-card="${l0.id}"] [data-act="edit"]`).click(); await W(300);
  ok('수정: 붙여넣기 칸 숨김 · 직접 입력 펼침 · 버튼 "수정 저장" · 이름에 포커스', q('#pasteBox').hidden && q('#formDirect').open && q('#submitBtn').textContent === '수정 저장' && d.activeElement === F.name, d.activeElement?.name);
  F.commute.value = 35; F.rooms.value = 2; q('#submitBtn').click(); await W(400);
  ok('수정에서 통근 채움 → "통근 미입력" 배지 사라지고 실제 통근으로 점수', fw.eval(`state.listings.find(l => l.id === '${l0.id}').commute`) === 35 && !/통근 미입력/.test(q(`.gl-cards [data-card="${l0.id}"]`).textContent) && fw.eval(`evaluate(state).all.find(l => l.id === '${l0.id}').commuteS`) === 35, '');
  // ---- 실사용 시나리오 (2026-11-12): 붙여넣기 등록(통근 없음) → 카드에 실제 월 부담 · 홈 '적합도 상위'
  { const l = await reg('쓰리룸 1000/30, 관리비 5만, 전용 80㎡, 방3, 5층/10층, 흑석역 도보 1분, 주거용, 전입신고 가능', [{ status: 503 }]); added.push(l?.id);
    const c = q(`.gl-cards [data-card="${l.id}"]`), m = fw.eval(`evaluate(state).all.find(x => x.id === '${l.id}')`);
    ok('붙여넣기 등록(통근 없음) → 카드에 실제 월 부담 숫자', l.commute == null && /실제 월 [\d.]+만원/.test(c.textContent) && c.textContent.includes(`${m.monthly.toFixed(1)}만원`), c.textContent.replace(/\s+/g, ' ').slice(0, 140));
    fw.location.hash = 'home'; await W(400);
    ok('붙여넣기 등록(통근 없음) → 홈 "적합도 상위"에 들어감 (통근 점수는 통과 매물 평균)', !m.reasons.length && q('#topList').textContent.includes('흑석역 쓰리룸') && !!q(`#topList [data-detail="${l.id}"]`), q('#topList').textContent.replace(/\s+/g, ' ').slice(0, 160));
    fw.location.hash = 'listings'; await W(300); }
  // ---- 예전 키 값 · 다른 곳으로 안 보냄
  ok('기기에 남은 예전 키 값은 그대로 (지우지도 쓰지도 않음) · Gemini 로 직접 안 보냄 · 저장 데이터에 안 들어감', fw.localStorage.getItem('suitable-gemini-key') === 'TEST-ONLY-0000' && other.length === 0 && !/TEST-ONLY-0000/.test(fw.localStorage.getItem('newlywed-home-v1')), other.join());
  // ---- 390
  f.remove(); f = await frame(390, '#listings'); d = f.contentDocument; q = s => d.querySelector(s);
  ok('390 매물 화면 가로 넘침 없음 (값 미확인 카드 포함)', d.documentElement.scrollWidth <= 390 && !!q('.gl-pend'), d.documentElement.scrollWidth);
  document.body.innerHTML = '<pre id="r">' + asc(out) + '</pre>';
})().catch(e => { document.body.innerHTML = '<pre id="r">' + asc([...out, ['NG', 'script error', e.message + ' ' + e.stack]]) + '</pre>'; });
"""

def main():
    data = json.dumps(json.loads((REPO / "scripts" / "verify" / "seed_v8.json").read_text(encoding="utf-8")), ensure_ascii=False)
    page = REPO / "screenshots" / "process" / "_ai_check.html"
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text('<!doctype html><meta charset="utf-8"><body><script>const SEED = ' + json.dumps(data) + ';' + JS + '</script>', encoding="utf-8")
    try:
        with tempfile.TemporaryDirectory() as prof:
            r = subprocess.run([CHROME, "--headless=new", f"--user-data-dir={prof}", "--enable-logging=stderr", "--v=0", "--virtual-time-budget=90000",
                                "--window-size=1400,1000", "--dump-dom", f"{BASE}/screenshots/process/_ai_check.html"], capture_output=True, timeout=240)
    finally:
        page.unlink(missing_ok=True)
    m = re.search(r'<pre id="r">(.*?)</pre>', r.stdout.decode("utf-8", "replace"), re.S)
    rows = json.loads(m.group(1).replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")) if m else [["NG", "결과 없음", ""]]
    for st, name, got in rows: print(f"{st}  {name}" + (f"  → {got}" if got else ""))
    logs = [l for l in r.stderr.decode("utf-8", "replace").splitlines() if "CONSOLE" in l and "index.html" in l]
    print(f"\n앱 콘솔 메시지 {len(logs)}건"); [print("  " + l[:300]) for l in logs]
    bad = sum(1 for x in rows if x[0] != 'OK')
    print(f"\n{len(rows) - bad}/{len(rows)} OK")
    raise SystemExit(1 if bad or logs else 0)

if __name__ == "__main__":
    main()
