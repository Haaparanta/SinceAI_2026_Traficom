// Short cut of the team's screen recording with a new narration track, captions and step labels.
// Inputs: narration_cut.json (source ranges and text) and public/cut.timed.json (voice durations and caption timing,
// written by scripts/tts.mjs --script narration_cut.json --name cut).
import { loadFont } from "@remotion/google-fonts/Nunito";
import {
  AbsoluteFill, Audio, Freeze, Img, OffthreadVideo, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig,
} from "remotion";
import script from "../narration_cut.json";
import timed from "../public/cut.timed.json";

export const FPS = 30;
const { fontFamily } = loadFont("normal", { weights: ["600", "800", "900"], subsets: ["latin"] });

const C = {
  plum: "#170a16",
  ink: "#3a0f2c",
  pink: "#fc7bb9",
  hot: "#e0408a",
  blush: "#fff0f7",
  cream: "#faeef3",
};

// Step labels for viewers without sound, and optional slow zooms (focus point in 1920x1080 source pixels).
const META: Record<string, { label: string; zoom?: { x: number; y: number; scale: number; from: number } }> = {
  hook: { label: "Filing Radar" },
  overview: { label: "Space IFIC 3074 at a glance" },
  calc: { label: "Indicative pfd check, RR Article 21", zoom: { x: 905, y: 520, scale: 1.55, from: 1.2 } },
  map: { label: "Findings and special-interest stations" },
  letter: { label: "Plain-language explanation and letter draft" },
  decide: { label: "The expert decides" },
  audit: { label: "Hash-chained audit log" },
  terrestrial: { label: "Terrestrial IFIC 3076, ITU-R P.1546", zoom: { x: 905, y: 520, scale: 1.55, from: 4.5 } },
  export: { label: "Light or dark, export CSV and JSON" },
  close: { label: "" },
};

type Seg = {
  id: string; from: number; dur: number; narr: number; audio: string;
  pages: { text: string; start: number; end: number }[];
  clip: [number, number] | null; rate: number; srcStart: number; playLen: number;
};

const GAP = 0.45;      // breath after each narration line
const MAX_RATE = 2.5;  // fastest playback of the recording

export function cutTimeline() {
  const byId = Object.fromEntries(timed.segments.map((s) => [s.id, s]));
  let t = 0;
  const segs: Seg[] = script.segments.map((s) => {
    const v = byId[s.id];
    const dur = Math.max(2.4, v.duration + GAP + (s.id === "close" ? 1.6 : 0));
    const clip = (s.clip as [number, number] | null) ?? null;
    let rate = 1, srcStart = 0, playLen = 0;
    if (clip) {
      const len = clip[1] - clip[0];
      rate = Math.min(MAX_RATE, Math.max(1, len / dur));
      playLen = Math.min(len, dur * rate);   // source seconds shown
      srcStart = clip[1] - playLen;          // keep the end of the range: it holds the result of the action
      if (len <= dur) srcStart = clip[0];
    }
    const seg = { id: s.id, from: t, dur, narr: v.duration, audio: v.file, pages: v.pages, clip, rate, srcStart, playLen };
    t += dur;
    return seg;
  });
  return { segs, total: Math.round(t * FPS) };
}

const Footage = ({ seg }: { seg: Seg }) => {
  const frame = useCurrentFrame();
  const sec = frame / FPS;
  const showFor = seg.playLen / seg.rate;          // output seconds of moving footage
  const z = META[seg.id]?.zoom;
  const drift = interpolate(frame, [0, seg.dur * FPS], [1, 1.035]);
  let scale = drift, ox = 960, oy = 540;
  if (z) {
    const p = spring({ frame: frame - z.from * FPS, fps: FPS, config: { damping: 200 }, durationInFrames: 40 });
    scale = interpolate(p, [0, 1], [drift, z.scale]);
    ox = interpolate(p, [0, 1], [960, z.x]);
    oy = interpolate(p, [0, 1], [540, z.y]);
  }
  const video = (
    <OffthreadVideo src={staticFile(script.source)} startFrom={Math.round(seg.srcStart * FPS)} playbackRate={seg.rate} muted
      style={{ width: 1920, height: 1080 }} />
  );
  return (
    <AbsoluteFill style={{ transform: `scale(${scale})`, transformOrigin: `${ox}px ${oy}px` }}>
      {sec < showFor ? video : <Freeze frame={Math.max(0, Math.floor(showFor * FPS) - 1)}>{video}</Freeze>}
    </AbsoluteFill>
  );
};

const Label = ({ text }: { text: string }) => {
  const frame = useCurrentFrame();
  const p = spring({ frame: frame - 4, fps: FPS, config: { damping: 18, stiffness: 160 } });
  if (!text) return null;
  return (
    <div style={{
      position: "absolute", top: 22, left: 24, transform: `translateY(${interpolate(p, [0, 1], [-30, 0])}px)`, opacity: p,
      fontFamily, fontWeight: 800, fontSize: 30, color: C.ink, background: C.blush, padding: "12px 26px", borderRadius: 999,
      boxShadow: "0 10px 30px rgba(224,64,138,.35)", border: `3px solid ${C.pink}`, display: "flex", alignItems: "center", gap: 14,
    }}>
      <span style={{ width: 14, height: 14, borderRadius: 99, background: C.hot, boxShadow: `0 0 12px ${C.pink}` }} />
      {text}
    </div>
  );
};

