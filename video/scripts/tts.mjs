// Narration audio for every segment of a narration script (default narration_cut.json).
//
// ElevenLabs when ELEVENLABS_API_KEY is set (in the environment, video/.env or the repository .env); otherwise the
// macOS `say` voice as a placeholder with estimated word timings. Writes public/audio_<name>/<id>.mp3 and
// public/<name>.timed.json (duration, word timings and caption pages per segment).
//
//   node scripts/tts.mjs                 # every segment, reusing audio whose text and voice have not changed
//   node scripts/tts.mjs --force         # regenerate all
//   ELEVENLABS_VOICE_ID=... node scripts/tts.mjs
//   node scripts/tts.mjs --script other.json --name other   # another script: public/audio_other/, public/other.timed.json
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, writeFileSync, rmSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const argv = (name, dflt) => { const i = process.argv.indexOf(name); return i > 0 ? process.argv[i + 1] : dflt; };
const SCRIPT = argv("--script", "narration_cut.json");
const NAME = argv("--name", "cut");
const AUDIO_DIR = NAME ? `audio_${NAME}` : "audio";
const TIMED = join(ROOT, "public", NAME ? `${NAME}.timed.json` : "narration.timed.json");
const OUT = join(ROOT, "public", AUDIO_DIR);
const FORCE = process.argv.includes("--force");
mkdirSync(OUT, { recursive: true });

