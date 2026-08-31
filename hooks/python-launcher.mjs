import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const inputChunks = [];
for await (const chunk of process.stdin) {
  inputChunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
}
const input = Buffer.concat(inputChunks);
const scriptPath = join(dirname(fileURLToPath(import.meta.url)), "jl_lifecycle.py");
const candidates = process.platform === "win32"
  ? [
      { command: "py", prefix: ["-3"] },
      { command: "python", prefix: [] },
      { command: "python3", prefix: [] },
    ]
  : [
      { command: "python3", prefix: [] },
      { command: "python", prefix: [] },
    ];

let selected = null;
for (const candidate of candidates) {
  const probe = spawnSync(
    candidate.command,
    [
      ...candidate.prefix,
      "-X",
      "utf8",
      "-c",
      "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)",
    ],
    { shell: false, stdio: "ignore", windowsHide: true },
  );
  if (!probe.error && probe.status === 0) {
    selected = candidate;
    break;
  }
}

if (!selected) {
  process.stderr.write("JL Knowledge Base Skill requires Python 3.10 or newer.\n");
  process.exit(3);
}

const result = spawnSync(
  selected.command,
  [...selected.prefix, "-X", "utf8", scriptPath],
  {
    shell: false,
    input,
    windowsHide: true,
    maxBuffer: 1024 * 1024,
  },
);

if (result.stdout) process.stdout.write(result.stdout);
if (result.stderr) process.stderr.write(result.stderr);
if (result.error) {
  process.stderr.write(`${result.error.message}\n`);
  process.exit(3);
}
process.exit(Number.isInteger(result.status) ? result.status : 3);