const Captions = ({ seg }: { seg: Seg }) => {
  const frame = useCurrentFrame();
  const t = frame / FPS - 0.15;
  const page = seg.pages.find((p) => t >= p.start && t < p.end) ?? (t >= 0 && t < seg.narr + 0.3 ? seg.pages.at(-1) : undefined);
  if (!page) return null;
  const local = (t - page.start) * FPS;
  const pop = spring({ frame: local, fps: FPS, config: { damping: 14, stiffness: 220 } });
  return (
    <div style={{ position: "absolute", left: 0, right: 0, bottom: 64, display: "flex", justifyContent: "center" }}>
      <div style={{
        maxWidth: 1500, textAlign: "center", fontFamily, fontWeight: 800, fontSize: 50, lineHeight: 1.18, color: C.ink,
        background: "rgba(255,240,247,0.96)", padding: "16px 38px 20px", borderRadius: 40,
        boxShadow: "0 14px 40px rgba(23,10,22,.55)", border: `4px solid ${C.pink}`,
        transform: `scale(${interpolate(pop, [0, 1], [0.92, 1])})`,
      }}>{page.text}</div>
    </div>
  );
};

const Sparkle = ({ x, y, s, d }: { x: number; y: number; s: number; d: number }) => {
  const frame = useCurrentFrame();
  const o = 0.35 + 0.65 * Math.abs(Math.sin((frame + d) / 14));
  return (
    <svg width={s} height={s} viewBox="0 0 24 24" style={{ position: "absolute", left: x, top: y, opacity: o, transform: `rotate(${frame + d}deg)` }}>
      <path d="M12 0 L14 10 L24 12 L14 14 L12 24 L10 14 L0 12 L10 10 Z" fill={C.pink} />
    </svg>
  );
};

const TitleChip = () => {
  const frame = useCurrentFrame();
  const p = spring({ frame: frame - 6, fps: FPS, config: { damping: 16 } });
  const out = interpolate(frame, [6.2 * FPS, 7 * FPS], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", opacity: out }}>
      <div style={{
        transform: `scale(${interpolate(p, [0, 1], [0.6, 1])})`, opacity: p, display: "flex", alignItems: "center", gap: 28,
        background: "rgba(23,10,22,.88)", padding: "34px 56px", borderRadius: 48, border: `4px solid ${C.pink}`,
        boxShadow: "0 30px 80px rgba(252,123,185,.35)",
      }}>
        <Img src={staticFile("logo.svg")} style={{ width: 120, height: 120, borderRadius: 28 }} />
        <div>
          <div style={{ fontFamily, fontWeight: 900, fontSize: 96, color: C.cream, letterSpacing: -2, lineHeight: 1 }}>Filing Radar</div>
          <div style={{ fontFamily, fontWeight: 700, fontSize: 34, color: C.pink, marginTop: 10 }}>ITU filings that may affect radio use in Finland</div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

const Close = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame, fps, config: { damping: 14 } });
  const p2 = spring({ frame: frame - 12, fps, config: { damping: 16 } });
  return (
    <AbsoluteFill style={{ background: `radial-gradient(circle at 50% 40%, #3b1233 0%, ${C.plum} 70%)`, justifyContent: "center", alignItems: "center" }}>
      <AbsoluteFill style={{ backgroundImage: `url(${staticFile("mosaic.png")})`, backgroundSize: 520, opacity: 0.16 }} />
      {[[260, 220, 46, 0], [1560, 260, 34, 40], [1420, 760, 52, 80], [380, 780, 30, 20], [960, 140, 26, 60]].map(([x, y, s, d]) => <Sparkle key={x} x={x} y={y} s={s} d={d} />)}
      <div style={{ textAlign: "center", transform: `scale(${interpolate(p, [0, 1], [0.7, 1])})`, opacity: p }}>
        <Img src={staticFile("logo.svg")} style={{ width: 170, height: 170, borderRadius: 40, boxShadow: "0 20px 60px rgba(252,123,185,.45)" }} />
        <div style={{ fontFamily, fontWeight: 900, fontSize: 140, color: C.cream, letterSpacing: -3, marginTop: 26, lineHeight: 1 }}>Filing Radar</div>
        <div style={{ fontFamily, fontWeight: 800, fontSize: 52, color: C.pink, marginTop: 22, opacity: p2 }}>The tool suggests. The expert decides.</div>
        <div style={{ fontFamily, fontWeight: 700, fontSize: 38, color: C.cream, marginTop: 34, opacity: p2 }}>filingradar.click</div>
      </div>
    </AbsoluteFill>
  );
};

export const Cut = () => {
  const { segs } = cutTimeline();
  return (
    <AbsoluteFill style={{ background: C.plum }}>
      {segs.map((s) => (
        <Sequence key={s.id} from={Math.round(s.from * FPS)} durationInFrames={Math.round(s.dur * FPS)} name={s.id}>
          {s.clip ? <Footage seg={s} /> : <Close />}
          {s.id === "hook" && <TitleChip />}
          {s.clip && s.id !== "hook" && <Label text={META[s.id]?.label ?? ""} />}
          <Sequence from={Math.round(0.15 * FPS)} name={`voice ${s.id}`}>
            <Audio src={staticFile(s.audio)} />
          </Sequence>
          {s.id !== "close" && <Captions seg={s} />}
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
