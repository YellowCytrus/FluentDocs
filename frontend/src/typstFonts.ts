import { $typst, TypstSnippet } from '@myriaddreamin/typst.ts/contrib/snippet';

// Те же файлы, что сервер передаёт Typst CLI через --font-path. Без них
// typst.ts тянул бы шрифты с CDN, и паритет зависел бы от сети.
import regular from '../../assets/fonts/pt-astra-serif_regular.ttf?url';
import italic from '../../assets/fonts/pt-astra-serif_italic.ttf?url';
import bold from '../../assets/fonts/pt-astra-serif_bold.ttf?url';
import boldItalic from '../../assets/fonts/pt-astra-serif_bold-italic.ttf?url';
import libertinusRegular from '../../assets/fonts/LibertinusSerif-Regular.otf?url';
import libertinusItalic from '../../assets/fonts/LibertinusSerif-Italic.otf?url';
import libertinusBold from '../../assets/fonts/LibertinusSerif-Bold.otf?url';
import libertinusBoldItalic from '../../assets/fonts/LibertinusSerif-BoldItalic.otf?url';
import libertinusSemibold from '../../assets/fonts/LibertinusSerif-Semibold.otf?url';
import libertinusSemiboldItalic from '../../assets/fonts/LibertinusSerif-SemiboldItalic.otf?url';
import newCmRegular from '../../assets/fonts/NewCM10-Regular.otf?url';
import newCmItalic from '../../assets/fonts/NewCM10-Italic.otf?url';
import newCmBold from '../../assets/fonts/NewCM10-Bold.otf?url';
import newCmBoldItalic from '../../assets/fonts/NewCM10-BoldItalic.otf?url';
import newCmMathRegular from '../../assets/fonts/NewCMMath-Regular.otf?url';
import newCmMathBold from '../../assets/fonts/NewCMMath-Bold.otf?url';
import newCmMathBook from '../../assets/fonts/NewCMMath-Book.otf?url';
import dejaVuMono from '../../assets/fonts/DejaVuSansMono.ttf?url';
import dejaVuMonoOblique from '../../assets/fonts/DejaVuSansMono-Oblique.ttf?url';
import dejaVuMonoBold from '../../assets/fonts/DejaVuSansMono-Bold.ttf?url';
import dejaVuMonoBoldOblique from '../../assets/fonts/DejaVuSansMono-BoldOblique.ttf?url';

export const PROJECT_FONT_URLS = [
  regular,
  italic,
  bold,
  boldItalic,
  libertinusRegular,
  libertinusItalic,
  libertinusBold,
  libertinusBoldItalic,
  libertinusSemibold,
  libertinusSemiboldItalic,
  newCmRegular,
  newCmItalic,
  newCmBold,
  newCmBoldItalic,
  newCmMathRegular,
  newCmMathBold,
  newCmMathBook,
  dejaVuMono,
  dejaVuMonoOblique,
  dejaVuMonoBold,
  dejaVuMonoBoldOblique,
];

/** Регистрирует шрифты проекта в typst.ts до первой компиляции. */
export function registerProjectFonts(): void {
  $typst.use(
    TypstSnippet.preloadFonts(PROJECT_FONT_URLS),
    TypstSnippet.disableDefaultFontAssets(),
  );
}
