# AI 읽기 중계 (Cloudflare Worker)

공고 PDF·매물 글을 Gemini로 읽는 중계 서버예요. 받는 요청은 `POST /notice`(PDF base64, 5MB까지)와 `POST /listing`(글, 5,000자까지) 두 가지뿐이고,
`https://dionelee.github.io`·`http://localhost:8766`·청약 체크 앱(`https://localhost` Android · `capacitor://localhost` iOS)에서 온 요청만 받아요. 요청 내용은 로그에 남기지 않아요.

## 배포 (무료 플랜)
1. `npx wrangler login`
2. `npx wrangler secret put GEMINI_API_KEY` → https://aistudio.google.com/apikey 에서 받은 키를 붙여넣기 (파일·커밋에 키를 적지 않기)
3. `npx wrangler deploy` → 나온 주소(예: `https://suitable-home-ai.<계정>.workers.dev`)를 `index.html` 의 `AI_WORKER` 에 넣고 커밋

- Gemini 는 홍콩 등에서 온 요청을 막는데("User location is not supported"), 한국 요청이 Cloudflare 홍콩(HKG) 서버로 갈 때가 있어요. 그래서 Gemini 호출은 미국 서부(`wnam`)에 고정한 Durable Object(`GeminiCaller`, 무료 플랜 SQLite 방식)에서 해요.
- 오류 때는 Gemini 오류 번호·사유만 `why` 로 돌려줘요 (요청 내용은 담지 않음).
- 잠시 끄기: `wrangler.toml` 의 `AI_ENABLED = "false"` 로 바꾸고 `npx wrangler deploy`
- 지시문·응답 형식은 `src/spec.js` (index.html 에서 자동 생성). 고칠 때는 index.html 의 AI_SPEC 블록을 고치고 `python scripts/sync_ai_spec.py`
- 로컬 시험용 키는 `.dev.vars` 에 (git 제외됨)
