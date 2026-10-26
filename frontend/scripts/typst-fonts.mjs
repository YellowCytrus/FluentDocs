import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { TypstSnippet } from '@myriaddreamin/typst.ts/contrib/snippet';

export const FONT_DIR = fileURLToPath(new URL('../../assets/fonts/', import.meta.url));

// Те же файлы, что сервер отдаёт Typst CLI. Порядок не важен.
const FONT_FILES = [
  'pt-astra-serif_regular.ttf',
  'pt-astra-serif_italic.ttf',
  'pt-astra-serif_bold.ttf',
  'pt-astra-serif_bold-italic.ttf',
  'LibertinusSerif-Regular.otf',
  'LibertinusSerif-Italic.otf',
  'LibertinusSerif-Bold.otf',
  'LibertinusSerif-BoldItalic.otf',
  'LibertinusSerif-Semibold.otf',
  'LibertinusSerif-SemiboldItalic.otf',
  'NewCM10-Regular.otf',
  'NewCM10-Italic.otf',
  'NewCM10-Bold.otf',
  'NewCM10-BoldItalic.otf',
  'NewCMMath-Regular.otf',
  'NewCMMath-Bold.otf',
  'NewCMMath-Book.otf',
  'DejaVuSansMono.ttf',
  'DejaVuSansMono-Oblique.ttf',
  'DejaVuSansMono-Bold.ttf',
  'DejaVuSansMono-BoldOblique.ttf',
];

/** Загружает в typst.ts те же шрифты, что сервер отдаёт Typst CLI. */
export function loadProjectFonts($typst) {
  const fonts = FONT_FILES.map((file) => new Uint8Array(readFileSync(join(FONT_DIR, file))));
  $typst.use(TypstSnippet.preloadFonts(fonts), TypstSnippet.disableDefaultFontAssets());
}
