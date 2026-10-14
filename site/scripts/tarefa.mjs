// Executa as tarefas do site de forma igual em Windows, macOS e Linux.
// Uso: node scripts/tarefa.mjs <dev|build|build:preview|preview|validar>
import { spawnSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const aqui = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const raiz = resolve(aqui, "..");

function rodar(cmd, args, env = {}) {
  const r = spawnSync(cmd, args, { cwd: aqui, stdio: "inherit", env: { ...process.env, ...env } });
  if (r.error) return { ok: false, naoEncontrado: r.error.code === "ENOENT" };
  return { ok: r.status === 0, status: r.status };
}

function validar() {
  const script = resolve(raiz, "scripts", "validar.py");
  const tentativas = [["python3", []], ["python", []], ["py", ["-3"]]];
  for (const [cmd, pre] of tentativas) {
    const r = rodar(cmd, [...pre, "-I", script]);
    if (r.naoEncontrado) continue;
    if (!r.ok) process.exit(r.status ?? 1);
    return;
  }
  console.error("Python 3 não encontrado (tentei python3, python e py -3). Instale em https://www.python.org/downloads/ e rode: pip install -r requirements.txt");
  process.exit(1);
}

function preparar() {
  const r = rodar(process.execPath, [resolve(aqui, "scripts", "preparar.mjs")]);
  if (!r.ok) process.exit(r.status ?? 1);
}

function astro(args, env) {
  const r = rodar(process.execPath, [resolve(aqui, "node_modules", "astro", "astro.js"), ...args], env);
  if (!r.ok) process.exit(r.status ?? 1);
}

const tarefa = process.argv[2];
const extra = process.argv.slice(3); // ex.: --port 4400 --host
switch (tarefa) {
  case "validar": validar(); break;
  case "dev": preparar(); astro(["dev", ...extra], { PREVIEW: "1" }); break;
  case "build": validar(); preparar(); astro(["build"]); break;
  case "build:preview": validar(); preparar(); astro(["build"], { PREVIEW: "1" }); break;
  case "preview": astro(["preview", ...extra]); break;
  default:
    console.error("Uso: node scripts/tarefa.mjs <dev|build|build:preview|preview|validar>");
    process.exit(2);
}
