// SUITABLE HOME AI 읽기 중계 (Cloudflare Worker)
// 받는 요청은 두 가지뿐: POST /notice (공고 PDF base64) · POST /listing (매물 글).
// 지시문·응답 형식은 이 안에 있고(spec.js), 요청 내용은 로그에 남기지 않는다. 키는 wrangler secret GEMINI_API_KEY.
import { SUB_PROMPT, LISTING_PROMPT, NOTICE_SCHEMA, LISTING_SCHEMA } from './spec.js';

const MODELS = ['gemini-3.6-flash', 'gemini-3.5-flash-lite'];   // index.html AI_MODELS 와 같게
// 앱(Capacitor): Android 화면 주소 https://localhost · iOS capacitor://localhost (청약 체크 앱 · 2026-11-09)
const ORIGINS = ['https://dionelee.github.io', 'https://suitable-home.pages.dev', 'https://seoul-cheongyak-check.pages.dev', 'http://localhost:8766', 'http://127.0.0.1:8766', 'https://localhost', 'capacitor://localhost'];
const MAX_PDF = 5 * 1024 * 1024, MAX_TEXT = 5000, TIMEOUT = 60000;

const cors = o => ({ 'Access-Control-Allow-Origin': o, 'Access-Control-Allow-Methods': 'POST, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type', 'Vary': 'Origin' });
const reply = (status, body, o) => new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json; charset=utf-8', ...(o ? cors(o) : {}) } });

export default {
  async fetch(req, env) {
    const origin = req.headers.get('Origin') || '';
    if (!ORIGINS.includes(origin)) return reply(403, { error: 'origin' });
    if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors(origin) });
    if (String(env.AI_ENABLED).toLowerCase() === 'false' || !env.GEMINI_API_KEY) return reply(503, { error: 'off' }, origin);
    const kind = new URL(req.url).pathname.slice(1);
    if (req.method !== 'POST' || (kind !== 'notice' && kind !== 'listing')) return reply(404, { error: 'kind' }, origin);
    const len = +req.headers.get('Content-Length') || 0, cap = kind === 'notice' ? Math.ceil(MAX_PDF * 4 / 3) + 4 : MAX_TEXT * 4;
    if (len > cap) return reply(413, { error: 'size' }, origin);
    const data = await req.text();
    let part;
    if (kind === 'notice') {
      if (data.length > cap || !/^[A-Za-z0-9+/]+={0,2}$/.test(data) || !data.startsWith('JVBER')) return reply(data.length > cap ? 413 : 400, { error: 'pdf' }, origin);   // JVBER = '%PDF' 의 base64
      part = { inline_data: { mime_type: 'application/pdf', data } };   // 해석하지 않고 그대로 넘긴다
    } else {
      if (!data.trim()) return reply(400, { error: 'empty' }, origin);
      if ([...data].length > MAX_TEXT) return reply(413, { error: 'size' }, origin);
      part = { text: data };
    }
    const [prompt, schema] = kind === 'notice' ? [SUB_PROMPT, NOTICE_SCHEMA] : [LISTING_PROMPT, LISTING_SCHEMA];
    const body = JSON.stringify({ contents: [{ role: 'user', parts: [{ text: prompt }, part] }], generationConfig: { responseMimeType: 'application/json', responseSchema: schema } });
    // Gemini 는 홍콩 등에서 온 요청을 막는다 (Worker 가 HKG 에서 돌 수 있음) → 미국 서부에 고정한 Durable Object 에서 부른다
    const r = await env.GEMINI.get(env.GEMINI.idFromName('wnam'), { locationHint: 'wnam' }).fetch('https://do/', { method: 'POST', body });
    return new Response(r.body, { status: r.status, headers: { 'Content-Type': 'application/json; charset=utf-8', ...cors(origin) } });
  },
};

export class GeminiCaller {   // Durable Object (미국 서부 고정)
  constructor(state, env) { this.env = env; }
  async fetch(req) {
    const body = await req.text(), signal = AbortSignal.timeout(TIMEOUT), why = [];   // why: Gemini 오류 번호·사유만 (요청 내용은 안 담김)
    let status = 502;
    for (const m of MODELS) {   // 기본 모델 실패하면 Flash-Lite 로 한 번만
      try {
        const r = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${m}:generateContent`, { method: 'POST', headers: { 'Content-Type': 'application/json', 'x-goog-api-key': this.env.GEMINI_API_KEY }, body, signal });
        if (!r.ok) { status = r.status === 429 ? 429 : 502; const e = (await r.json().catch(() => null))?.error; why.push(`${m} ${r.status} ${e?.status || ''} ${String(e?.message || '').slice(0, 200)}`); continue; }
        const text = (await r.json())?.candidates?.[0]?.content?.parts?.map(p => p.text || '').join('');
        if (text) return Response.json({ text, model: m });
      } catch (e) { status = signal.aborted ? 504 : 502; if (signal.aborted) break; }
    }
    return Response.json({ error: 'gemini', why }, { status });
  }
}
