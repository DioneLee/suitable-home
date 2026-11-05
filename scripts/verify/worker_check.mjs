// Worker 검사 (Gemini 는 가짜 fetch). 사용: node scripts/verify/worker_check.mjs
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const mod = await import(pathToFileURL(path.join(root, 'worker/src/index.js'))), W = mod.default;
let calls = [], plan = [];
globalThis.fetch = async (url, o) => { calls.push({ url, body: JSON.parse(o.body) }); const s = plan.shift() ?? 200;
  return new Response(JSON.stringify(s === 200 ? { candidates: [{ content: { parts: [{ text: '{"ok":1}' }] } }] } : { error: { message: 'x' } }), { status: s }); };
let hints = [];
const env = { GEMINI_API_KEY: 'test', AI_ENABLED: 'true' }, O = 'https://dionelee.github.io';
env.GEMINI = { idFromName: n => n, get: (id, o) => { hints.push(o?.locationHint); const c = new mod.GeminiCaller(null, env); return { fetch: (u, i) => c.fetch(new Request(u, i)) }; } };   // Durable Object 흉내
const req = (p, body, o = O, m = 'POST') => new Request('https://w.dev/' + p, { method: m, body: m === 'POST' ? body : undefined, headers: o ? { Origin: o } : {} });
const pdf = Buffer.from('%PDF-1.4 test').toString('base64');
let n = 0, bad = 0; const ok = (name, c, got = '') => { n++; if (!c) bad++; console.log(`${c ? 'OK' : 'NG'}  ${name}${got !== '' ? '  → ' + got : ''}`); };
let r;
r = await W.fetch(req('notice', pdf, 'https://evil.example'), env); ok('다른 사이트 Origin 거절 403', r.status === 403, r.status);
r = await W.fetch(req('notice', pdf, null), env); ok('Origin 없음 거절 403', r.status === 403, r.status);
r = await W.fetch(req('ask', 'hi'), env); ok('정해진 두 종류 말고는 거절 404', r.status === 404 && !calls.length, r.status);
r = await W.fetch(req('notice', pdf), { ...env, AI_ENABLED: 'false' }); ok('AI_ENABLED=false → 503 (Gemini 안 부름)', r.status === 503 && !calls.length, r.status);
r = await W.fetch(req('notice', 'A'.repeat(7 * 1024 * 1024)), env); ok('PDF 5MB 넘음 413', r.status === 413 && !calls.length, r.status);
r = await W.fetch(req('notice', Buffer.from('hello').toString('base64')), env); ok('PDF 아닌 것 400', r.status === 400 && !calls.length, r.status);
r = await W.fetch(req('listing', '가'.repeat(5001)), env); ok('글 5,000자 넘음 413', r.status === 413 && !calls.length, r.status);
r = await W.fetch(req('notice', pdf), env); let c = calls.pop();
ok('Gemini 호출은 미국 서부(wnam) Durable Object 에서', hints.at(-1) === 'wnam', hints.at(-1));
ok('공고: PDF 그대로 inline_data + 지시문 + JSON 형식', r.status === 200 && c.body.contents[0].parts[1].inline_data.data === pdf && /모집공고문/.test(c.body.contents[0].parts[0].text)
  && c.body.generationConfig.responseMimeType === 'application/json' && c.body.generationConfig.responseSchema.properties.types, c.url.split('/').pop());
r = await W.fetch(req('listing', '투룸 3000/70'), env); c = calls.pop();
ok('매물 글: 글 + 매물 형식', r.status === 200 && c.body.contents[0].parts[1].text === '투룸 3000/70' && c.body.generationConfig.responseSchema.properties.walk, (await r.json()).text);
calls = []; plan = [500, 200]; r = await W.fetch(req('listing', '글'), env);
ok('기본 모델 실패 → Flash-Lite 한 번 더', r.status === 200 && calls.length === 2 && /3\.6-flash:/.test(calls[0].url) && /flash-lite:/.test(calls[1].url), calls.map(x => x.url.split('/').pop()).join(', '));
calls = []; plan = [429, 429]; r = await W.fetch(req('listing', '글'), env); ok('둘 다 한도 초과 → 429 (두 번만 부름)', r.status === 429 && calls.length === 2, r.status);
r = await W.fetch(req('notice', '', O, 'OPTIONS'), env); ok('OPTIONS 허용 사이트만 CORS', r.status === 204 && r.headers.get('Access-Control-Allow-Origin') === O, r.status);
const src = (await import('node:fs')).readFileSync(path.join(root, 'worker/src/index.js'), 'utf8');
ok('요청 내용을 로그로 안 남김 (console 없음)', !/console\./.test(src));
console.log(`\n${n - bad}/${n} OK`); process.exit(bad ? 1 : 0);
