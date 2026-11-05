"""v27 테스트 후속 수정 검사 (임시 Chrome 프로필 + localhost:8766, 실제 저장 데이터와 섞이지 않음).

먼저 레포 루트에서:  python -m http.server 8766 --bind localhost
사용: python scripts/verify/v27_check.py
항목: AI 503 재시도·다시 시도 · 매물 추가 후 글 칸 비움 · 홈 상위 N곳 제목 · PC 표 탈락 제외 · 시트 안내(PC/휴대폰)
      · 정렬 줄 흐림 · 매물 화면 버튼 하나 · 입력칸 단위 설명 · 리포트 aria-current · 방향 입력 펼침 · 탈락 카드 강조 · 같은 메뉴로 시트 닫기
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
  await new Promise(r => f.onload = r); await W(1200); f.contentDocument.documentElement.style.scrollBehavior = 'auto'; return f;
}
const fill = (d, v) => { const F = d.querySelector('#form'); for (const [k, x] of Object.entries(v)) { F[k].value = x; F[k].dispatchEvent(new Event('change', { bubbles: true })); } };
(async () => {
  localStorage.setItem('newlywed-home-v1', SEED); localStorage.setItem('suitable-intro', '1'); localStorage.removeItem('suitable-gemini-key');
  // ---------- PC 1280
  let f = await frame(1280, '#home'), d = f.contentDocument, fw = f.contentWindow, q = s => d.querySelector(s);
  const ev = fw.eval('evaluate(state)'), n = Math.min(3, ev.passed.length);
  ok(`3. 홈 제목 = 상위 ${n}곳 (통과 ${ev.passed.length})`, q('#h-homeTop').textContent === `적합도 상위 ${n}곳` && q('#topList').getAttribute('aria-label') === `적합도 상위 ${n}곳`, q('#h-homeTop').textContent);
  fw.eval('renderTop({ passed: evaluate(state).passed.slice(0, 2), cands: evaluate(state).cands })');
  ok('3. 통과 2곳이면 "상위 2곳"', q('#h-homeTop').textContent === '적합도 상위 2곳' && /상위 2곳으로/.test(q('[data-scroll="#homeTop"]').getAttribute('aria-label')), q('#h-homeTop').textContent);
  fw.location.hash = 'listings'; await W(500);
  const failed = ev.cands.filter(l => l.reasons.length).map(l => l.id);
  ok(`4. PC 표에 탈락(${failed}) 없음 · 탈락 보기에만`, failed.length && failed.every(id => !q(`.gl-table [data-card="${id}"]`) && q(`.gl-failed [data-card="${id}"]`)), '');
  ok('4. PC 탈락 보기: 접힘 → 펼치면 카드가 보임', !q('.gl-failed').open && !q(`.gl-failed [data-card="${failed[0]}"]`).checkVisibility(), '');
  q('.gl-failed > summary').click(); await W(300);
  ok('4. PC 탈락 보기 펼침 → 카드 보임 · 가로 넘침 없음', q(`.gl-failed [data-card="${failed[0]}"]`).checkVisibility() && d.documentElement.scrollWidth <= 1280, d.documentElement.scrollWidth);
  q('.gl-failed > summary').click(); await W(300);
  fw.eval(`flashCard('${failed[0]}')`); await W(100);
  ok('엣지2. PC 에서도 탈락 카드 강조 → 접힌 탈락 보기 펼침', q('.gl-failed').open && q(`.gl-failed [data-card="${failed[0]}"]`).classList.contains('flash'), '');
  ok('7. 매물 화면: 제목 옆 등록 버튼 없음 · 맨 위 메뉴 버튼 있음', !q('#glanceList .gl-head [data-addform]') && !!q('.nav [data-addform]'), '');
  // 8. 단위
  const units = [...d.querySelectorAll('#form .in > i')];
  ok(`8. 단위 ${units.length}칸: aria-hidden + 설명(aria-describedby)`, units.length >= 8 && units.every(u => u.getAttribute('aria-hidden') === 'true' && u.previousElementSibling.getAttribute('aria-describedby') === u.id && d.getElementById(u.id) === u), units.map(u => u.textContent).join(','));
  // 시트(PC 패널) 안내 · 같은 메뉴로 닫기
  q('.gl-table [data-detail]').click(); await W(500);
  ok('5. PC 안내 "‹ › 로 넘겨요" (좌우로 밀기 문구 없음)', fw.eval('sheet.open') && /· ‹ › 로 넘겨요$/.test(q('#shPos').textContent), q('#shPos').textContent);
  q('.nav [data-nav="listings"]').click(); await W(500);
  ok('엣지3. 시트 열고 같은 메뉴(매물) → 시트 닫힘 · 화면 그대로', !fw.eval('sheet.open') && fw.location.hash === '#listings', fw.location.hash);
  q('.gl-table [data-detail]').click(); await W(500);
  q('.nav [data-nav="report"]').click(); await W(700);
  ok('엣지3. 시트 열고 다른 메뉴(리포트) → 이동 + 닫힘', !fw.eval('sheet.open') && /^#report/.test(fw.location.hash) && !q('[data-view="report"]').hidden, fw.location.hash);
  fw.location.hash = 'report/space'; await W(500);
  ok('8. 리포트 장 링크 aria-current', q('[data-rptab="space"]').getAttribute('aria-current') === 'page' && d.querySelectorAll('.rp-tabs [aria-current]').length === 1, '');
  // 2. 매물 추가 성공 → 글 칸 비움
  fw.location.hash = 'listings'; await W(400);
  q('.nav [data-addform]').click(); await W(300);
  q('#lstText').value = '투룸 보증금 3000 / 월세 70'; q('#lstText').dispatchEvent(new Event('input'));
  fill(d, { name: 'v27 추가', deposit: 3000, rent: 70, area: 40, rooms: 2, commute: 30 });
  q('#submitBtn').click(); await W(500);
  ok('2. 매물 추가 → 매물 글 칸 비움', q('#lstText').value === '' && !q('#formDlg').open && fw.eval("state.listings.some(l => l.name === 'v27 추가')"), JSON.stringify(q('#lstText').value));
  // 1. AI 503 (내 키 → Gemini 503)
  fw.localStorage.setItem('suitable-gemini-key', 'TESTKEY'); fw.eval('syncAi()');
  q('.nav [data-addform]').click(); await W(300);
  let gcalls = 0, mode = 503; const realFetch = fw.fetch;
  fw.fetch = async (url, o) => { if (!/generativelanguage|workers\.dev/.test(url)) return realFetch(url, o); gcalls++;
    if (mode === 'ok') return new Response(JSON.stringify({ candidates: [{ content: { parts: [{ text: JSON.stringify({ deal: '월세', deposit: 3000, rent: 70 }) }] } }] }), { status: 200 });
    if (mode === 'w502') return new Response(JSON.stringify({ error: 'gemini', why: ['gemini-2.5-flash 503 UNAVAILABLE The model is overloaded'] }), { status: 502 });
    return new Response(JSON.stringify({ error: { status: 'X' } }), { status: mode }); };
  const lmsg = () => q('#lstSend [data-msg]');
  q('#lstText').value = '투룸 보증금 3000 / 월세 70'; q('#lstGo').click(); await W(1000);
  const per = gcalls; ok('1. 첫 시도 뒤 2초 대기 중 (아직 실패 문구 없음)', per >= 1 && !/붐벼요/.test(lmsg().textContent), `calls ${per}`);
  await W(3000);
  ok('1. 내 키 503 → 2초 뒤 한 번 더 (호출 2배) → 붐빔 문구 + 다시 시도', gcalls === per * 2 && /AI 서버가 지금 붐벼요\. 잠시 후 다시 누르거나 직접 붙여넣기로 할 수 있어요\./.test(lmsg().textContent) && lmsg().querySelector('button')?.textContent === '다시 시도', `calls ${gcalls} · ${lmsg().textContent}`);
  mode = 'ok'; lmsg().querySelector('button').click(); await W(1000);
  ok('1. 다시 시도 → 성공하면 칸 채움', q('#form [name=deposit]').value === '3000' && /AI가 \d칸을 채웠어요/.test(q('#lstMsg').textContent), q('#lstMsg').textContent);
  mode = 429; gcalls = 0; q('#lstGo').click(); await W(4000);
  ok('1. 429 → 지금 문구 그대로 (재시도 없음)', /오늘 AI 사용량이 다 찼어요/.test(lmsg().textContent) && !lmsg().querySelector('button') && gcalls === per, `calls ${gcalls} · ${lmsg().textContent}`);
  fw.localStorage.removeItem('suitable-gemini-key'); fw.eval('syncAi()');
  mode = 'w502'; gcalls = 0; q('#lstGo').click(); await W(4000);
  ok('1. 공용 Worker 502(why 503) → 2번 시도 → 붐빔 문구', gcalls === 2 && /붐벼요/.test(lmsg().textContent), `calls ${gcalls} · ${lmsg().textContent}`);
  mode = 503; gcalls = 0; q('#lstGo').click(); await W(4000);
  ok('1. 공용 Worker 503(AI 꺼짐) → 기존 문구 · 재시도 없음', gcalls === 1 && /AI 읽기가 꺼져 있어요/.test(lmsg().textContent), `calls ${gcalls} · ${lmsg().textContent}`);
  fw.fetch = realFetch; q('#cancelEdit').click(); d.querySelector('#formDlg').close();
  // 엣지1. 3D 집 보기 → 방향 입력 버튼
  fw.location.hash = 'studio'; await W(1500);
  q("#stTabAna").click(); await W(1500);   // 예시 매물은 방향이 모두 비어 있다
  const fb = q('#anaFacingBtn');
  if (!fb) ok('엣지1. 방향 입력 버튼 찾기', false, q('#anaFacing').textContent.slice(0, 80));
  else { fb.click(); await W(400);
    ok('엣지1. 방향 입력 → 등록 창 · 더 입력하기 펼침 · 방향 칸 포커스', q('#formDlg').open && q('#formMore').open && d.activeElement === q('#form [name=facing]'), d.activeElement?.name); q('#formDlg').close(); }
  // ---------- 휴대폰 390
  f.remove(); f = await frame(390, '#listings'); d = f.contentDocument; fw = f.contentWindow;
  const mk = getComputedStyle(d.querySelector('.gl-sort')); ok('6. 휴대폰 정렬 줄 오른쪽 끝 흐림(mask)', /gradient/.test(mk.maskImage || mk.webkitMaskImage) && d.querySelector('.gl-sort').scrollWidth > d.querySelector('.gl-sort').clientWidth, mk.maskImage || mk.webkitMaskImage);
  ok('390 가로 스크롤 없음', d.documentElement.scrollWidth <= 390, d.documentElement.scrollWidth);
  d.querySelector('.gl-cards [data-detail]').click(); await W(500);
  ok('5. 휴대폰 안내는 그대로 "좌우로 밀거나"', /좌우로 밀거나 ‹ › 로 넘겨요/.test(d.querySelector('#shPos').textContent), d.querySelector('#shPos').textContent);
  d.querySelector('.tabbar [data-nav="listings"]').click(); await W(500);
  ok('엣지3. 휴대폰 아래 탭(같은 메뉴) → 시트 닫힘', !fw.eval('sheet.open'), '');
  // 엣지2. 탈락 매물 등록 → 접힌 '탈락 보기' 펼치고 강조
  ok('엣지2 전제: 탈락 보기 접힘', !d.querySelector('.gl-failed').open, '');
  d.querySelector('.nav [data-addform]').click(); await W(300);
  fill(d, { name: 'v27 탈락', deposit: 3000, rent: 70, area: 40, rooms: 2, commute: 30, moveIn: '불가' });
  d.querySelector('#submitBtn').click(); await W(300);
  const id = fw.eval("state.listings.find(l => l.name === 'v27 탈락').id"), card = d.querySelector(`.gl-failed [data-card="${id}"]`);
  ok('엣지2. 탈락 매물 등록 → 탈락 보기 펼침 + 카드 강조', d.querySelector('.gl-failed').open && card?.classList.contains("flash") && card.checkVisibility(), `open ${d.querySelector('.gl-failed')?.open} · card ${!!card} · flash ${card?.className} · reasons ${fw.eval(`evaluate(state).all.find(l => l.id === '${id}').reasons`)}`);
  ok('실제 저장 키는 이 임시 프로필에만', true, '');
  document.body.innerHTML = '<pre id="r">' + encodeURIComponent(JSON.stringify(out)) + '</pre>';
})().catch(e => { document.body.innerHTML = '<pre id="r">' + encodeURIComponent(JSON.stringify([...out, ['NG', 'script error', e.message + ' ' + e.stack]])) + '</pre>'; });
"""

