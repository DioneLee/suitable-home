"""v30 새 주소 정리 검사 (2026-11-12, https://suitable-home.pages.dev): 값 미확인 매물 · 백업 화면 · 불러오기 확인 · 예전 주소 띠 · 평면도 치수 보존.
임시 Chrome 프로필 + localhost:8766 (실제 저장 데이터와 섞이지 않음). 가짜 매물·샘플 평면도만 쓴다.
먼저 레포 루트에서:  python -m http.server 8766 --bind localhost
사용: python scripts/verify/v30_check.py
"""
import json, re, subprocess, sys, tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
BASE = "http://localhost:8766"

JS = r"""
const asc = o => JSON.stringify(o).replace(/[<>&]/g, c => '\\u' + c.charCodeAt(0).toString(16).padStart(4, '0'));
const W = ms => new Promise(r => setTimeout(r, ms)), out = [], ok = (name, cond, got) => { out.push([cond ? 'OK' : 'NG', name, String(got ?? '')]); document.title = 'AT ' + asc(out); }, step = s => { document.title = 'AT ' + asc([...out, ['..', s, '']]); };
async function frame(w, hash) { const f = document.createElement('iframe'); f.style.cssText = `border:0;width:${w}px;height:900px`; f.src = '/index.html' + hash; document.body.append(f); await new Promise(r => f.onload = r); await W(1200); return f; }
const reloaded = f => new Promise(r => f.addEventListener('load', r, { once: true }));
(async () => {
  localStorage.setItem('newlywed-home-v1', SEED); localStorage.setItem('suitable-intro', '1');
  const src = await (await fetch('/index.html')).text();
  ok('새 주소는 상수 NEW_SITE 한 곳 (https://suitable-home.pages.dev/) · 예전 주소 이름은 OLD_HOST 한 곳', /const NEW_SITE = 'https:\/\/suitable-home\.pages\.dev\/', OLD_HOST = 'dionelee\.github\.io';/.test(src) && src.split('suitable-home.pages.dev').length === 2 && src.split('dionelee.github.io').length === 2, '');
  for (const [u, t] of [['/privacy.html', '개인정보 처리방침'], ['/404.html', '없는 주소']]) { const r = await fetch(u), h = await r.text();
    ok(`${u} 있음 (${t})`, r.ok && h.includes(`<title>${t}`) && (u !== '/privacy.html' || h.includes('https://github.com/DioneLee/suitable-home/issues')), r.status); }
  let f = await frame(1280, '#home'), d = f.contentDocument, fw = f.contentWindow, q = s => d.querySelector(s);
  // ---- 예전 주소 띠 (localhost 에선 숨김 · 링크·내보내기는 같은 함수)
  ok('예전 주소 띠: 여기(localhost)에선 숨김 · "새 주소 열기" = NEW_SITE · 버튼 "내 데이터 옮기기"', q('#movedBar').hidden && q('#movedGo').href === 'https://suitable-home.pages.dev/' && q('#movedExport').textContent === '내 데이터 옮기기', q('#movedGo').href);
  { let bl = null; const ou = fw.URL.createObjectURL; fw.URL.createObjectURL = b => { bl = b; return 'blob:x'; }; const ac = fw.HTMLAnchorElement.prototype.click; fw.HTMLAnchorElement.prototype.click = function () {};
    q('#movedExport').click(); await W(600); fw.URL.createObjectURL = ou; fw.HTMLAnchorElement.prototype.click = ac;
    const j = bl && JSON.parse(await bl.text());
    ok('"내 데이터 옮기기" → 바로 내보내기 파일 (매물 전부) · 띠 안에 "내보냈어요"', j?.app === 'suitable-home' && j.data.listings.length === fw.eval('state.listings.length') && /내보냈어요/.test(q('#movedMsg').textContent), q('#movedMsg').textContent); }
  // ---- 값 미확인 매물: 계산·점수·순위·홈 상위·3D 에서 빠짐
  const ev0 = fw.eval('evaluate(state)'), top0 = q('#topList').innerHTML, cnt0 = q('#stCount').dataset.to;
  fw.eval(`state.listings.push({ id: 'pend1', name: '값 빠진 집', region: '', addr: '', station: '흑석역', basement: false, loanOk: true, usage: '주거용', current: false, facing: null, deal: '월세', moveIn: null, floorNo: '', route: '', url: '', loanYears: 30, repay: 'amort', deposit: 100, rent: 1, fee: null, area: null, rooms: 2, walk: 5, commute: null, urlSaved: null });
    state.selectedId = 'pend1'; render();`); await W(300);
  const ev1 = fw.eval('evaluate(state)');
  ok('값 미확인(면적·통근 없음) → 계산·점수·순위에서 빠짐 (pending 에만)', !ev1.all.some(l => l.id === 'pend1') && ev1.pending.map(l => l.id).join() === 'pend1' && ev1.passed.length === ev0.passed.length && JSON.stringify(ev1.passed.map(l => [l.id, l.rank, Math.round(l.score)])) === JSON.stringify(ev0.passed.map(l => [l.id, l.rank, Math.round(l.score)])), ev1.pending.length);
  ok('홈 "적합도 상위" 카드·숫자 그대로 (값 미확인은 안 들어감 · 월세 1만이어도 최저 월 부담에 안 나옴)', q('#topList').innerHTML === top0 && q('#stCount').dataset.to === cnt0 && !/값 빠진 집/.test(q('#topList').textContent + q('#stCostSub').textContent), q('#stCostSub').textContent);
  ok('3D·시트: 선택이 값 미확인이면 계산되는 첫 매물로 · 3D 고르기 목록에 없음', fw.eval('state.selectedId') !== 'pend1' && ![...q('#sel3d').options].some(o => o.value === 'pend1'), fw.eval('state.selectedId'));
  fw.location.hash = 'listings'; await W(400);
  const pc = q('.gl-pend [data-card="pend1"]'), cards = [...q('[data-glance]').querySelectorAll('.gl-cards > li')];
  ok('매물 화면: 값 미확인 카드는 계산된 카드 뒤 · "값 미확인 · 수정에서 채우면 계산돼요 (전용면적)" · 통근 미입력 배지 · 자세히·3D 버튼 없음 · PC 에서도 보임',
    !!pc && /값 미확인 · 수정에서 채우면 계산돼요 \(전용면적\)/.test(pc.textContent) && /통근 미입력/.test(pc.textContent) && !pc.querySelector('[data-detail],[data-act="view"]') && pc.checkVisibility()
    && cards.indexOf(pc) > cards.findIndex(li => !li.closest('.gl-pend') && !li.closest('.gl-failed')) && !pc.closest('.gl-failed'), pc?.textContent);
  ok('PC 표에는 값 미확인 없음', !q('.gl-table [data-card="pend1"]'), '');
  { const F = fw.eval('form'); fw.eval("startEdit(state.listings.find(l => !l.current && l.id !== 'pend1').id)"); await W(200); const id = F.id.value; F.url.value = 'javascript:alert(1)'; q('#submitBtn').click(); await W(300);
    const l1 = fw.eval(`state.listings.find(l => l.id === '${id}')`); fw.eval(`startEdit('${id}')`); await W(200); F.url.value = 'https://example.com/a?b=1'; q('#submitBtn').click(); await W(300);
    const l2 = fw.eval(`state.listings.find(l => l.id === '${id}')`), m = fw.eval('migrate')({ listings: [{ url: 'JaVaScRiPt:alert(1)' }, { url: 'https://ok.example/x' }] });
    ok('원문 링크는 http(s)만 저장 (javascript: → 빈 칸 · 예전 저장값도 불러올 때 거름)', l1.url === '' && l1.urlSaved === null && l2.url === 'https://example.com/a?b=1' && m.listings[0].url === '' && m.listings[1].url === 'https://ok.example/x', `${l1.url} / ${l2.url}`); }
  fw.eval("state.listings = state.listings.filter(l => l.id !== 'pend1'); render()");
  // ---- 백업 화면
  ok('메뉴에 백업 없음 · 예전 "데이터와 AI 설정" 칸 없음 · 매물 화면에 내보내기 버튼 없음', !q('.nav a[href="#backup"]') && !q('#manageSec') && !q('[data-view="listings"] #exportBtn'), '');
  q('footer a[href="#backup"]').click(); await W(400);
  ok('맨 아래 "백업" → #backup 화면 (제목 "백업" · 내보내기·불러오기·초기화) · 덮어쓰기 안내 글', fw.location.hash === '#backup' && !q('[data-view="backup"]').hidden && q('[data-view="home"]').hidden && d.title === '백업 · SUITABLE HOME'
    && ['#exportBtn', '#importFile', '#resetBtn'].every(s => q('[data-view="backup"]').contains(q(s))) && /불러오면 지금 이 기기의 매물·평면도가 파일 내용으로 바뀌어요/.test(q('#io').textContent), d.title);
  let confirms = 0; fw.confirm = () => { confirms++; return true; }; fw.alert = () => { confirms++; };
  { const before = fw.localStorage.getItem('newlywed-home-v1'), j = JSON.parse(before), n0 = j.listings.length; j.listings = j.listings.slice(0, 1);
    const dt = new fw.DataTransfer(); dt.items.add(new fw.File([JSON.stringify({ app: 'suitable-home', version: 3, data: j })], 'backup.json', { type: 'application/json' }));
    const inp = q('#importFile'); inp.files = dt.files; inp.dispatchEvent(new fw.Event('change', { bubbles: true })); await W(300);
    ok('불러오기: 파일을 고르면 화면 안에서 한 번 더 확인 ("…가 이 파일 내용으로 바뀌어요" · 바꾸기 / 취소) · confirm() 안 씀 · 아직 안 바뀜',
      /매물 1곳/.test(q('#ioMsg').textContent) && /이 파일 내용으로 바뀌어요/.test(q('#ioMsg').textContent) && q('#ioYes')?.textContent === '바꾸기' && q('#ioNo')?.textContent === '취소' && confirms === 0 && JSON.parse(fw.localStorage.getItem('newlywed-home-v1')).listings.length === n0, q('#ioMsg').textContent);
    q('#ioNo').click(); await W(100);
    ok('취소 → 그대로', /취소했어요/.test(q('#ioMsg').textContent) && JSON.parse(fw.localStorage.getItem('newlywed-home-v1')).listings.length === n0 && fw.eval('state.listings.length') === n0, ''); }
  f.remove();
  // ---- 평면도 치수 보존: 가짜 매물 + 샘플 평면도(크게 키워 내보내기에서 줄어들게) → 내보내기 → 불러오기 → 같은 치수
  localStorage.setItem('newlywed-home-v1', JSON.stringify({ settings: { myCash: 5000, rate: 3, work: '여의도', budget: 95, budgetFail: false, commuteMax: null, commuteWarn: true, commuteFail: false },
    people: [{ id: 'p1', name: '가', w: { price: 5, area: 5, commute: 5, station: 5 } }], selectedId: 'k', furniture: [],
    listings: [{ id: 'k', name: '가짜 평면도 집', region: '마포구', deposit: 3000, rent: 90, fee: 10, area: 38.5, rooms: 1, basement: false, loanOk: true, usage: '주거용', station: '공덕역', walk: 5, commute: 40, facing: 'SE' }] }));
  step('3D 화면 열기'); f = await frame(1280, '#studio'); d = f.contentDocument; fw = f.contentWindow; q = s => d.querySelector(s);
  step('샘플 평면도 키우기');
  let BIG; { const im = new Image(); await new Promise(r => { im.onload = r; im.src = '/samples/plan_sample_color.png'; }); const k = 1500 / Math.max(im.width, im.height), c = document.createElement('canvas');
    c.width = Math.round(im.width * k); c.height = Math.round(im.height * k); const g = c.getContext('2d'); g.drawImage(im, 0, 0, c.width, c.height);
    const px = g.getImageData(0, 0, c.width, c.height); for (let i = 0; i < px.data.length; i += 4) { const n = (Math.random() * 7 | 0) - 3; for (let k = 0; k < 3; k++) px.data[i + k] = Math.max(0, Math.min(255, px.data[i + k] + n)); }
    g.putImageData(px, 0, 0); BIG = c.toDataURL('image/png');   // 사진처럼 잡티를 조금 (압축이 덜 되게)
    const blob = await (await fetch('/samples/plan_sample_color.png')).blob(), dt = new fw.DataTransfer(); dt.items.add(new fw.File([blob], 'plan.png', { type: 'image/png' }));
    const inp = q('#planFile'); inp.files = dt.files; inp.dispatchEvent(new fw.Event('change', { bubbles: true })); }
  step('평면도 인식 기다림');
  for (let i = 0; i < 60 && !fw.eval('!!state.listings[0].plan'); i++) await W(250);
  await W(500);
  fw.eval(`{ const p = state.listings[0].plan; p.scaleM = 0.06; p.winSide = 'left'; p.img = ${JSON.stringify(BIG)}; p.v++; save(); render(); }`);   // 예전 버전에서 저장된 큰 사진처럼 await W(500);
  const sig = async (fw2) => { const l = fw2.eval('state.listings[0]'), A = await fw2.__ana.analyze(l);
    const p = { ...l.plan }; delete p.img;
    return { plan: JSON.stringify(p), facing: l.facing, cellM: A.c, box: A.box.map(v => +(v * A.c).toFixed(4)).join(), total: +A.total.toFixed(4), floorM2: +A.floorM2.toFixed(4), wallM2: +A.wallM2.toFixed(4),
      spaces: JSON.stringify(A.spaces.map(s => Object.fromEntries(Object.entries(s).filter(([, v]) => typeof v === 'number' || typeof v === 'string').map(([k, v]) => [k, typeof v === 'number' ? +v.toFixed(3) : v])))),
      entry: JSON.stringify(A.entry), zoning: A.zoning, imgLen: l.plan.img.length }; };
  step('분석(전)');
  const s0 = await sig(fw);
  ok('가짜 평면도: 인식됨 · 큰 사진(40만 자 넘음, 예전 버전에서 저장된 큰 사진처럼)', !!fw.eval('state.listings[0].plan') && s0.imgLen > 400000, `img ${s0.imgLen} · zoning ${s0.zoning} · total ${s0.total}㎡`);
  let bl = null; { const ou = fw.URL.createObjectURL; fw.URL.createObjectURL = b => { bl = b; return 'blob:x'; }; const ac = fw.HTMLAnchorElement.prototype.click; fw.HTMLAnchorElement.prototype.click = function () {};
    fw.location.hash = 'backup'; await W(300); q('#exportBtn').click(); for (let i = 0; i < 40 && !bl; i++) await W(100); fw.URL.createObjectURL = ou; fw.HTMLAnchorElement.prototype.click = ac; }
  step('내보내기 끝');
  const blText = await bl.text(), j = JSON.parse(blText), ep = j.data.listings[0].plan;   // 창을 닫기 전에 읽어 둠 (닫힌 창의 Blob 은 안 읽힘)
  ok('내보내기 파일에 평면도 전부: 사진(줄이지 않고 그대로) · 인식 칸(mask·gw·gh) · 축척(scaleM) · 창 쪽(winSide) · 고정물 · 방향(facing)', ep && ep.img === fw.eval('state.listings[0].plan.img') && ep.mask && ep.gw && ep.gh && ep.scaleM === 0.06 && ep.winSide === 'left' && Array.isArray(ep.fixtures) && j.data.listings[0].facing === 'SE',
    `img ${ep?.img.length} · ${Object.keys(ep || {}).join(',')}`);
  step('다른 기기처럼 비움'); localStorage.setItem('newlywed-home-v1', JSON.stringify({ ...JSON.parse(localStorage.getItem('newlywed-home-v1')), listings: [] }));   // 다른 기기처럼 비우고
  f.remove(); step('백업 화면 열기'); f = await frame(1280, '#backup'); d = f.contentDocument; fw = f.contentWindow; q = s => d.querySelector(s);
  ok('불러오기 전: 매물 0곳', fw.eval('state.listings.length') === 0, fw.eval('state.listings.length'));
  { const dt = new fw.DataTransfer(); dt.items.add(new fw.File([blText], 'suitable-home.json', { type: 'application/json' }));
    const inp = q('#importFile'); inp.files = dt.files; inp.dispatchEvent(new fw.Event('change', { bubbles: true })); await W(300);
  for (let i = 0; i < 300 && !q('#ioYes'); i++) await W(100);
  step('불러오기 바꾸기 · ' + q('#ioMsg').textContent + ' · ' + blText.length);
  if (!q('#ioYes')) throw new Error('확인 버튼 없음: ' + q('#ioMsg').textContent);
    const done = reloaded(f); q('#ioYes').click(); await done; await W(1500); }
  fw = f.contentWindow; d = f.contentDocument; q = s => d.querySelector(s);
  step('분석(후)'); const s1 = await sig(fw);
  ok('불러온 뒤: 화면은 #backup · "불러왔어요: 매물 1곳 · 평면도 1개"', fw.location.hash === '#backup' && /불러왔어요: 매물 1곳 · 평면도 1개/.test(q('#ioMsg').textContent), q('#ioMsg').textContent);
  const keys = ['plan', 'facing', 'cellM', 'box', 'total', 'floorM2', 'wallM2', 'entry'];
  ok('치수 보존: 인식 칸·축척·집 크기(가로×세로)·바닥·벽·합계 면적·현관·방향이 내보내기 전과 같음', keys.every(k => s0[k] === s1[k]), keys.filter(k => s0[k] !== s1[k]).map(k => `${k}: ${s0[k]} → ${s1[k]}`).join(' | ') || `집 ${s1.box} m · 합계 ${s1.total}㎡`);
  ok('공간 나눔(색으로 구분한 방·거실)도 같음', s0.spaces === s1.spaces, s0.spaces === s1.spaces ? `공간 ${JSON.parse(s1.spaces).length}개` : `${s0.spaces} → ${s1.spaces}`);
  document.body.innerHTML = '<pre id="r">' + asc(out) + '</pre>';
})().catch(e => { document.body.innerHTML = '<pre id="r">' + asc([...out, ['NG', 'script error', e.message + ' ' + e.stack]]) + '</pre>'; });
"""

