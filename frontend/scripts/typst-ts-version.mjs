// Печатает версию Typst, встроенную в компилятор typst.ts.
// Используется tests/test_versions.py. Запуск: node frontend/scripts/typst-ts-version.mjs
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { $typst } from '@myriaddreamin/typst.ts/contrib/snippet';

const wasmPath = fileURLToPath(
  new URL('../node_modules/@myriaddreamin/typst-ts-web-compiler/pkg/typst_ts_web_compiler_bg.wasm', import.meta.url),
);
$typst.setCompilerInitOptions({ getModule: () => readFileSync(wasmPath) });

const svg = await $typst.svg({ mainContent: '#sys.version' });
const match = svg.match(/\b\d+\.\d+\.\d+\b/);
if (!match) {
  console.error('не удалось определить версию Typst в typst.ts');
  process.exit(1);
}
console.log(match[0]);
