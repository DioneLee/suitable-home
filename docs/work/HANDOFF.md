# 작업 인수인계 — SUITABLE HOME (2026-11-03 기준)

다른 노트북에서 이어서 작업하기 위한 메모. 새 세션은 이 파일부터 읽고 시작한다.

## 지금 상태

- 배포: https://dionelee.github.io/suitable-home/ (main 에 push 하면 GitHub Pages 가 자동 배포)
- 마지막 작업: **v8 한눈에 비교 · 거래 유형** (커밋 `1e3775d`)
  - 거래 유형 월세/전세/매매, 전입신고(불가 = 탈락), 층/총층, 통근 경로, 원문 링크(저장일 자동)
  - 자금: 주담대 연이율, 보증금·전세금 상한(기본 13000), 매매가 상한
  - 매매 원리금균등은 실제 월 부담에 원금 포함, 금액 옆에 "이자 ○만 + 원금 ○만"
  - 홈: 히어로 → 한눈에 비교 → 더 깊이 보기(최종 추천·메뉴, 펼친 상태)
  - 설계: `docs/design/한눈에비교.md` · 검사: `python scripts/verify/v8_check.py` (54/54 OK, 앱 콘솔 0건)
- 미커밋 파일·실행 중 서버 없음. 백업은 `index_v1~v8_backup.html` (v5·v7·v8 은 사용자 지정 보존본).

- v10 **청약(임대 공고)** (2026-11-04): 메뉴 '청약' · [신혼부부 | 청년] 탭 · 공고 JSON(`samples/notice_yongsan.json`) · 예비 판정 · 주택형 → 월세 매물 · 일정 D-day·.ics
  - 설계 `docs/design/청약.md` · 검사 `python scripts/verify/v10_check.py` (29항목) · 공고문 PDF·추출본은 `local-data/`(git 제외)
  - 원효로 청년안심주택 **접수 2026-11-12~15** (PC 인터넷만, 1인 1건)
- v12 수정 (2026-11-04): 새 가구는 도면 분석 공간 하나 안(침대·옷장·책상은 침실, 나머지 거실 먼저, 현관 둘레 0.8m 비움) · 칸 이름 중복 막기 · 청약 소득 "초과 · 기준 ○만" · 혼인신고일/예비신혼이면 청년 기혼 자동 · 주택형 6조합을 넣기 전에 고르고 상한 안 조합 '추천'
  - 백업 `index_v12_backup.html` · 실매물 검사 `python local-data/probe.py local-data/_t5.js 390` (git 제외)
- v14 쉬운 청약 화면 (2026-11-04): 예시 공고 체험(예시 가족, 저장 안 함) · 공고 추가 3단계(복사용 문장 + 붙여넣기 검사) · 질문 7단계 · 신호등 결과 카드 · 고급 설정에 JSON. 판정 계산 그대로
  - 백업 `index_v14_backup.html` · 검사 `v10_check.py` 69항목(v21) · 스크린샷 `screenshots/after_subs_easy_*` (결과 = seed_v10, 예시 가족 = seed_v8 + 예시 버튼, 질문 = wizard)

- 공고 피드 자동화 (2026-11-04): `feed/notices.json` = 사이트 '새로 올라온 공고'
  - 수집: jev-harness `npm run watch` (작업 스케줄러 `jev-housing-watch`, 매시간 :16) — SH 게시판·청년안심주택·마이홈포털 API·LH 분양임대공고문 API 합쳐서 씀
    - 위치 `C:\Users\LEE\.aside\u\0\sessions\2026-09-22_XLpnL10juHpcnhZn\artifacts\jev-harness` (`src/feed.js`, `src/sources/*.js`, 인증키는 그 폴더 `.env` 의 `DATA_GO_KR_KEY` — 절대 저장소·로그에 쓰지 않기)
  - 올리기: `scripts/push-feed.ps1` (작업 스케줄러 `suitable-home-feed-push`, 매일 08:30) — notices.json 만 경로 지정 커밋 후 push, 실패 시 pull/force 없이 로그만
    - 로그 `local-data\push-feed.log` (git 제외). 끄려면 작업 스케줄러에서 해당 작업 사용 안 함

- v24 AI 읽기 (2026-11-05): 공고 PDF → Gemini → 공고 JSON (기존 검사·판정 그대로) · 매물 글 → 폼 채우기('AI가 채움') · AI 설정(내 키, localStorage `suitable-gemini-key`)
  - 설계 `docs/design/AI읽기.md` · Worker `worker/` (배포는 사용자, `worker/README.md`) · 지시문은 index.html AI_SPEC 블록 → `python scripts/sync_ai_spec.py`
  - 검사 `node scripts/verify/worker_check.mjs`(14) · `python scripts/verify/ai_check.py`(32, 가짜 Gemini) · 예시 `samples/notice_example.pdf`(`scripts/make_sample_pdf.py`) · `samples/listing_texts.json`
  - 배포됨 `https://suitable-home-ai.demolee.workers.dev` (Cloudflare 계정 demolee, secret GEMINI_API_KEY = AI Studio 'Default Gemini Project' 무료 등급) · 실제 공고 PDF·매물 글 읽기 확인

