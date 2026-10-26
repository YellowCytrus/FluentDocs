// Компилирует набор Typst-файлов через typst.ts для теста паритета.
// Запуск: node frontend/scripts/typst-parity.mjs manifest.json
// manifest.json: [{ "input": "...", "output": "..." }, ...]
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, normalize } from 'node:path';
import { performance } from 'node:perf_hooks';
import { fileURLToPath } from 'node:url';
import { $typst } from '@myriaddreamin/typst.ts/contrib/snippet';
import { loadProjectFonts } from './typst-fonts.mjs';

const manifestPath = process.argv[2];
if (!manifestPath) {
  console.error('usage: typst-parity.mjs <manifest.json>');
  process.exit(2);
}

const wasmPath = fileURLToPath(
  new URL(
    '../node_modules/@myriaddreamin/typst-ts-web-compiler/pkg/typst_ts_web_compiler_bg.wasm',
    import.meta.url,
  ),
);
$typst.setCompilerInitOptions({ getModule: () => readFileSync(wasmPath) });
loadProjectFonts($typst);

const jobs = JSON.parse(readFileSync(manifestPath, 'utf8'));
const results = [];
for (const job of jobs) {
  const source = readFileSync(job.input, 'utf8');
  await $typst.resetShadow();
  for (const match of source.matchAll(/image\s*\(\s*"([^"]+)"/g)) {
    const ref = match[1];
    if (
      !ref ||
      ref.startsWith('http://') ||
      ref.startsWith('https://') ||
      ref.startsWith('data:')
    ) {
      continue;
    }
    const localPath = normalize(join(dirname(job.input), ref));
    if (!existsSync(localPath)) continue;
    const shadowPath = ref.startsWith('/') ? ref : `/${ref}`;
    await $typst.mapShadow(shadowPath, new Uint8Array(readFileSync(localPath)));
  }
  await $typst.addSource('/main.typ', source);
  const started = performance.now();
  const pdf = await $typst.pdf({ mainFilePath: '/main.typ', root: '/' });
  const elapsed = performance.now() - started;
  if (!pdf) throw new Error(`typst.ts не вернул PDF для ${job.input}`);
  writeFileSync(job.output, pdf);
  results.push({ input: job.input, ms: Math.round(elapsed), bytes: pdf.length });
}
console.log(JSON.stringify(results));
