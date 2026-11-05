"""index.html 의 AI 지시문·응답 형식(AI_SPEC 블록)을 worker/src/spec.js 로 복사한다.
사용: python scripts/sync_ai_spec.py          (복사)
      python scripts/sync_ai_spec.py --check  (같은지 검사만, 다르면 종료 코드 1)
"""
import re, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
html = (REPO / "index.html").read_text(encoding="utf-8")
m = re.search(r"// ==== AI_SPEC 시작.*?\n(.*?)// ==== AI_SPEC 끝 ====", html, re.S)
if not m: sys.exit("index.html 에 AI_SPEC 블록이 없어요")
body = m.group(1)
for name in ("SUB_PROMPT", "LISTING_PROMPT", "NOTICE_SCHEMA", "LISTING_SCHEMA"):
    body = body.replace(f"const {name} =", f"export const {name} =")
out = "// 자동 생성: index.html 의 AI_SPEC 블록 (직접 고치지 말고 python scripts/sync_ai_spec.py)\n" + body
dst = REPO / "worker" / "src" / "spec.js"
if "--check" in sys.argv:
    same = dst.exists() and dst.read_text(encoding="utf-8") == out
    print("AI 지시문 같음" if same else "AI 지시문 다름: python scripts/sync_ai_spec.py 실행")
    sys.exit(0 if same else 1)
dst.write_text(out, encoding="utf-8", newline="\n")
print(f"썼어요: {dst}")
