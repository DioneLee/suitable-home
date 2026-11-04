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
  ok('예시 가족 결과 먼저 (저장 안 함 표시 · 자격 되지만 예산 넘음 노랑 + 첫 줄 예산 · 다음 할 일 D-8 11월 12일(목)부터)', /예시 가족 기준 결과예요 · 저장되지 않아요/.test(d.querySelector('#subDemo').innerText) && /신청은 할 수 있어요 · 예산은 넘어요/.test(d.querySelector('#subJudge .sig').innerText) && /^예산보다 월 30만원 많아요/.test(d.querySelector('#subJudge .why li').innerText) && /^D-8 다음 할 일: 11월 12일\(목\)부터 청약 접수/.test(nd()), nd());
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
  ok('소득 750만 → 특공 불가 · 일반 가능 · 쉬운 이유 "월 46만원 많아서"', e.join() === 'no,ok' && /부부 소득이 기준보다 월 46만원 많아서 특별공급은 어려워요\./.test(d.querySelector('#subJudge .why').innerText) && /일반공급\(추첨\)은 신청할 수 있어요/.test(d.querySelector('#subJudge .why').innerText) && /예산은 넘어요/.test(d.querySelector('#subJudge .sig').innerText) && /^예산보다/.test(d.querySelector('#subJudge .why li').innerText), d.querySelector('#subJudge .why').innerText.replace(/\s+/g, ' '));
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
  ok('청년으로 보기: 판정 전환 · 결혼 이유 한 줄 · 고치기 없음 · 신혼부부로 보기', fw.eval('state.subs.tab') === 'youth' && /청년 특별공급/.test(d.querySelector('#subJudge').textContent) && d.querySelector('#subJudge .why').innerText.trim() === '결혼한 경우 청년 공급은 신청할 수 없어요.' && !d.querySelector('#subJudge .why button') && (d.querySelector('#subJudge').innerText.match(/청년 공급은 신청할 수 없어/g) || []).length === 1 && /신혼부부로 보기/.test(d.querySelector('#subJudge').innerText), '');
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
  // 새로 올라온 공고(feed): 없으면 숨김 · 예시 형식이면 마감 안 지난 것만 · 위험한 링크 거름
  const fd = d.querySelector('#subFeed'), noFeed = fd.hidden || (await fetch('/feed/notices.json')).ok;   // 진짜 feed 가 있으면 보이는 게 맞다
  const ex = await (await fetch('/samples/feed_example.json')).json(); ex.items.push({ title: '지난 공고', to: '2026-11-01' }, { title: '나쁜 링크', url: 'javascript:alert(1)', to: '2026-12-01' });
  fw.eval('setFeed')(ex); await W(100);
  ok('새로 올라온 공고: feed 없으면 숨김 · 있으면 표시(지난 공고 빼고, D-day, 새 공고, javascript 링크 없음) · 공고 보러 가기 링크 4개', noFeed && !fd.hidden && fd.querySelectorAll('li').length === 3 && /행복주택 입주자 모집공고/.test(fd.innerText) && /새 공고/.test(fd.innerText) && /D-6/.test(fd.innerText) && !fd.innerHTML.includes('javascript:') && d.querySelectorAll('.sub-go a').length === 4, fd.innerText.replace(/\s+/g, ' ').slice(0, 200));
  // v21: aside 시험 피드 (fixtures/feed_test.json) — 긴 기관 이름 · 오늘 마감 · 8개 넘으면 더 보기
  const ft = await (await fetch('/scripts/verify/fixtures/feed_test.json')).json();
  fw.eval('setFeed')(ft); await W(100);
  const orgs = [...fd.querySelectorAll('.org')], lng = orgs.find(o => o.title === '한국자산관리공사(긴이름)'), lefts = [...fd.querySelectorAll('li')].map(li => li.children[li.querySelector('.new') ? 2 : 1].getBoundingClientRect().left);
  ok('v21-1 기관 칸: 긴 이름 말줄임 + title 전체 · 제목 시작 위치 같음', lng && lng.scrollWidth > lng.clientWidth && getComputedStyle(lng).textOverflow === 'ellipsis' && new Set(orgs.map(o => Math.round(o.getBoundingClientRect().width))).size === 1, lng && [lng.title, lng.scrollWidth, lng.clientWidth, orgs.map(o => Math.round(o.getBoundingClientRect().width))].join(' '));
  const today = [...fd.querySelectorAll('li')].find(li => /오늘 마감 공고/.test(li.textContent));
  ok('v21-2 마감일 = 오늘 → "오늘 마감"(경고색) · 다른 줄은 D-n 그대로', today && today.querySelector('.dd').textContent === '오늘 마감' && /D-\d+/.test(fd.textContent) && !/진행 중/.test(today.textContent), today && today.querySelector('.dd')?.textContent);
  ft.items.push(...[1, 2, 3, 4].map(k => ({ id: 'more' + k, org: 'LH', title: '추가 공고 ' + k, to: '2026-12-0' + k })));
  fw.eval('setFeed')(ft); await W(100);
  const mb = fd.querySelector('[data-feedmore]'), n8 = fd.querySelectorAll('li').length;
  mb?.click(); await W(100);
  const tos = [...fd.querySelectorAll('li')].map(li => li.querySelector('.dd')?.textContent || '');
  ok('v21-6 공고 10개 → 8개 + "공고 2개 더 보기" → 누르면 10개 (마감 가까운 순 유지)', n8 === 8 && mb && mb.textContent === '공고 2개 더 보기' && fd.querySelectorAll('li').length === 10 && !fd.querySelector('[data-feedmore]') && tos[0] === '오늘 마감' && /추가 공고 4/.test(fd.querySelectorAll('li')[8].textContent) && /기간 없는/.test(fd.querySelectorAll('li')[9].textContent), [n8, mb?.textContent, fd.querySelectorAll('li').length, tos.join('|')].join(' '));
  // v21-4: 청년 전용 공고를 신혼부부로 보면 '모집 없음'
  const yj = await (await fetch('/scripts/verify/fixtures/test_notice_youth.json')).text();
  d.querySelector('#subAddBtn').click(); await W(200); paste(yj); await W(300); const tab0 = fw.eval('state.subs.tab'); fw.eval("state.subs.tab = 'newlywed'; render();"); await W(200);
  const yc = d.querySelector('#subJudge .sub-main'), ypick = [...d.querySelectorAll('#subJudge .sub-pick')].find(p => /사당/.test(p.textContent));
  ok('v21-4 청년 전용 공고 · 신혼부부로 보기 → "신혼부부 모집 없음" · "이 공고는 신혼부부를 모집하지 않아요"', fw.eval('state.subs.tab') === 'newlywed' && ypick && /신혼부부 모집 없음/.test(ypick.textContent) && /이 공고는 신혼부부를 모집하지 않아요/.test(yc.textContent), [fw.eval('state.subs.tab'), yc.querySelector('.sub-kind')?.textContent, ypick?.textContent].join(' / '));
  fw.eval("state.subs.notices.push({ ...structuredClone(state.subs.notices.find(n => n.id === 'test-youth-sadang-2026-11')), id: 'nw-only', short: '신혼 전용 시험', types: state.subs.notices[0].types.filter(t => t.tier === 'newlywed') }); state.subs.sel = 'nw-only'; state.subs.tab = 'youth'; render();"); await W(300);
  ok('v21-4 청년으로 보기 → "청년 모집 없음" · "이 공고는 청년을 모집하지 않아요"', /이 공고는 청년을 모집하지 않아요/.test(d.querySelector('#subJudge .sub-main').textContent) && [...d.querySelectorAll('#subJudge .sub-pick')].some(p => /청년 모집 없음/.test(p.textContent)), d.querySelector('#subJudge .sub-main .sig')?.textContent);
  fw.eval(`state.subs.notices = state.subs.notices.filter(n => n.id !== 'nw-only' && n.id !== 'test-youth-sadang-2026-11'); state.subs.tab = '${tab0}'; state.subs.sel = 'paste-test'; render();`); await W(300);
  // v21-5: 내 돈이 필요한 돈보다 많으면 "X 중 Y 사용"
  const cb = d.createElement('div'); cb.innerHTML = fw.eval("loanBox('t5', 4000, false, '', '')"); d.querySelector('#subJudge').append(cb); fw.eval('paintLoans()');
  const myc = fw.eval('state.settings.myCash');
  ok('v21-5 내 돈 5,000 > 보증금 4,000 → "내 돈 5,000만원 중 4,000만원 사용" · 막대는 4,000만큼', myc === 5000 && cb.querySelector('.loan-legend .c').textContent === '내 돈 5,000만원 중 4,000만원 사용' && cb.querySelector('.loan-bar i').style.width === '100%', myc + ' ' + cb.querySelector('.loan-legend .c').textContent);
  cb.remove();
  // B2: 자녀 수를 0으로 쓰면 태아 체크 풀림
  fw.eval("state.subs.me.nw.fetus = true; state.subs.me.nw.kids = 1; render();"); await W(100);
  { const k = d.querySelector('[data-me="nw.kids"]'); k.value = 0; k.dispatchEvent(new fw.Event('input', { bubbles: true })); await W(100); }
  ok('자녀 수 0 입력 → 태아 체크 풀림', fw.eval('state.subs.me.nw.fetus') === false && fw.eval('state.subs.me.nw.kids') === 0, fw.eval('JSON.stringify(state.subs.me.nw)'));
  // 공고 둘: 왼쪽 목록 · 새로 넣은 공고가 골라짐 · 눌러서 바꾸기 · 제목 띠
  const head = () => d.querySelector('#subJudge .sub-main .sub-head h3')?.textContent, picks = () => [...d.querySelectorAll('#subJudge .sub-pick')];
  ok('공고 2개 → 목록 2장 · 새 공고가 골라져 제목 띠에 표시', picks().length === 2 && head() === '붙여넣기 시험' && picks()[1].getAttribute('aria-current') === 'true' && d.querySelectorAll('#subJudge .sub-main .easy-card').length === 1, head());
  picks()[0].click(); await W(300);
  const hd = d.querySelector('#subJudge .sub-head');
  ok('목록에서 원효로 누르면 그 공고 · 제목 띠(청약 종류 · 이름 · 구·일정)', head() === '원효로 청년안심주택' && fw.eval('state.subs.sel') === 'yongsan-2026-11' && /청약 · 임대/.test(hd.querySelector('.sub-kind').textContent) && /용산구/.test(hd.querySelector('.sub-meta').textContent) && /D-8 청약 접수/.test(hd.querySelector('.sub-meta').textContent), hd.innerText.replace(/\s+/g, ' '));
  ok('제목 글자 26px', getComputedStyle(hd.querySelector('h3')).fontSize === '26px', getComputedStyle(hd.querySelector('h3')).fontSize);
  // 휴대폰 390
  f.remove(); f = await frame(390); d = f.contentDocument; fw = f.contentWindow;
  ok('휴대폰: 청약 화면 가로 넘침 없음', d.documentElement.scrollWidth <= 390, d.documentElement.scrollWidth);
  fw.eval('setFeed')(await (await fetch('/scripts/verify/fixtures/feed_test.json')).json()); await W(100);
  { const dt = d.querySelector('#subFeed h3 small .d'); ok('v21-3 휴대폰: "2026-11-04 확인" 한 줄 (안 쪼개짐) · 가로 넘침 없음', dt && dt.getClientRects().length === 1 && dt.textContent === '2026-11-04 확인' && d.documentElement.scrollWidth <= 390, dt && [dt.getClientRects().length, d.documentElement.scrollWidth].join(' ')); }
  fw.eval('state.subs.wizard.done = false; wizOpen = false; render();'); await W(300);
  ok('휴대폰: 질문 화면 가로 넘침 없음 · 한 열', !d.querySelector('#subWiz').hidden && d.documentElement.scrollWidth <= 390 && d.querySelectorAll('.wiz-pick button')[1].getBoundingClientRect().top > d.querySelectorAll('.wiz-pick button')[0].getBoundingClientRect().bottom - 1, d.documentElement.scrollWidth);
  // 처음 온 사람: 메뉴 '청약'(1) → '예시 공고로 체험하기'(2) → 결과
  localStorage.clear(); localStorage.setItem('suitable-intro', '1'); f.remove(); f = await frame(390); d = f.contentDocument; fw = f.contentWindow;
  d.querySelector('#subSample').click(); await W(1200);
  ok('처음 온 사람: 클릭 2번으로 예시 결과 (390)', /신청은 할 수 있어요/.test(d.querySelector('#subJudge .sig')?.innerText || '') && d.documentElement.scrollWidth <= 390, d.documentElement.scrollWidth);
  ok('휴대폰: 탭바에 청약', [...d.querySelectorAll('.tabbar a')].some(a => a.textContent === '청약' && a.getAttribute('aria-current') === 'page'), '');
  // 처음 사용자 흐름: 예시 → 우리 상황 입력하기 → 7단계를 '다음'으로만 한 칸씩 → 결과
  d.querySelector('#subDemoExit').click(); await W(300);
  const cnt = () => d.querySelector('#wizCount').textContent.split(' · ')[0], seen = [cnt()];
  const typ = (sel, v) => { const el = d.querySelector(sel); el.value = v; el.dispatchEvent(new fw.Event('input', { bubbles: true })); };
  d.querySelector('[data-wtier="newlywed"]').click(); await W(200); seen.push(cnt());   // 고르기만 → 그대로 1/7
  const next = async () => { d.querySelector('#wizNext').click(); await W(200); seen.push(cnt()); };
  await next(); typ('[data-me="a.birth"]', '1992-05-01'); typ('[data-me="b.birth"]', '1993-02-01');
  const age = d.querySelector('[data-age="a.birth"]').textContent;
  await next(); typ('[data-me="nw.married"]', '2024-06-01');
  const chk = (sel, v) => { const el = d.querySelector(sel); el.checked = v; el.dispatchEvent(new fw.Event('input', { bubbles: true })); };
  chk('[data-me="nw.pre"]', true); await W(150);
  ok('결혼 예정 체크 → 혼인신고일 비우고 잠금', fw.eval('state.subs.me.nw.married') === '' && d.querySelector('[data-me="nw.married"]').disabled && d.querySelector('[data-me="nw.married"]').value === '', fw.eval('JSON.stringify(state.subs.me.nw)'));
  chk('[data-me="nw.pre"]', false); await W(150); typ('[data-me="nw.married"]', '2024-06-01');
  chk('[data-me="nw.fetus"]', true); await W(150);
  const kids1 = d.querySelector('[data-me="nw.kids"]').value, hh3 = fw.eval("(() => { const m = structuredClone(state.subs.me); m.a.income = 350; m.b.income = 300; return elig(state.subs.notices[0], m, 'newlywed', 'special').checks.find(c => c.k === 'income').t; })()");
  chk('[data-me="nw.fetus"]', false); await W(150);
  ok('태아 체크 → 자녀 수 칸 1 (가구원 3인) · 풀면 0', kids1 === '1' && /3인 기준/.test(hh3) && d.querySelector('[data-me="nw.kids"]').value === '0', kids1 + ' ' + hh3);
  ok('예전 저장값: 태아 체크·자녀 0 → 자녀 1로 한 번만 옮김', fw.eval("migrate({ listings: [], subs: { me: { nw: { fetus: true, kids: 0 } } } }).subs.me.nw.kids") === 1 && fw.eval("migrate(migrate({ listings: [], subs: { me: { nw: { fetus: true, kids: 0 } } } })).subs.me.nw.kids") === 1, '');
  await next(); typ('[data-me="nw.homeless"]', '1');
  await next(); typ('[data-year-for="a.income"]', 4200); typ('[data-year-for="b.income"]', 3600);
  const mon = d.querySelector('[data-won="a.income"]').textContent;
  await next(); typ('[data-me="nw.asset"]', 20000);
  await next(); typ('[data-me="live.city"]', '서울'); await W(100); typ('[data-me="live.gu"][data-gu-sel]', '동작구');
  ok('7단계를 한 칸씩 (선택만으로 안 넘어감)', seen.join(',') === '1 / 7,1 / 7,2 / 7,3 / 7,4 / 7,5 / 7,6 / 7,7 / 7' && age === '만 34세 (공고일 기준)' && mon === '월 350만원', seen.join(',') + ' ' + age + ' ' + mon);
  d.querySelector('#wizNext').click(); await W(300);
  e = fw.eval("elig(state.subs.notices[0], state.subs.me, 'newlywed', 'special')");
  ok('결과 보기 → 650만 특공 가능 · 3순위 · 지역 2순위 (예산 95 넘어 노랑)', d.querySelector('#subWiz').hidden && e.st === 'ok' && e.rankI === 3 && e.rankR === 2 && /예산은 넘어요/.test(d.querySelector('#subJudge .sig').innerText), JSON.stringify([e.st, e.rankI, e.rankR]));
  fw.eval('state.settings.budget = 140; state.settings.depMax = 25000; render();'); await W(300);
  ok('예산 안이면 초록 "신청할 수 있어요"', d.querySelector('#subJudge .sig').innerText === '신청할 수 있어요' && d.querySelector('#subJudge .sig').classList.contains('ok'), d.querySelector('#subJudge .sig').innerText);
  const wa = d.querySelector('[data-workaddr]'), kk = d.querySelector('[data-kakao]');
  const kOff = kk.disabled;
  wa.value = '서울 영등포구 여의대로 108'; wa.dispatchEvent(new fw.Event('input', { bubbles: true })); wa.dispatchEvent(new fw.Event('change', { bubbles: true })); await W(300);
  // 위치 검색·새 탭은 가짜로: 단지 주소는 찾고, 회사 주소는 '번지'를 빼야 찾히는 경우
  const asked = [], opened = { href: '' }; const realFetch = fw.fetch, realOpen = fw.open;
  fw.fetch = async u => { const q = new URL(u).searchParams.get('q'); asked.push(q); return { ok: true, json: async () => q === '서울 영등포구 여의대로' ? [{ lat: '37.52', lon: '126.92' }] : q.includes('효창원로') ? [{ lat: '37.54', lon: '126.96' }] : [] }; };
  fw.open = () => ({ set opener(v) {}, location: opened });
  d.querySelector('[data-kakao]').click(); await W(2500);
  const k2 = decodeURIComponent(opened.href);
  ok('회사 주소 → 좌표 찾아 카카오맵 대중교통 길찾기 (번지 빼고 재검색) · 기억', kOff && k2.startsWith('https://map.kakao.com/link/by/traffic/') && k2.includes(fw.eval('state.subs.notices[0].addr').replace(/,/g, ' ') + ',37.54,126.96/서울 영등포구 여의대로 108,37.52,126.92') && asked.includes('서울 영등포구 여의대로') && fw.eval('state.subs.workAddr') === '서울 영등포구 여의대로 108', k2 + ' | ' + asked.join(' / '));
  fw.eval("state.subs.workAddr = '없는 주소 999'; delete state.geo['없는 주소 999']; render();"); await W(200); opened.href = '';
  d.querySelector('[data-kakao]').click(); await W(3000);
  ok('좌표를 못 찾으면 구글지도 대중교통 길찾기 + 안내', opened.href.startsWith('https://www.google.com/maps/dir/?api=1&origin=') && opened.href.includes('travelmode=transit') && /구글지도/.test(d.querySelector('[data-kakaomsg]').textContent), opened.href);
  fw.fetch = realFetch; fw.open = realOpen;
  const cl = d.querySelector('[data-ncommute]').closest('label');
  ok('통근 칸: 라벨 · 예: 50 · 분', /이 단지에서 직장까지 편도 몇 분인가요\?/.test(cl.innerText) && /비교 매물로 넣을 때만 필요해요/.test(cl.innerText) && cl.querySelector('input').placeholder === '예: 50' && cl.querySelector('.with-unit span').textContent === '분', cl.innerText.replace(/\s+/g, ' '));
  // 대출 계산기 (청약 = 빌릴 비율 80% 기본, 매매 = 지역 LTV)
  const lbx = d.querySelector('#subJudge .fit-home .loan'), lmsg = () => lbx.querySelector('.loan-msg').textContent;
  const m0 = lmsg(); const rg = lbx.querySelector('[data-loanpct]'); rg.value = 50; rg.dispatchEvent(new fw.Event('input', { bubbles: true }));
  ok('청약 돈 계산: 보증금 2억 · 내 돈 5천 → 80% 채움 · 50%면 5천 모자람(빨강)', /부족한 1억 5,000만원을 빌려서 채울 수 있어요/.test(m0) && /50%로는 5,000만원이 더 모자라요/.test(lmsg()) && lbx.querySelector('.loan-msg').classList.contains('bad') && /모자란 돈 5,000만원/.test(lbx.innerText), m0 + ' / ' + lmsg());
  const tb = d.createElement('div'); tb.innerHTML = fw.eval("loanBox('t', 70000, true, 'reg', '')"); d.querySelector('#subJudge').append(tb); fw.eval('paintLoans()');
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
  ok('처음 흐름 390: 가로 넘침 없음', d.documentElement.scrollWidth <= 390, d.documentElement.scrollWidth);
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
