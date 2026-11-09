"""AI 읽기(Gemini) 화면 검사: 가짜 Gemini 응답으로 매물 글 칸 채우기 · 실패 처리 (공고 PDF 읽기는 2026-11-09 청약 체크로 옮김).
임시 Chrome 프로필 + localhost:8766 (실제 저장 데이터와 섞이지 않음). 실제 Gemini 는 부르지 않는다.
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
  localStorage.setItem('newlywed-home-v1', SEED); localStorage.setItem('suitable-intro', '1'); localStorage.removeItem('suitable-gemini-key');
  const texts = (await (await fetch('/samples/listing_texts.json')).json()).items;
  let f = await frame(1280, '#listings'), d = f.contentDocument, fw = f.contentWindow, q = s => d.querySelector(s);
  const vis = el => !!el && !el.hidden && el.getClientRects().length > 0, lmsg = () => q('#lstSend [data-msg]').textContent;
  const WK = fw.eval('AI_WORKER');
  ok('맨 아래 안내: Gemini 문구 (매물 글만)', /AI 읽기를 쓸 때만 매물 글을 Google Gemini로 보내요/.test(q('footer').textContent), '');
  // ---- 가짜 Gemini (키 방식)
  let calls = [], plan = [];
  let wcalls = [], wplan = [];
  fw.fetch = async (url, o) => { if (WK && url.startsWith(WK)) { wcalls.push({ url, body: o.body, headers: o.headers }); const p = wplan.shift() ?? { status: 503 };
      return new fw.Response(JSON.stringify(p.status ? { error: 'x' } : { text: p.text }), { status: p.status || 200 }); }
    if (!/generativelanguage/.test(url)) return fetch(url, o); const body = JSON.parse(o.body); calls.push({ url, body });
    const p = plan.shift() ?? { text: '{}' }; if (p.wait) return new Promise((_, rej) => o.signal.addEventListener('abort', () => rej(new DOMException('a', 'AbortError'))));
    if (p.net) throw new TypeError('net'); return new fw.Response(JSON.stringify(p.status ? { error: { message: p.msg || 'x' } } : { candidates: [{ content: { parts: [{ text: p.text }] } }] }), { status: p.status || 200 }); };
  fw.localStorage.setItem('suitable-gemini-key', 'TEST-ONLY-0000'); fw.eval('syncAi()');
  fw.location.hash = 'listings'; await W(500);
  const n0 = fw.eval('state.listings.length');
  q('[data-addform]').click(); await W(200);   // v25: 매물 등록 창
  ok('매물 글 칸: 등록 창 맨 위(필수 칸보다 위) · 보내기 안내 처음부터 · 버튼 "AI로 읽기" 하나 · AI 설정 바로가기', q('#formDlg').open && !!(q('.ai-paste').compareDocumentPosition(q('#form')) & 4) && vis(q('#lstSend')) && /이 내용만 Gemini로 보내요/.test(q('#lstSend').textContent) && q('#lstGo').textContent === 'AI로 읽기' && q('.ai-paste').querySelectorAll('button:not([hidden])').length === 1 && !!q('.ai-paste a[data-focus="#aiSet"]'), '');
  const asG = e => { const g = { ...e }; if ('floor' in e) { g.basement = e.floor === '반지하'; delete g.floor; } return g; };
  for (const [k, it] of texts.entries()) {
    fw.eval('resetForm()'); const t = q('#lstText'); t.value = it.text; t.dispatchEvent(new fw.Event('input'));
    calls = []; plan = [{ text: JSON.stringify(k === 0 ? { ...asG(it.expect), rooms: 99, deposit: -5 } : asG(it.expect)) }];
    const sentBefore = calls.length; q('#lstGo').click(); await W(500);
    const F = fw.eval('form'), got = {}; for (const key of Object.keys(it.expect)) got[key] = F[key].value;
    const want = { ...it.expect }; if (k === 0) { delete want.rooms; delete want.deposit; }
    const same = Object.entries(want).every(([key, v]) => String(got[key]) === String(v)), tags = F.querySelectorAll('.ai-filled').length;
    ok(`가상 매물 글 ${k + 1}: 누르면 보냄 · 글만 보냄 · 칸 ${Object.keys(want).length}개 채움 + 테두리 표시 ${tags}칸 · "AI가 N칸을 채웠어요" · 읽는 중 문구 지움` + (k === 0 ? ' · 범위 밖(방 99·보증금 -5)은 버림' : ''),
      sentBefore === 0 && calls.length === 1 && q('#lstMsg').textContent.startsWith(`AI가 ${Object.keys(want).length}칸을 채웠어요`) && q('#lstSend [data-msg]').textContent === '' && !F.querySelector('.ai-tag') && calls[0].body.contents[0].parts[1].text === it.text && !!calls[0].body.generationConfig.responseSchema.properties.walk && same && tags === Object.keys(want).length
      && (k > 0 || (F.rooms.value === '' && F.deposit.value === '')), JSON.stringify(got));
  }
  ok('채우기만 하고 저장 안 함', fw.eval('state.listings.length') === n0, fw.eval('state.listings.length'));
  const F = fw.eval('form'); F.area.value = 34; F.area.dispatchEvent(new fw.Event('input', { bubbles: true }));
  ok('사람이 고친 칸은 테두리 표시 지움', !F.area.classList.contains('ai-filled') && F.querySelectorAll('.ai-filled').length === Object.keys(texts[2].expect).length - 1, '');
  fw.eval('resetForm()'); ok('폼 비우면 표시도 지움', F.querySelectorAll('.ai-filled').length === 0 && q('#lstMsg').textContent === '', '');
  // ---- 실패 처리 (aiRun · 매물 글 경로로 확인, 2026-11-09 공고 PDF 읽기는 청약 체크로 옮김)
  const lgo = async ms => { q('#lstGo').click(); await W(ms); };
  { const t = q('#lstText'); t.value = texts[0].text; t.dispatchEvent(new fw.Event('input')); }
  calls = []; plan = [{ status: 500 }, { text: JSON.stringify(asG(texts[1].expect)) }]; await lgo(900);
  ok('기본 모델 실패 → Flash-Lite 로 한 번 더 → 성공', calls.length === 2 && /3\.5-flash-lite/.test(calls[1].url) && /칸을 채웠어요/.test(q('#lstMsg').textContent), calls.map(x => x.url.split('/').pop()).join(','));
  calls = []; plan = [{ status: 429 }, { status: 429 }]; await lgo(900);
  ok('429 → "오늘 AI 사용량이 다 찼어요…" (두 번만)', calls.length === 2 && /오늘 AI 사용량이 다 찼어요/.test(lmsg()), lmsg());
  calls = []; plan = [{ net: 1 }, { net: 1 }, { net: 1 }, { net: 1 }]; await lgo(2800);   // 연결 실패는 2초 뒤 한 번 더
  ok('네트워크 오류 → 2초 뒤 한 번 더 (모델 2개 × 2번) → 쉬운 말', calls.length === 4 && /AI에 연결하지 못했어요/.test(lmsg()), calls.length + ' · ' + lmsg());
  calls = []; plan = [{ status: 400, msg: 'API_KEY_INVALID' }]; await lgo(600);
  ok('키 틀림 → 다시 안 부르고 안내', calls.length === 1 && /Gemini 키가 맞지 않아요/.test(lmsg()), lmsg());
  plan = [{ wait: 1 }]; await lgo(200);
  ok('읽는 중 표시 + 취소 버튼', /읽는 중…/.test(lmsg()) && vis(q('#lstSend [data-stop]')), lmsg());
  q('#lstSend [data-stop]').click(); await W(200);
  ok('취소 → 멈춤', /취소했어요/.test(lmsg()) && !vis(q('#lstSend [data-stop]')) && vis(q('#lstGo')), lmsg());
  { const st = fw.setTimeout; fw.setTimeout = (fn, ms, ...a) => st(fn, ms === 60000 ? 300 : ms, ...a);   // 60초 제한 (시험에선 300ms)
    plan = [{ wait: 1 }]; await lgo(700); fw.setTimeout = st; }
  ok('60초 지나면 끊고 안내', /1분 안에 읽지 못했어요/.test(lmsg()), lmsg());
  fw.eval('resetForm()');
  // ---- 키는 저장 데이터·내보내기와 따로
  fw.eval('save()');
  ok('키는 newlywed-home-v1 밖 (내보내기에 안 들어감)', !/TEST-ONLY-0000/.test(fw.localStorage.getItem('newlywed-home-v1')) && !/TEST-ONLY-0000/.test(fw.eval('JSON.stringify(state)')), '');
  ok('AI 설정: 키 끝 4자리만 표시', /…0000/.test(q('#aiState').textContent) && q('#aiKey').value === '', q('#aiState').textContent);
  q('#aiKeyDel').click();
  if (!WK) {
    ok('키 지우면 다시 직접 붙여넣기', !fw.localStorage.getItem('suitable-gemini-key') && /공용 AI 서버가 없어요/.test(q('#aiState').textContent), q('#aiState').textContent);
    const t = q('#lstText'); t.value = '투룸'; calls = []; q('#lstGo').click(); await W(200); ok('키 없음: 매물 글 → 직접 적기 안내 (안 보냄)', /AI 설정에 Gemini 키를 넣으면/.test(q('#lstMsg').textContent) && calls.length === 0, q('#lstMsg').textContent);
  } else {
    ok('키 지우면 공용 Worker 로', !fw.localStorage.getItem('suitable-gemini-key') && /공용 AI 서버로 읽어요/.test(q('#aiState').textContent), q('#aiState').textContent);
    const t = q('#lstText'); t.value = texts[1].text; t.dispatchEvent(new fw.Event('input')); fw.eval('resetForm()');
    wplan = [{ text: JSON.stringify({ deal: '전세', deposit: 21000 }) }]; q('#lstGo').click(); await W(500);
    ok('Worker 경로: /listing 에 글만 (키·지시문 안 보냄) → 칸 채움', wcalls.length === 1 && wcalls[0].url === WK + '/listing' && wcalls[0].body === texts[1].text && !JSON.stringify(wcalls[0].headers).includes('goog') && fw.eval('form').deposit.value === '21000', wcalls[0] && wcalls[0].url);
    wcalls = []; wplan = [{ status: 503 }]; fw.eval('resetForm()'); { const t = q('#lstText'); t.value = texts[1].text; t.dispatchEvent(new fw.Event('input')); } await lgo(600);
    ok('Worker 꺼짐(503: 키 없음·AI_ENABLED=false) → 안내 · 다시 안 부름', wcalls.length === 1 && wcalls[0].url === WK + '/listing' && /지금은 AI 읽기가 꺼져 있어요/.test(lmsg()), lmsg());
    wplan = [{ status: 429 }]; await lgo(600);
    ok('Worker 429 → 사용량 안내', /오늘 AI 사용량이 다 찼어요/.test(lmsg()), lmsg());
  }
  // ---- 390
  f.remove(); f = await frame(390, '#listings'); d = f.contentDocument; q = s => d.querySelector(s);
  ok('390 매물 화면 가로 넘침 없음', d.documentElement.scrollWidth <= 390, d.documentElement.scrollWidth);
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
            r = subprocess.run([CHROME, "--headless=new", f"--user-data-dir={prof}", "--enable-logging=stderr", "--v=0", "--virtual-time-budget=60000",
                                "--window-size=1400,1000", "--dump-dom", f"{BASE}/screenshots/process/_ai_check.html"], capture_output=True, timeout=240)
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
