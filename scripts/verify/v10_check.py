"""v10 청약 매물 · 대출 계산기 자동 검사 (임시 Chrome 프로필 + localhost:8766, 실제 브라우저 데이터와 섞이지 않음).
2026-11-09 2단계: 청약 화면은 청약 체크(새 사이트)로 옮김 → 청약 화면 항목은 빼고, 메뉴 링크 · 청약 매물 마지막 판정 저장 · subs 보존을 본다.

먼저 레포 루트에서:  python -m http.server 8766 --bind localhost
사용: python scripts/verify/v10_check.py      (시드 scripts/verify/seed_v8.json + 예시 공고 samples/notice_yongsan.json, 우리 상황은 가짜 값)
"""
import json, re, subprocess, tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]          # 이 파일 위치 기준
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
BASE = "http://localhost:8766"

JS = r"""
const asc = o => JSON.stringify(o).replace(/[<>&]/g, c => '\\u' + c.charCodeAt(0).toString(16).padStart(4, '0'));   // 결과 글자에 < 가 있어도 HTML 로 안 바뀌게
const W = ms => new Promise(r => setTimeout(r, ms)), out = [], ok = (name, cond, got) => out.push([cond ? 'OK' : 'NG', name, String(got ?? '')]);
const CHECK = 'https://seoul-cheongyak-check.pages.dev/';
async function frame(w, hash = 'subs') { const f = document.createElement('iframe'); f.style.cssText = `border:0;width:${w}px;height:900px`; f.src = '/index.html#' + hash; document.body.append(f); await new Promise(r => f.onload = r); await W(1200); return f; }
(async () => {
  localStorage.setItem('newlywed-home-v1', SEED); localStorage.setItem('suitable-intro', '1');
  let f = await frame(1280), d = f.contentDocument, fw = f.contentWindow;
  const L = id => fw.eval('evaluate(state)').all.find(l => l.id === id), vis = s => { const e = d.querySelector(s); return !!e && !e.closest('[hidden]'); };
  // 2단계: 청약 화면은 청약 체크로 옮김
  ok('예전 주소 #subs → 홈 · 청약 화면 없음', !d.querySelector('[data-view="subs"]') && vis('[data-view="home"]') && !d.querySelector('#subsSec, #subsNext'), fw.location.hash);
  const navs = [...d.querySelectorAll('.nav a, .tabbar a')].filter(a => a.href === CHECK);
  ok('메뉴(위·휴대폰 탭바): 청약 자리에 "청약 체크 ↗" 새 탭 · #subs 링크 없음', navs.length === 2 && navs.every(a => a.target === '_blank' && /noopener/.test(a.rel) && a.textContent.trim() === '청약 체크 ↗') && !d.querySelector('a[href="#subs"]'), navs.length);
  ok('마이그레이션: 청약 빈 값 (subs 는 그대로 둠)', fw.eval('JSON.stringify([state.subs.tab, state.subs.notices.length, state.subs.me.nw.appl])') === '["newlywed",0,"a"]', fw.eval('JSON.stringify(state.subs.tab)'));
  const m1 = L('m1').monthly;
  // 청약 매물: 마지막 판정을 한 번만 저장 (freezeSubs) · 보증금은 그대로
  const yong = await (await fw.fetch('samples/notice_yongsan.json')).json();
  fw.eval(`state.subs.notices = [normNotice(${JSON.stringify(yong.notice ?? yong)})]; Object.assign(state.subs.me.a, { birth: '1992-05-01', income: 350 }); Object.assign(state.subs.me.b, { birth: '1993-02-01', income: 300 });
    state.subs.me.nw.married = '2024-06-01'; state.subs.wizard.done = true;`);
  const nid = fw.eval('state.subs.notices[0].id'), mk = (id, name) => `state.listings.push({ id: '${id}', name: '${name}', region: '용산구', addr: '', station: '', deal: '월세', deposit: 20000, rent: 73, fee: 14.8, area: 45.51, rooms: 2, basement: false, loanOk: true, usage: '주거용', walk: 5, commute: 40, current: false, moveIn: '가능', floorNo: '', route: '', url: '', loanYears: 30, repay: 'amort', sub: { notice: '${nid}', type: '56', supply: 'special', i: 2, auto: true } }); render();`;
  fw.eval(mk('sOk', '청약 가능 매물')); await W(200);
  ok('자격 되는 청약 매물 → l.sub.no = false 저장 · 탈락 아님', fw.eval("state.listings.find(l => l.id === 'sOk').sub.no") === false && !L('sOk').reasons.length, JSON.stringify(L('sOk').reasons));
  fw.eval("state.subs.me.nw.married = '2019-11-04';"); fw.eval(mk('sNo', '청약 자격 없음 매물')); await W(200);   // 혼인 2,556일 → 특공·일반 모두 불가
  ok('자격 없는 청약 매물 → "청약 체크에서 확인한 결과: 자격 없음" 탈락', fw.eval("state.listings.find(l => l.id === 'sNo').sub.no") === true && L('sNo').reasons.includes('청약 체크에서 확인한 결과: 자격 없음'), JSON.stringify(L('sNo').reasons));
  ok('한 번 저장한 판정은 다시 계산 안 함 (조건이 바뀌어도 그대로)', fw.eval("state.listings.find(l => l.id === 'sOk').sub.no") === false && !L('sOk').reasons.length, '');
  fw.eval('state.settings.myCash = 1000; render();'); await W(200);
  ok('청약 매물 보증금·월세는 저장된 값 그대로 (자금 바꿔도)', fw.eval("JSON.stringify(state.listings.filter(l => l.sub).map(l => [l.deposit, l.rent, l.fee]))") === '[[20000,73,14.8],[20000,73,14.8]]', fw.eval("JSON.stringify(state.listings.filter(l => l.sub).map(l => [l.deposit, l.rent]))"));
  fw.eval('state.settings.myCash = 5000; render();');
  fw.location.hash = 'listings'; await W(500);
  { const gl = d.querySelector('#glanceList').innerText, a = [...d.querySelectorAll('#glanceList a')].find(x => x.href === CHECK);
    ok('한눈에 비교: 탈락 배지 · 다른 청약 매물은 "청약 체크에서 확인 ↗" 링크', /청약 체크에서 확인한 결과: 자격 없음/.test(gl + d.querySelector('#glanceList').textContent) && !!a && a.target === '_blank', gl.slice(0, 80)); }
  ok('newlywed-home-v1 에 subs·판정 저장 (공고 그대로)', (() => { const s = JSON.parse(fw.localStorage.getItem('newlywed-home-v1')); return s.subs.notices.length === 1 && s.listings.find(l => l.id === 'sNo').sub.no === true; })(), '');
  f.remove(); f = await frame(1280, 'listings'); d = f.contentDocument; fw = f.contentWindow;
  ok('다시 열어도 판정 그대로 (sOk 통과 · sNo 탈락)', !L('sOk').reasons.length && L('sNo').reasons.includes('청약 체크에서 확인한 결과: 자격 없음') && fw.eval('state.subs.notices.length') === 1, '');
  ok('기존 매물 그대로 (상도동 투룸 75.0)', Math.abs(L('m1').monthly - m1) < 1e-9 && Math.abs(m1 - 75) < 1e-9, m1);
  // 내보내기: 개인정보 안내 · subs 도 들어감
  let blob = null; const ou = fw.URL.createObjectURL; fw.URL.createObjectURL = b => { blob = b; return 'blob:x'; }; fw.HTMLAnchorElement.prototype.click = function () {};
  d.querySelector('#exportBtn').click(); await W(800); fw.URL.createObjectURL = ou;
  const ex = blob ? JSON.parse(await blob.text()) : null;
  ok('내보내기: 개인정보 안내 · 청약 입력(subs)도 들어감', /개인정보/.test(d.querySelector('#ioMsg').textContent) && ex?.data?.subs?.notices?.length === 1, d.querySelector('#ioMsg').textContent.slice(0, 60));
  // 대출 계산기 (매물 시트 · 매매 LTV)
  fw.eval("state.selectedId = state.listings[0].id; render();"); await W(200);
  d.querySelector('#glanceList .gl-table [data-detail]').click(); await W(500);   // v25: PC 도 매물 시트(오른쪽 패널)에 돈 계산
  { const tl = !d.querySelector('#sheet').hidden && d.querySelector('#shLoan .loan'), li = d.querySelector('.simrank li');
    d.querySelector('[data-sheet-close]').click(); await W(500);
    ok('v25 PC 매물 시트(오른쪽 패널)에 돈 계산 · 순위 첫 칸 4.4em', tl && tl.querySelector('[data-loanpct]') && (!li || getComputedStyle(li).gridTemplateColumns.split(' ')[0] === parseFloat(getComputedStyle(li).fontSize) * 4.4 + 'px'), [!!tl, li && getComputedStyle(li).gridTemplateColumns].join(' ')); }
  const tb = d.createElement('div'); tb.innerHTML = fw.eval("loanBox('t', 70000, true, 'reg', '')"); d.querySelector('#glanceList').append(tb); fw.eval('paintLoans()');
  const tr = tb.querySelector('[data-loanpct]'), tm = () => tb.querySelector('.loan-msg');
  const t40 = tm().textContent; tr.value = 50; tr.dispatchEvent(new fw.Event('input', { bubbles: true }));
  ok('매매 서울 7억: 기본 LTV 40% · 50%로 올리면 빨간 "대출이 안 돼요"', /3억 7,000만원이 더 모자라요/.test(t40) && /규제지역 \(서울 등\)은 LTV 40%까지예요\. 50%는 대출이 안 돼요/.test(tm().textContent) && tm().classList.contains('bad'), t40 + ' / ' + tm().textContent);
  const ts = tb.querySelector('select'); ts.value = 'non'; ts.dispatchEvent(new fw.Event('change', { bubbles: true }));
  ok('지역을 비규제로 → 슬라이더 70% · 경고 사라짐', tr.value === '70' && !/안 돼요/.test(tm().textContent), tm().textContent);
  ok('지역 추정: 서울 구 이름 → 규제 · 의왕 → 비규제', fw.eval("guessRegion({ region: '동작구' })") === 'reg' && fw.eval("guessRegion({ region: '의왕시', addr: '경기 의왕시' })") === 'non', '');
  tb.remove();
  fw.eval("state.listings.push({ id: 'buy1', name: '매매 시험', region: '동작구', addr: '', deal: '매매', deposit: 70000, rent: 0, fee: 20, area: 59, rooms: 3, basement: false, loanOk: true, usage: '주거용', commute: 30, walk: 5, loanYears: 30, repay: 'amort' }); state.selectedId = 'buy1'; openSheet(); render();"); await W(400);
  const sl = d.querySelector('#shLoan .loan');
  ok('매물 시트: 매매는 LTV 계산기 (동작구 → 규제 40%)', sl && sl.dataset.region === 'reg' && sl.querySelector('[data-loanpct]').value === '40' && /LTV/.test(sl.innerText), sl && sl.innerText.replace(/\s+/g, ' ').slice(0, 120));
  fw.eval("closeSheet(); state.listings = state.listings.filter(l => l.id !== 'buy1'); render();"); await W(200);
  // 휴대폰 390
  f.remove(); f = await frame(390, 'home'); d = f.contentDocument; fw = f.contentWindow;
  const tab = [...d.querySelectorAll('.tabbar a')].map(a => a.textContent.trim());
  ok('휴대폰: 탭바 6칸 · 청약 자리에 청약 체크 ↗', tab.length === 6 && tab[2] === '청약 체크 ↗', tab.join('|'));
  ok('390 홈 가로 넘침 없음', d.documentElement.scrollWidth <= 390, d.documentElement.scrollWidth);
  fw.location.hash = 'listings'; await W(500);
  ok('390 매물 가로 넘침 없음 (청약 배지 포함)', d.documentElement.scrollWidth <= 390, d.documentElement.scrollWidth);
  document.body.innerHTML = '<pre id="r">' + asc(out) + '</pre>';
})().catch(e => { document.body.innerHTML = '<pre id="r">' + asc([...out, ['NG', 'script error', e.message + ' ' + e.stack]]) + '</pre>'; });
"""

