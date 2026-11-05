// 자동 생성: index.html 의 AI_SPEC 블록 (직접 고치지 말고 python scripts/sync_ai_spec.py)
export const SUB_PROMPT = `첨부한 임대주택 입주자 모집공고문을 읽고, 아래 형식의 JSON 하나만 돌려줘. 설명 문장 없이 JSON만.
- 금액은 모두 만원 단위 숫자, 날짜는 'YYYY-MM-DD', 모르는 값은 null.
- kind 는 항상 "임대". tier 는 신혼부부면 "newlywed", 청년이면 "youth".
- prices 는 보증금 비율(ratios 순서)마다 [보증금, 월임대료] 짝. special = 특별공급, general = 일반공급.
- incomeBase 는 공고의 도시근로자 가구원수별 월평균소득 100% 금액(1인~5인), incomeExtra 는 6인 이상 1인당 더하는 금액.
- rules 의 incomeMax·incomeRanks 는 % 숫자, asset·car 는 만원, marriageDays 는 혼인 기간 일수(7년이면 2555), homeless 는 "세대" 또는 "본인".
{"id":"영문-숫자-아이디","kind":"임대","name":"공고 이름","short":"짧은 이름","addr":"주소","city":"서울","region":"용산구","station":"가까운 역","noticeDate":"2026-11-03","url":"공고 사이트",
 "summary":"한 줄 요약","cite":{"rules":"신청자격 쪽 번호"},
 "schedule":[{"key":"apply","label":"청약 접수","from":"2026-11-12","to":"2026-11-15"}],
 "ratios":[30,40,50],"contractPct":10,"parking":12,"incomeBase":[381.3,586.6,816.8,880.2,932.7],"incomeExtra":57.9,
 "rules":{"newlywed":{"special":{"age":[19,39],"marriageDays":2555,"preMarried":true,"homeless":"세대","incomeMax":120,"incomeRanks":[100,110,120],"asset":34500,"car":4542},"general":{"age":[19,39],"marriageDays":2555,"preMarried":true,"homeless":"세대","car":4542}},
  "youth":{"special":{"age":[19,39],"single":true,"homeless":"본인","incomeMax":120,"incomeRanks":[100,110,120],"asset":25100,"car":4542},"general":{"age":[19,39],"single":true,"homeless":"본인","car":4542}}},
 "types":[{"id":"56","tier":"newlywed","area":47.37,"rooms":2,"fee":14.8,"units":{"special":69,"general":273},"prices":{"special":[[12000,102],[16000,88],[20000,73]],"general":[[14300,121],[19000,104],[23800,86]]}}],
 "notes":["알아 둘 점"]}`;
export const LISTING_PROMPT = `아래 매물 설명 글에서 값만 뽑아 JSON 하나로 돌려줘. 설명 문장 없이 JSON만.
- 글에 없는 값은 반드시 null. 짐작하거나 지어내지 마.
- 금액은 만원 단위 숫자 (1억 2천 → 12000, '3000/70' → deposit 3000, rent 70). 전세·매매면 deposit 에 전세금·매매가를 넣고 rent 는 null.
- area 는 전용면적 ㎡ (평만 있으면 null), rooms 는 방 개수.
- floorNo 는 '해당층/총층' (예: '3/5'). basement 는 반지하·지하층이면 true, 지상층이 분명하면 false.
- usage 는 업무용 오피스텔이면 '업무용', 주거용이면 '주거용'. moveIn 은 전입신고, loan 은 전세대출 가능 여부.
- station 은 가까운 역 이름, walk 는 역까지 걸어서 몇 분.`;
const S_N = { type: 'NUMBER', nullable: true }, S_I = { type: 'INTEGER', nullable: true }, S_S = { type: 'STRING', nullable: true }, S_NA = { type: 'ARRAY', items: { type: 'NUMBER' } };
const S_E = a => ({ type: 'STRING', nullable: true, enum: a });
const S_RULE = { type: 'OBJECT', nullable: true, properties: { age: S_NA, marriageDays: S_N, preMarried: { type: 'BOOLEAN' }, single: { type: 'BOOLEAN' }, homeless: S_E(['세대', '본인']),
  incomeMax: S_N, incomeRanks: S_NA, asset: S_N, car: S_N } };
const S_TIER = { type: 'OBJECT', nullable: true, properties: { special: S_RULE, general: S_RULE } }, S_PAIRS = { type: 'ARRAY', items: S_NA };
export const NOTICE_SCHEMA = { type: 'OBJECT', required: ['kind', 'name', 'noticeDate', 'incomeBase', 'rules', 'types'], properties: {
  id: { type: 'STRING' }, kind: { type: 'STRING', enum: ['임대'] }, name: { type: 'STRING' }, short: S_S, addr: S_S, city: S_S, region: S_S, station: S_S, noticeDate: { type: 'STRING' }, url: S_S, summary: S_S,
  cite: { type: 'OBJECT', nullable: true, properties: { rules: S_S } },
  schedule: { type: 'ARRAY', items: { type: 'OBJECT', properties: { key: { type: 'STRING' }, label: { type: 'STRING' }, from: { type: 'STRING' }, to: { type: 'STRING' } } } },
  ratios: S_NA, contractPct: S_N, parking: S_N, incomeBase: S_NA, incomeExtra: S_N,
  rules: { type: 'OBJECT', properties: { newlywed: S_TIER, youth: S_TIER } },
  types: { type: 'ARRAY', items: { type: 'OBJECT', properties: { id: { type: 'STRING' }, tier: { type: 'STRING', enum: ['newlywed', 'youth'] }, area: { type: 'NUMBER' }, rooms: S_N, fee: S_N,
    units: { type: 'OBJECT', properties: { special: S_N, general: S_N } }, prices: { type: 'OBJECT', properties: { special: S_PAIRS, general: S_PAIRS } } } } },
  notes: { type: 'ARRAY', items: { type: 'STRING' } } } };
export const LISTING_SCHEMA = { type: 'OBJECT', properties: { deal: S_E(['월세', '전세', '매매']), deposit: S_N, rent: S_N, fee: S_N, area: S_N, rooms: S_I, floorNo: S_S, basement: { type: 'BOOLEAN', nullable: true },
  usage: S_E(['주거용', '업무용']), station: S_S, walk: S_I, moveIn: S_E(['가능', '불가']), loan: S_E(['가능', '불가']) } };