def main():
    data = json.dumps(json.loads((REPO / "scripts" / "verify" / "seed_v8.json").read_text(encoding="utf-8")), ensure_ascii=False)
    csp = subprocess.run([sys.executable, str(REPO / "scripts" / "csp.py")], capture_output=True, text=True, encoding="utf-8")   # 인라인 스크립트를 고치면 _headers 해시도 (python scripts/csp.py --write)
    page = REPO / "screenshots" / "process" / "_v30_check.html"
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text('<!doctype html><meta charset="utf-8"><body><script>const SEED = ' + json.dumps(data) + ';' + JS + '</script>', encoding="utf-8")
    try:
        with tempfile.TemporaryDirectory() as prof:
            r = subprocess.run([CHROME, "--headless=new", f"--user-data-dir={prof}", "--enable-logging=stderr", "--v=0", "--virtual-time-budget=400000",
                                "--window-size=1400,1000", "--dump-dom", f"{BASE}/screenshots/process/_v30_check.html"], capture_output=True, timeout=600)
    finally:
        page.unlink(missing_ok=True)
    raw = r.stdout.decode("utf-8", "replace"); m = re.search(r"<pre id=\"r\">(.*?)</pre>", raw, re.S)
    if m and not m.group(1).startswith("["):
        tt = re.search(r"<title>AT (.*?)</title>", raw, re.S); m = None
        rows = json.loads(tt.group(1).replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")) + [["NG", "끝나지 않음 (위 마지막 단계에서 멈춤)", ""]] if tt else [["NG", "결과 없음", ""]]
    if m: rows = json.loads(m.group(1).replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&"))
    rows.insert(0, ["OK" if csp.returncode == 0 else "NG", "CSP: _headers 의 인라인 스크립트 해시가 지금 index.html 과 같음", csp.stdout.strip()])
    for st, name, got in rows: print(f"{st}  {name}" + (f"  → {got}" if got else ""))
    logs = [l for l in r.stderr.decode("utf-8", "replace").splitlines() if "CONSOLE" in l and "index.html" in l]
    print(f"\n앱 콘솔 메시지 {len(logs)}건"); [print("  " + l[:300]) for l in logs]
    bad = sum(1 for x in rows if x[0] != 'OK')
    print(f"\n{len(rows) - bad}/{len(rows)} OK")
    raise SystemExit(1 if bad or logs else 0)

if __name__ == "__main__":
    main()