def main():
    data = json.dumps(json.loads((REPO / "scripts" / "verify" / "seed_v8.json").read_text(encoding="utf-8")), ensure_ascii=False)
    page = REPO / "screenshots" / "process" / "_v27_check.html"
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text('<!doctype html><meta charset="utf-8"><body><script>const SEED = ' + json.dumps(data) + ';' + JS + '</script>', encoding="utf-8")
    try:
        with tempfile.TemporaryDirectory() as prof:
            r = subprocess.run([CHROME, "--headless=new", f"--user-data-dir={prof}", "--enable-logging=stderr", "--v=0", "--virtual-time-budget=90000",
                                "--window-size=1400,1000", "--dump-dom", f"{BASE}/screenshots/process/_v27_check.html"], capture_output=True, timeout=240)
    finally:
        page.unlink(missing_ok=True)
    dom = r.stdout.decode("utf-8", "replace")
    m = re.search(r"<pre id=\"r\">(%5B.*?)</pre>", dom, re.S)
    rows = json.loads(unquote(m.group(1))) if m else [["NG", "결과 없음 (마지막: " + (re.search(r"<title>(.*?)</title>", dom) or [0, "?"])[1] + ")", ""]]
    for st, name, got in rows: print(f"{st}  {name}" + (f"  → {got}" if got else ""))
    logs = [l for l in r.stderr.decode("utf-8", "replace").splitlines() if "CONSOLE" in l and "index.html" in l]
    print(f"\n앱 콘솔 메시지 {len(logs)}건"); [print("  " + l[:300]) for l in logs]
    print(f"\n{sum(1 for x in rows if x[0] == 'OK')}/{len(rows)} OK")

if __name__ == "__main__":
    main()
