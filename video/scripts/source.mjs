// The screen recording as the edit uses it: browser tab bar cropped off, 1920x1080, 30 fps, no audio.
//
//   node scripts/source.mjs "/path/to/2026-11-07 07-34-23.mp4"     # writes public/source.mp4 (git-ignored, about 110 MB)
//
// The crop fits a 2880x1800 Retina recording of a Safari window: 210 px off the top (tabs and address bar) and 27 px
// off each side, which leaves exactly 16:9.
import { execFileSync } from "node:child_process";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const input = process.argv[2];
if (!input) { console.error("usage: node scripts/source.mjs <recording.mp4>"); process.exit(2); }
execFileSync("npx", ["remotion", "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", input, "-an",
  "-vf", "crop=2826:1590:27:210,scale=1920:1080:flags=lanczos,format=yuv420p",
  "-fps_mode", "cfr", "-r", "30", "-c:v", "libx264", "-crf", "17", "-preset", "fast", "-g", "30", "-movflags", "+faststart",
  join(ROOT, "public", "source.mp4")], { cwd: ROOT, stdio: "inherit" });
console.log("public/source.mp4 written");
