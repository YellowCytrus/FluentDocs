// Компилирует Typst-файл в PDF через typst.ts (тот же компилятор, что в превью).
// Запуск: node frontend/scripts/typst-render.mjs input.typ output.pdf [--time]
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';
import { performance } from 'node:perf_hooks';
import { $typst } from '@myriaddreamin/typst.ts/contrib/snippet';
import { loadProjectFonts } from './typst-fonts.mjs';

const [inputPath, outputPath] = process.argv.slice(2);
if (!inputPath || !outputPath) {
  console.error('usage: typst-render.mjs <input.typ> <output.pdf> [--time]');
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

const source = readFileSync(inputPath, 'utf8');
await $typst.resetShadow();
const sourceDir = dirname(inputPath);
for (const match of source.matchAll(/image\s*\(\s*"([^"]+)"/g)) {
  const ref = match[1];
  if (!ref || ref.startsWith('http://') || ref.startsWith('https://') || ref.startsWith('data:')) {
    continue;
  }
  const localPath = normalize(join(sourceDir, ref));
  if (!existsSync(localPath)) continue;
  const shadowPath = ref.startsWith('/') ? ref : `/${ref}`;
  await $typst.mapShadow(shadowPath, new Uint8Array(readFileSync(localPath)));
}
await $typst.addSource('/main.typ', source);
const started = performance.now();
const pdf = await $typst.pdf({ mainFilePath: '/main.typ', root: '/' });
const elapsed = performance.now() - started;
if (!pdf) {
  console.error('typst.ts не вернул PDF');
  process.exit(1);
}
writeFileSync(outputPath, pdf);
if (process.argv.includes('--time')) {
  console.log(JSON.stringify({ pdf_ms: Math.round(elapsed), bytes: pdf.length }));
}