def main():
    data = json.dumps(json.loads((REPO / "scripts" / "verify" / "seed_v8.json").read_text(encoding="utf-8")), ensure_ascii=False)
    page = REPO / "screenshots" / "process" / "_v10_check.html"
    page.write_text('<!doctype html><meta charset="utf-8"><body><script>const SEED = ' + json.dumps(data) + ';' + JS + '</script>', encoding="utf-8")
    try:
        with tempfile.TemporaryDirectory() as prof:
            r = subprocess.run([CHROME, "--headless=new", f"--user-data-dir={prof}", "--enable-logging=stderr", "--v=0", "--virtual-time-budget=40000",
                                "--window-size=1400,1000", "--dump-dom", f"{BASE}/screenshots/process/_v10_check.html"], capture_output=True, timeout=240)
    finally:
        page.unlink(missing_ok=True)
    m = re.search(r'<pre id="r">(.*?)</pre>', r.stdout.decode("utf-8", "replace"), re.S)
    rows = json.loads(m.group(1).replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")) if m else [["NG", "결과 없음", ""]]
    for st, name, got in rows: print(f"{st}  {name}" + (f"  → {got}" if got else ""))
    logs = [l for l in r.stderr.decode("utf-8", "replace").splitlines() if "CONSOLE" in l and "index.html" in l]
    print(f"\n앱 콘솔 메시지 {len(logs)}건"); [print("  " + l[:300]) for l in logs]
    print(f"\n{sum(1 for x in rows if x[0] == 'OK')}/{len(rows)} OK")

if __name__ == "__main__":
    main()