function readEnvFile(path) {
  if (!existsSync(path)) return {};
  const env = {};
  for (const line of readFileSync(path, "utf8").split("\n")) {
    const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$/);
    if (m) env[m[1]] = m[2].replace(/^["']|["']$/g, "");
  }
  return env;
}
const fileEnv = { ...readEnvFile(join(ROOT, "..", ".env")), ...readEnvFile(join(ROOT, ".env")) };
const KEY = process.env.ELEVENLABS_API_KEY ?? fileEnv.ELEVENLABS_API_KEY;
const script = JSON.parse(readFileSync(join(ROOT, SCRIPT), "utf8"));
// Default "Alice" (calm, neutral); a script can name its own voice, e.g. "Jessica" (young, playful) for the cut.
const VOICE = process.env.ELEVENLABS_VOICE_ID ?? fileEnv.ELEVENLABS_VOICE_ID ?? script.elevenlabs_voice_id ?? "Xb7hH8MSUJpSbSDYk0k2";
const STYLE = script.elevenlabs_style ?? 0.1;
// macOS placeholder: rate in words per minute and a pitch lift in semitones (0 = the voice as it is).
const SAY_RATE = String(script.say_rate ?? 182);
const SAY_PITCH = Number(script.say_pitch_semitones ?? 0);
const MODEL = process.env.ELEVENLABS_MODEL ?? fileEnv.ELEVENLABS_MODEL ?? "eleven_multilingual_v2";
const SAY_VOICE = process.env.SAY_VOICE ?? script.say_voice ?? "Samantha";
const provider = KEY ? "elevenlabs" : "say";

const ffmpeg = (...args) => execFileSync("npx", ["remotion", "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", ...args], { cwd: ROOT });
const duration = (file) => Number(execFileSync("npx", ["remotion", "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", file], { cwd: ROOT }).toString().trim());

const { segments } = script;
const previous = existsSync(TIMED)
  ? Object.fromEntries(JSON.parse(readFileSync(TIMED, "utf8")).segments.map((s) => [s.id, s]))
  : {};

// Words with start/end seconds, from a per-character alignment.
function wordsFromAlignment(chars, starts, ends) {
  const words = [];
  let cur = null;
  chars.forEach((c, i) => {
    if (/\s/.test(c)) { if (cur) { words.push(cur); cur = null; } return; }
    if (!cur) cur = { text: "", start: starts[i], end: ends[i] };
    cur.text += c;
    cur.end = ends[i];
  });
  if (cur) words.push(cur);
  return words;
}

// Placeholder timings: words spread over the clip in proportion to their length, with pauses after punctuation.
function estimateWords(text, total) {
  const raw = text.split(/\s+/).filter(Boolean);
  const weight = (w) => w.length + 2 + (/[.,:;!?]$/.test(w) ? 6 : 0);
  const sum = raw.reduce((a, w) => a + weight(w), 0);
  const lead = 0.05, usable = total - 0.15;
  let t = lead;
  return raw.map((w) => { const d = (weight(w) / sum) * usable; const r = { text: w, start: t, end: t + d * 0.85 }; t += d; return r; });
}

// Caption pages: the caption text cut into short lines, timed by mapping its position onto the spoken words.
function captionPages(caption, words, total) {
  const cw = caption.split(/\s+/).filter(Boolean);
  const pages = [];
  let line = [];
  const flush = () => { if (line.length) pages.push(line); line = []; };
  cw.forEach((w, i) => {
    line.push(i);
    const len = line.map((j) => cw[j]).join(" ").length;
    if (len >= 46 || (/[.:;!?]$/.test(w) && len >= 18) || (/,$/.test(w) && len >= 30)) flush();
  });
  flush();
  const at = (frac) => {
    if (!words.length) return frac * total;
    const idx = Math.min(words.length - 1, Math.floor(frac * words.length));
    return words[idx].start;
  };
  return pages.map((idxs, p) => {
    const start = at(idxs[0] / cw.length);
    const end = p + 1 < pages.length ? at(pages[p + 1][0] / cw.length) : total;
    return { text: idxs.map((j) => cw[j]).join(" "), start: Math.max(0, start - 0.05), end };
  });
}

async function elevenlabs(seg, i) {
  const body = {
    text: seg.say,
    model_id: MODEL,
    previous_text: segments[i - 1]?.say,
    next_text: segments[i + 1]?.say,
    voice_settings: { stability: 0.55, similarity_boost: 0.75, style: STYLE, use_speaker_boost: true, speed: 1.0 },
  };
  const res = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${VOICE}/with-timestamps?output_format=mp3_44100_128`, {
    method: "POST",
    headers: { "xi-api-key": KEY, "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`ElevenLabs ${res.status}: ${(await res.text()).slice(0, 300)}`);
  const j = await res.json();
  const file = join(OUT, `${seg.id}.mp3`);
  writeFileSync(file, Buffer.from(j.audio_base64, "base64"));
  const a = j.alignment ?? j.normalized_alignment;
  return { file, words: wordsFromAlignment(a.characters, a.character_start_times_seconds, a.character_end_times_seconds) };
}

function macSay(seg) {
  const aiff = join(OUT, `${seg.id}.wav`);
  const file = join(OUT, `${seg.id}.mp3`);
  execFileSync("say", ["-v", SAY_VOICE, "-r", SAY_RATE, "--file-format=WAVE", "--data-format=LEI16@44100", "-o", aiff, seg.say]);
  // Pitch lift without changing speed: resample faster, then stretch time back.
  const k = Math.pow(2, SAY_PITCH / 12);
  const af = SAY_PITCH ? ["-af", `asetrate=${Math.round(44100 * k)},aresample=44100,atempo=${(1 / k).toFixed(5)}`] : [];
  ffmpeg("-i", aiff, ...af, "-ar", "44100", "-ac", "1", "-b:a", "128k", file);
  rmSync(aiff);
  return { file, words: null };
}

const out = [];
for (const [i, seg] of segments.entries()) {
  const caption = seg.caption ?? seg.say;
  const hash = createHash("sha256").update(JSON.stringify([provider, VOICE, MODEL, STYLE, SAY_VOICE, SAY_RATE, SAY_PITCH, seg.say])).digest("hex").slice(0, 16);
  const prev = previous[seg.id];
  let words, total;
  if (!FORCE && prev?.hash === hash && existsSync(join(OUT, `${seg.id}.mp3`))) {
    ({ words, duration: total } = prev);
  } else {
    const r = provider === "elevenlabs" ? await elevenlabs(seg, i) : macSay(seg);
    total = duration(r.file);
    words = r.words ?? estimateWords(seg.say, total);
    console.log(`${seg.id}: ${total.toFixed(2)} s (${provider})`);
  }
  out.push({ id: seg.id, file: `${AUDIO_DIR}/${seg.id}.mp3`, provider, hash, duration: total, words, pages: captionPages(caption, words, total) });
}
writeFileSync(TIMED, JSON.stringify({ provider, voice: provider === "elevenlabs" ? VOICE : SAY_VOICE, segments: out }, null, 1));
const sum = out.reduce((a, s) => a + s.duration, 0);
console.log(`narration: ${out.length} segments, ${sum.toFixed(1)} s of speech, provider ${provider}`);
