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
python scripts/verify/v8_check.py                  # v8 자동 검사 (seed_v8.json)
python scripts/verify/screenshot.py after_v8_ index.html home,listings,report --seed scripts/verify/seed_v8.json
python scripts/verify/ana_shots.py sample          # 도면 분석 스크린샷
```
필요: Python 3 + Pillow(`pip install pillow`), Chrome(`C:\Program Files\Google\Chrome\Application\chrome.exe` — 경로가 다르면 각 스크립트의 `CHROME` 수정)

## 다른 노트북 세팅

1. `git clone https://github.com/DioneLee/suitable-home.git`
2. 전역 Claude 설정 복사: `setup/README.md` 참고 (`setup/claude/` → `~/.claude/`)
3. **매물 데이터는 브라우저마다 따로 저장된다.** 지금 PC 사이트에서 '매물 → 데이터 옮기기 → JSON 내보내기' → 새 노트북 사이트에서 'JSON 불러오기'