- v25 화면 길이 정리 (2026-11-05): 홈은 숫자 카드 + 적합도 상위 3곳 · 매물은 한눈에 비교 하나(카드마다 자세히·수정·3D·삭제, 휴대폰 카드 접힘, 탈락 N곳 접기) · 자세히 = 매물 시트(휴대폰 아래 · PC 오른쪽 560px) · 매물 등록은 창(필수 9칸 + 더 입력하기) · 리포트 탭 `#report/cost|space|commute|fit|location` · 맨 위로 · AI 읽기 버튼 하나 + 채운 칸 테두리
  - 설계·항목 목록·길이 표 `docs/design/화면길이정리.md` · 길이 재기 `python scripts/verify/length_check.py [--page 파일]` (가상 11곳 `scripts/verify/seed_v25_11.json`)
  - v26 3D 집 보기 2단(PC 왼쪽 3D 고정 · 오른쪽 가구 추가 + 접힌 도면 보정)
  - 휴대폰 매물 16.7 → 2.6화면, 홈 11 → 2, 리포트 9.9 → 2.6(가장 긴 탭) (가상 11곳)
  - v27 (2026-11-06): 청약을 새 사이트 **청약 체크**(`../cheongyak-check`, 주소 예정 `dionelee.github.io/cheongyak-check/`)로 분리. 여기 청약 탭은 **2027-01-20(공모전 심사)까지 그대로** 두고 맨 위 안내 한 줄(`#subsMoved`)만 추가 · 백업 `index_v27_backup.html`
    - 판정 코드가 두 곳에 있음 → 청약 판정을 고치면 `cheongyak-check/scripts/verify/check.py`(판정 동등성)까지 돌리기
    - `push-feed.ps1`·jev-harness 공고 감시는 이 저장소용으로만 당분간 유지 (새 사이트는 GitHub Actions)

## 다음에 할 것 / 남은 것

- [ ] 실제 우리 상황을 청약 화면에 입력해 판정 확인 (접수 11.12 전)
- [ ] 분양 공고(가점·생애최초·중도금)는 실제 분양 공고가 생기면 공고 JSON `kind: '분양'`으로 추가

- [ ] 실제 사이트를 오래 열어 둔 **예전 버전 탭은 새로고침** (보호 코드가 없는 예전 탭은 데이터를 덮어쓸 수 있음)
- [ ] 실제 매물 11곳에 v8 새 칸 채우기: 거래 유형·전입신고·층·통근 경로·원문 링크
- [ ] (제안만 함) 도면 분석 보드: 가로로 긴 도면이면 평면 세 장을 전체 너비로 쌓는 배치
- [ ] (나중에) 통근 경로 3안 — ODsay 대중교통 API 붙이기
- [ ] (선택) Kakao 개발자 콘솔에 등록해 둔 도메인 정리 (카카오맵은 쓰지 않기로 함)
- 알려진 한계: 301호 도면을 가로 9.8m로 맞추면 세로가 4.11m(도면 3.9m)로 잡힘 / 한눈에 비교 표는 매물이 많으면 가로로 스크롤

## 작업 규칙 (요약 — 원문은 CLAUDE.md)

- 큰 작업은 `/지시서`(일곱 칸 계획 → 확인 후 작업), 수정은 `/고쳐줘` (`.claude/commands/`)
- 새 로직은 mermaid 흐름도 먼저 → 확인 → `docs/design/<기능명>.md` 저장
- 작업 전 `index.html` → `index_vN_backup.html` 백업, 색은 `design-guidelines.md` 토큰만
- **실제 저장 데이터('newlywed-home-v1')는 절대 덮어쓰지 않는다.** 테스트는 `localhost:8766` + 임시 Chrome 프로필에서만
- 사용자 네이버 평면도·301호 스크린샷은 `screenshots/process/`(git 제외)에만
- 커밋에 Claude 서명 줄을 붙이지 않는다. 커밋·푸시는 확인받고

## 검증 도구 (`scripts/verify/`)

```bash
python -m http.server 8766 --bind localhost        # 레포 루트에서, 테스트 전용 주소
python scripts/verify/v8_check.py ; python scripts/verify/v10_check.py   # 한눈에 비교·시트 / 청약 자동 검사
python scripts/verify/length_check.py              # 화면별 세로 길이 (예시 3곳 · 가상 11곳)
python scripts/verify/ai_check.py ; node scripts/verify/worker_check.mjs ; python scripts/sync_ai_spec.py --check   # AI 읽기
python scripts/verify/screenshot.py after_v8_ index.html home,listings,report --seed scripts/verify/seed_v8.json
python scripts/verify/ana_shots.py sample          # 도면 분석 스크린샷
```
필요: Python 3 + Pillow(`pip install pillow`), Chrome(`C:\Program Files\Google\Chrome\Application\chrome.exe` — 경로가 다르면 각 스크립트의 `CHROME` 수정)

## 다른 노트북 세팅

1. `git clone https://github.com/DioneLee/suitable-home.git`
2. 전역 Claude 설정: 공개 저장소에는 없다(2026-11-04 뺌). 이 PC의 `setup/`(git 제외 폴더)을 직접 옮겨서 `setup/README.md` 참고
3. **매물 데이터는 브라우저마다 따로 저장된다.** 지금 PC 사이트에서 '매물 → 데이터 옮기기 → JSON 내보내기' → 새 노트북 사이트에서 'JSON 불러오기'
