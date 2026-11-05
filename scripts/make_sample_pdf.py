"""시연용 예시 공고 PDF 만들기: samples/notice_yongsan.json 내용으로 samples/notice_example.pdf (실제 공고 아님).
사용: python scripts/make_sample_pdf.py
"""
import json, subprocess, tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
n = json.loads((REPO / "samples" / "notice_yongsan.json").read_text(encoding="utf-8"))["notice"]
won = lambda v: f"{v:,}만원"
rows = "".join(f"<tr><td>{t['id']}형</td><td>{'신혼부부' if t['tier'] == 'newlywed' else '청년'}</td><td>{t['area']}㎡</td><td>{t['rooms']}</td><td>{t['units']['special']} / {t['units']['general']}</td><td>{t['fee']}만원</td>"
               + "".join(f"<td>{won(p[0])} / {p[1]}만원</td>" for p in t['prices']['special']) + "</tr>"
               + f"<tr class=g><td colspan=6>일반공급 가격</td>" + "".join(f"<td>{won(p[0])} / {p[1]}만원</td>" for p in t['prices']['general']) + "</tr>" for t in n["types"])
sch = "".join(f"<tr><td>{e['label']}</td><td>{e['from']} ~ {e['to']}</td></tr>" for e in n["schedule"])
inc = "".join(f"<td>{v:,.1f}만원</td>" for v in n["incomeBase"])
def rule(r, who):
    return (f"<li>나이 만 {r['age'][0]}~{r['age'][1]}세" + (f", 혼인 {r['marriageDays'] // 365}년 이내(예비 신혼부부 포함)" if r.get('marriageDays') else '') + (", 미혼" if r.get('single') else '')
            + f", 무주택({r['homeless']})" + (f", 소득 {r['incomeMax']}% 이하 (순위 {'/'.join(map(str, r['incomeRanks']))}%)" if r.get('incomeMax') else '')
            + (f", 총자산 {won(r['asset'])} 이하" if r.get('asset') else '') + f", 자동차 {won(r['car'])} 이하 — {who}</li>")
rules = "".join(rule(n['rules'][t][s], f"{'신혼부부' if t == 'newlywed' else '청년'} {'특별' if s == 'special' else '일반'}공급") for t in ('newlywed', 'youth') for s in ('special', 'general'))
html = f"""<!doctype html><meta charset="utf-8"><style>body{{font:12px/1.6 'Malgun Gothic',sans-serif;margin:24px}} h1{{font-size:20px}} table{{border-collapse:collapse;width:100%;margin:8px 0}} td,th{{border:1px solid #999;padding:4px}} .g td{{color:#555}} .w{{color:#b00;font-weight:700}}</style>
<p class=w>시연용 예시 공고 · 실제 모집공고가 아니에요 (SUITABLE HOME 시험용)</p>
<h1>{n['name']} 입주자 모집공고</h1><p>공고일 {n['noticeDate']} · 위치 {n['addr']} · 가까운 역 {n['station']} · 문의 {n['url']}</p>
<h2>1. 공급 일정</h2><table>{sch}</table>
<h2>2. 신청 자격 (3쪽)</h2><ul>{rules}</ul>
<h2>3. 소득 기준 — 도시근로자 가구원수별 월평균소득 100%</h2><table><tr><th>1인</th><th>2인</th><th>3인</th><th>4인</th><th>5인</th></tr><tr>{inc}</tr></table><p>6인 이상은 1인당 {n['incomeExtra']:.1f}만원을 더함.</p>
<h2>4. 주택형·임대 조건 (보증금 비율 {'/'.join(map(str, n['ratios']))}%, 보증금 / 월임대료, 계약금 보증금의 {n['contractPct']}%)</h2>
<table><tr><th>주택형</th><th>대상</th><th>전용</th><th>방</th><th>특별/일반 호수</th><th>관리비</th>{''.join(f'<th>특별공급 {r}%</th>' for r in n['ratios'])}</tr>{rows}</table>
<h2>5. 알아 둘 점</h2><ul>{''.join(f'<li>{x}</li>' for x in n['notes'])}</ul>"""
with tempfile.TemporaryDirectory() as d:
    src = Path(d) / "n.html"; src.write_text(html, encoding="utf-8")
    out = REPO / "samples" / "notice_example.pdf"
    subprocess.run([CHROME, "--headless=new", f"--user-data-dir={d}/p", "--no-pdf-header-footer", f"--print-to-pdf={out}", src.as_uri()], capture_output=True, timeout=60)
print(out, out.stat().st_size)
