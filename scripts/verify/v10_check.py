"""v10 청약(임대 공고) 자동 검사 (임시 Chrome 프로필 + localhost:8766, 실제 브라우저 데이터와 섞이지 않음).

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
async function frame(w) { const f = document.createElement('iframe'); f.style.cssText = `border:0;width:${w}px;height:900px`; f.src = '/index.html#subs'; document.body.append(f); await new Promise(r => f.onload = r); await W(1200); return f; }
(async () => {
  localStorage.setItem('newlywed-home-v1', SEED); localStorage.setItem('suitable-intro', '1');
  let f = await frame(1280), d = f.contentDocument, fw = f.contentWindow;
  fw.__today = '2026-11-04';
  const L = id => fw.eval('evaluate(state)').all.find(l => l.id === id), sub = () => fw.eval("state.listings.find(l => l.sub)"), evSub = () => fw.eval("evaluate(state)").all.find(l => l.sub);
  const set = (path, v) => { const el = d.querySelector(`[data-me="${path}"]`); if (el.type === 'checkbox') el.checked = v; else el.value = v; el.dispatchEvent(new fw.Event('input', { bubbles: true })); };
  const m1 = L('m1').monthly;
  ok('마이그레이션: 청약 빈 값', fw.eval('JSON.stringify([state.subs.tab, state.subs.notices.length, state.subs.me.nw.appl])') === '["newlywed",0,"a"]', fw.eval('JSON.stringify(state.subs.tab)'));
  d.querySelector('#subSample').click(); await W(800);
  ok('예시 공고 넣기', fw.eval('state.subs.notices.length') === 1 && /주택형 4개 · 일정 6개/.test(d.querySelector('#subMsg').textContent), d.querySelector('#subMsg').textContent);
  const nd = () => d.querySelector('#subJudge .next-do')?.innerText.replace(/\s+/g, ' ');
  ok('예시 가족 결과 먼저 (저장 안 함 표시 · 신호등 · 다음 할 일 D-8 11월 12일(목)부터)', /예시 가족 기준 결과예요 · 저장되지 않아요/.test(d.querySelector('#subDemo').innerText) && /신청할 수 있어요/.test(d.querySelector('#subJudge .sig').innerText) && /^D-8 다음 할 일: 11월 12일\(목\)부터 청약 접수/.test(nd()), nd());
  ok('예시 가족 값은 우리 상황에 안 들어감', fw.eval('JSON.stringify([state.subs.me.a.birth, state.subs.me.a.income, state.subs.me.nw.married])') === '["",null,""]', fw.eval('JSON.stringify(state.subs.me.a)'));
  d.querySelector('#subDemoExit').click(); await W(300);
  ok('우리 상황 입력하기 → 질문 1/7', !d.querySelector('#subWiz').hidden && /^1 \/ 7/.test(d.querySelector('#wizCount').textContent) && !d.querySelector('#subDemo').innerHTML, d.querySelector('#wizCount').textContent);
  ok('홈 일정 한 줄', !d.querySelector('#subsNext').hidden && /D-8.*원효로 청년안심주택.*청약 접수/.test(d.querySelector('#subsNext').textContent), d.querySelector('#subsNext').textContent);
  // 우리 상황 (가짜 값): 입력 칸으로 넣기
  set('a.birth', '1992-05-01'); set('b.birth', '1993-02-01');
  const y = d.querySelector('[data-year-for="a.income"]'); y.value = 4200; y.dispatchEvent(new fw.Event('input', { bubbles: true }));
  y.value = 4100; y.dispatchEvent(new fw.Event('input', { bubbles: true })); y.blur(); fw.eval('render()');
  ok('연봉 4,100 → 월 341.7 · 다시 그려도 연봉 4100 (4100.4 아님)', fw.eval('state.subs.me.a.income') === 341.7 && y.value === '4100', y.value);
  y.value = 4200; y.dispatchEvent(new fw.Event('input', { bubbles: true }));
  ok('연소득 4,200 → 월 350', fw.eval('state.subs.me.a.income') === 350 && d.querySelector('[data-me="a.income"]').value === '350', fw.eval('state.subs.me.a.income'));
  set('b.income', 300); set('nw.married', '2024-06-01'); set('nw.homeless', '1'); set('nw.asset', 20000); set('live.city', '서울'); set('live.gu', '동작구'); await W(300);
  fw.eval('state.subs.wizard.done = true; wizOpen = false; render();'); await W(300);
  let e = fw.eval("elig(state.subs.notices[0], state.subs.me, 'newlywed', 'special')");
  ok('신혼특공 가능 · 소득 3순위(110.8%) · 지역 2순위', e.st === 'ok' && e.rankI === 3 && e.rankR === 2, JSON.stringify([e.st, e.rankI, e.rankR]));
  ok('판정 카드 표시 (근거 자세히 안)', /신혼부부 특별공급\s*가능/.test(d.querySelector('#subJudge').textContent) && /110\.8%/.test(d.querySelector('#subJudge').textContent), '');
  ok('쉬운 이유: 특공 소득 3순위 · 지역 2순위', /특별공급을 신청할 수 있어요\. 소득 3순위, 지역 2순위\(서울\)예요\./.test(d.querySelector('#subJudge .why').innerText), d.querySelector('#subJudge .why').innerText);
  // 매물로 넣기: 통근 먼저
  d.querySelector('[data-tadd="yongsan-2026-11|56"]').click(); await W(300);
  ok('통근 없이 넣으면 안내', !sub() && /통근 시간/.test(d.querySelector('#subMsg').textContent), d.querySelector('#subMsg').textContent);
  const c = d.querySelector('[data-ncommute]'); c.value = 40; c.dispatchEvent(new fw.Event('change', { bubbles: true })); await W(300);
  d.querySelector('[data-tadd="yongsan-2026-11|56"]').click(); await W(500);
  let s = sub(), es = evSub();
  ok('56형 → 특공 50% 자동 (20,000/73, 관리비 14.8)', s && s.sub.supply === 'special' && s.sub.i === 2 && s.deposit === 20000 && s.rent === 73 && s.fee === 14.8, s && JSON.stringify([s.sub, s.deposit, s.rent, s.fee]));
  ok('실제 월 부담 125.3 = 73 + 14.8 + 15,000×3%÷12', Math.abs(es.monthly - 125.3) < 1e-6, es.monthly);
  fw.location.hash = 'home'; await W(500);
  const gl = d.querySelector('#glanceHome .gl-table').innerText;
  ok('한눈에 비교: 청약 가능 배지', /청약 가능 · 신혼특공 · 소득 3순위/.test(gl) && /보증금 2억 \/ 73/.test(gl), '');
  fw.location.hash = 'subs'; await W(400);
  // 소득 720 → 특공 불가 → 일반 가격 50%
  set('b.income', 370); await W(300); s = sub(); es = evSub();
  ok('소득 720만(122.7%) → 특공 불가 · 일반 50% 23,800/86', s.sub.supply === 'general' && s.deposit === 23800 && s.rent === 86 && !es.reasons.length, JSON.stringify([s.sub, s.deposit, es.reasons]));
  ok('일반 50% 월 부담 147.8', Math.abs(es.monthly - (86 + 14.8 + 18800 * 0.03 / 12)) < 1e-6, es.monthly);
  set('b.income', 400); await W(300);
  e = fw.eval("[elig(state.subs.notices[0], state.subs.me, 'newlywed', 'special').st, elig(state.subs.notices[0], state.subs.me, 'newlywed', 'general').st]");
  ok('소득 750만 → 특공 불가 · 일반 가능 · 쉬운 이유 "월 46만원 많아서"', e.join() === 'no,ok' && /부부 소득이 기준보다 월 46만원 많아서 특별공급은 어려워요\./.test(d.querySelector('#subJudge .why').innerText) && /일반공급\(추첨\)은 신청할 수 있어요/.test(d.querySelector('#subJudge .why').innerText) && /신청할 수 있어요/.test(d.querySelector('#subJudge .sig').innerText), d.querySelector('#subJudge .why').innerText.replace(/\s+/g, ' '));
  // 소득 빈칸 → 확인 필요, 탈락 안 함
  set('b.income', ''); await W(300); es = evSub();
  ok('소득 빈칸 → 특공 확인 필요 · 탈락 안 함', es.si.sp.st === 'unk' && !es.reasons.length && /청약 (가능|확인 필요)/.test(fw.eval('subBadge(evaluate(state).all.find(l => l.sub))')), es.si.sp.st);
  set('b.income', 300);
  // 혼인 2,556일 → 특공·일반 불가 → 탈락
  set('nw.married', '2019-11-04'); await W(300); es = evSub();
  ok('혼인 2,556일 → 둘 다 불가 → "청약 자격 없음" 탈락', es.si.sp.st === 'no' && es.reasons.includes('청약 자격 없음'), es.reasons.join(','));
  set('nw.married', '2024-06-01');
  // 신청자 40세
  set('a.birth', '1986-11-03'); await W(300); es = evSub();
  ok('신청자 만 40세 → 탈락', es.reasons.includes('청약 자격 없음'), es.reasons.join(','));
  set('a.birth', '1992-05-01'); await W(300);
  // 직접 고르기 → 자금 바꿔도 유지
  d.querySelector('[data-opt$="|special|0"]').click(); d.querySelector('[data-opt$="|special|0"]').dispatchEvent(new fw.Event('change', { bubbles: true })); await W(300);
  fw.eval('state.settings.myCash = 15000; render();'); await W(300); s = sub();
  ok('직접 고른 특공 30% → 내 돈 바꿔도 유지', s.sub.auto === false && s.sub.i === 0 && s.deposit === 12000, JSON.stringify(s.sub));
  d.querySelector('[data-oauto]').click(); await W(300); s = sub();
  ok('자동 선택으로 돌리기', s.sub.auto === true, JSON.stringify(s.sub));
  fw.eval('state.settings.myCash = 5000; render();');
  // 자동차 → 주차 12
  set('hasCar', true); set('car', 2000); await W(300); s = sub();
  ok('자동차 있음 → 관리비 14.8 + 주차 12 = 26.8', s.fee === 26.8, s.fee);
  set('hasCar', false); await W(300);
  // 청년 탭
  d.querySelector('[data-subtab="youth"]').click(); await W(300);
  ok('청년으로 보기: 판정 전환 · 결혼 안내', fw.eval('state.subs.tab') === 'youth' && /청년 특별공급/.test(d.querySelector('#subJudge').textContent) && /결혼하면 청년 공급은 신청할 수 없어요/.test(d.querySelector('#subJudge').innerText), '');
  ok('혼인신고일 있음 → 청년 미혼 칸 잠김·기혼 불가', d.querySelector('[data-me="yt.single"]').disabled && fw.eval("elig(state.subs.notices[0], state.subs.me, 'youth', 'general')").st === 'no', '');
  fw.eval("state.subs.me.nw.married = ''; render();"); await W(300);
  set('yt.single', '1'); set('yt.homeless', '1'); set('yt.asset', 9000); await W(300);
  e = fw.eval("elig(state.subs.notices[0], state.subs.me, 'youth', 'special')");
  ok('청년특공 가능 (단독 350만 = 1인 91.8%)', e.st === 'ok' && e.rankI === 1, JSON.stringify([e.st, e.rankI]));
  d.querySelector('[data-tadd="yongsan-2026-11|25"]').click(); await W(500);
  const y25 = fw.eval("evaluate(state)").all.find(l => l.sub?.type === '25');
  ok('25형 매물 → 전용 22.53㎡ 40㎡ 미만 탈락', y25 && y25.reasons.some(r => /40㎡ 미만/.test(r)), y25 && y25.reasons.join(','));
  ok('두 계층 모두 넣으면 1인 1건 경고', /한 사람이 한 건만/.test(d.querySelector('#subJudge').innerText), '');
  // ics
  const ics = fw.eval('icsOf(state.subs.notices[0])');
  ok('ics: VEVENT 6개 · 접수 20261112~20261116(다음 날)', (ics.match(/BEGIN:VEVENT/g) || []).length === 6 && /DTSTART;VALUE=DATE:20261112\r\nDTEND;VALUE=DATE:20261116/.test(ics) && ics.includes('\r\n'), (ics.match(/BEGIN:VEVENT/g) || []).length);
  // 공고 JSON 고치기 · 형식 검사
  ok('공고 형식 검사 (분양·날짜 틀림 거절)', fw.eval("normNotice({ kind: '분양', noticeDate: '2026-11-03', types: [] })") === null, '');
  ok('기존 매물 그대로 (상도동 투룸 75.0)', Math.abs(L('m1').monthly - m1) < 1e-9 && Math.abs(m1 - 75) < 1e-9, m1);
  // 내보내기 개인정보 안내
  fw.URL.createObjectURL = () => 'blob:x'; fw.HTMLAnchorElement.prototype.click = function () {};
  d.querySelector('#exportBtn').click(); await W(800);
  ok('내보내기: 개인정보 안내', /개인정보/.test(d.querySelector('#ioMsg').textContent), d.querySelector('#ioMsg').textContent.slice(0, 60));
  // 직장 다른 지역: 경기 → 시·군·구 직접 입력, 지역 순위는 서울 쪽(거주지)으로
  fw.eval('state.subs.wizard.step = 6; wizOpen = true; render();'); await W(200);
  set('work.city', '경기'); await W(200);
  const wt = d.querySelector('[data-me="work.gu"][data-gu-txt]'); wt.value = '의왕시'; wt.dispatchEvent(new fw.Event('input', { bubbles: true })); await W(200);
  ok('직장 경기 의왕시 저장 · 구 칸이 직접 입력으로 · 지역 순위 그대로 2', fw.eval('JSON.stringify(state.subs.me.work)') === '{"city":"경기","gu":"의왕시"}' && !wt.hidden && d.querySelector('[data-me="work.gu"][data-gu-sel]').hidden && fw.eval("elig(state.subs.notices[0], state.subs.me, 'newlywed', 'special').rankR") === 2, fw.eval('JSON.stringify(state.subs.me.work)'));
  fw.eval('wizOpen = false; render();');
  // 예전(v10) 데이터: 우리 상황이 이미 있으면 질문을 건너뛰고 결과
  ok('예전 데이터(우리 상황 있음, wizard 없음) → 질문 끝낸 것으로', fw.eval("migrate({ listings: [], subs: { me: { a: { birth: '1992-05-01', income: 350 } } } }).subs.wizard.done") === true && fw.eval("migrate({ listings: [], subs: {} }).subs.wizard.done") === false, '');
  // 공고 추가하기: 붙여넣기 검사
  d.querySelector('#subAddBtn').click(); await W(200);
  const paste = v => { const t = d.querySelector('#subPaste'); t.value = v; t.dispatchEvent(new fw.Event('input', { bubbles: true })); };
  paste('{"kind":"임대","noticeDate":"2026-11-0'); await W(100);
  ok('붙여넣기: 끊긴 내용 → 쉬운 말 안내', !d.querySelector('#subAdd').hidden && /끊겼거나/.test(d.querySelector('#subPasteErr').innerText), d.querySelector('#subPasteErr').innerText);
  paste('```json\n{"kind":"임대","noticeDate":"2026-11-03","types":[{"id":"59","tier":"newlywed","area":59}]}\n```'); await W(100);
  ok('붙여넣기: 빈 칸 알려 줌 (가격·소득표·자격)', /주택형 59의 가격/.test(d.querySelector('#subPasteErr').innerText) && /소득 기준표/.test(d.querySelector('#subPasteErr').innerText), d.querySelector('#subPasteErr').innerText.replace(/\s+/g, ' '));
  const good = fw.eval('JSON.stringify({ ...state.subs.notices[0], id: "paste-test", short: "붙여넣기 시험" })'); paste('여기 결과예요:\n```json\n' + good + '\n```'); await W(300);
  ok('붙여넣기: 올바르면 바로 들어감', fw.eval('state.subs.notices.some(n => n.id === "paste-test")') && d.querySelector('#subAdd').hidden, fw.eval('state.subs.notices.length'));
  // 휴대폰 390
  f.remove(); f = await frame(390); d = f.contentDocument; fw = f.contentWindow;
  ok('휴대폰: 청약 화면 가로 넘침 없음', d.documentElement.scrollWidth <= 390, d.documentElement.scrollWidth);
  fw.eval('state.subs.wizard.done = false; wizOpen = false; render();'); await W(300);
  ok('휴대폰: 질문 화면 가로 넘침 없음 · 한 열', !d.querySelector('#subWiz').hidden && d.documentElement.scrollWidth <= 390 && d.querySelectorAll('.wiz-pick button')[1].getBoundingClientRect().top > d.querySelectorAll('.wiz-pick button')[0].getBoundingClientRect().bottom - 1, d.documentElement.scrollWidth);
  // 처음 온 사람: 메뉴 '청약'(1) → '예시 공고로 체험하기'(2) → 결과
  localStorage.clear(); localStorage.setItem('suitable-intro', '1'); f.remove(); f = await frame(390); d = f.contentDocument; fw = f.contentWindow;
  d.querySelector('#subSample').click(); await W(1200);
  ok('처음 온 사람: 클릭 2번으로 예시 결과 (390)', /신청할 수 있어요/.test(d.querySelector('#subJudge .sig')?.innerText || '') && d.documentElement.scrollWidth <= 390, d.documentElement.scrollWidth);
  ok('휴대폰: 탭바에 청약', [...d.querySelectorAll('.tabbar a')].some(a => a.textContent === '청약' && a.getAttribute('aria-current') === 'page'), '');
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
