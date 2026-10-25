// Замер перерисовки превью: первый (холодный) и повторный (после правки) проходы.
// Запуск: node frontend/scripts/typst-preview-bench.mjs input.typ
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { performance } from 'node:perf_hooks';
import { $typst } from '@myriaddreamin/typst.ts/contrib/snippet';

const inputPath = process.argv[2];
if (!inputPath) {
  console.error('usage: typst-preview-bench.mjs <input.typ>');
  process.exit(2);
}

const wasmPath = fileURLToPath(
  new URL(
    '../node_modules/@myriaddreamin/typst-ts-web-compiler/pkg/typst_ts_web_compiler_bg.wasm',
    import.meta.url,
  ),
);
$typst.setCompilerInitOptions({ getModule: () => readFileSync(wasmPath) });

const source = readFileSync(inputPath, 'utf8');
const edited = `${source}\n\nДополнительный абзац после правки.\n`;

await $typst.addSource('/main.typ', source);
const warmupStart = performance.now();
const first = await $typst.pdf({ mainFilePath: '/main.typ', root: '/' });
const warmupMs = performance.now() - warmupStart;

await $typst.addSource('/main.typ', edited);
const editStart = performance.now();
const second = await $typst.pdf({ mainFilePath: '/main.typ', root: '/' });
const redrawMs = performance.now() - editStart;

if (!first || !second) {
  console.error('typst.ts не вернул PDF');
  process.exit(1);
}
console.log(
  JSON.stringify({
    warmup_ms: Math.round(warmupMs),
    redraw_ms: Math.round(redrawMs),
    first_bytes: first.length,
    second_bytes: second.length,
  }),
);
