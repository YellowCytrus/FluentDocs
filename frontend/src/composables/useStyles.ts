import type { ElementType } from '../types/api';
import { API_BASE } from '../config';

const ALL_ELEMENT_PATHS: ElementType[] = [
  'page',
  'document',
  'par',
  'heading',
  'heading_1',
  'heading_2',
  'heading_3',
  'heading_4',
  'heading_5',
  'heading_6',
  'bullet_list',
  'numbered_list',
  'table',
  'figure',
  'footnote',
  'quote',
  'raw',
  'equation',
  'terms',
  'outline',
];

function typstStr(s: string): string {
  const escaped = s.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
  return `"${escaped}"`;
}

function typstListSpacing(s: string): string {
  if (s === 'auto') return 'auto';
  if (s === 'tight') return '0.5em';
  if (s === 'loose') return '1em';
  return 'auto';
}

/** Компенсация пустого места под скрытый номер заголовка (см. typst_preamble._HEADING_UNNUMBERED_LEFT_OUTDENT). */
const UNNUMBERED_HEADING_LEFT_OUTDENT = '-0.3em';

type DTO = Record<string, unknown>;

function pageLine(e: DTO): string {
  const args: string[] = [typstStr(e.paper as string ?? 'a4')];
  if (e.flipped) args.push('flipped: true');
  const mp: string[] = [
    `top: ${((e.margin_top as number) ?? 25)}mm`,
    `bottom: ${((e.margin_bottom as number) ?? 25)}mm`,
    `left: ${((e.margin_left as number) ?? 25)}mm`,
    `right: ${((e.margin_right as number) ?? 25)}mm`,
  ];
  args.push(`margin: (${mp.join(', ')})`);
  if ((e.columns as number) !== 1) args.push(`columns: ${e.columns}`);
  if (e.numbering !== 'none') args.push(`numbering: ${typstStr(e.numbering as string)}`);
  if (e.number_align !== 'center+bottom') args.push(`number-align: ${e.number_align}`);
  return `#set page(${args.join(', ')})`;
}

function documentLine(e: DTO): string {
  const ta: string[] = [`size: ${e.font_size ?? 12}pt`];
  if (e.font && e.font !== 'libertinus serif') ta.push(`font: ${typstStr(e.font as string)}`);
  if (e.weight && e.weight !== 'regular') ta.push(`weight: ${typstStr(e.weight as string)}`);
  if (e.style && e.style !== 'normal') ta.push(`style: ${typstStr(e.style as string)}`);
  if (e.fill && e.fill !== 'black') ta.push(`fill: ${e.fill}`);
  if (e.lang && e.lang !== 'en') ta.push(`lang: ${typstStr(e.lang as string)}`);
  if (e.tracking && (e.tracking as number) !== 0) ta.push(`tracking: ${e.tracking}pt`);
  if (e.word_spacing && (e.word_spacing as number) !== 100) ta.push(`spacing: ${e.word_spacing}%`);
  if (!e.ligatures && e.ligatures !== undefined) ta.push('ligatures: false');
  return `#set text(${ta.join(', ')})\n#set par(leading: ${e.line_spacing ?? 5.08}mm)`;
}

function parLine(e: DTO): string {
  const a: string[] = [`spacing: ${e.spacing ?? 4.2333333333}mm`];
  if (e.first_line_indent && (e.first_line_indent as number) !== 0) a.push(`first-line-indent: (amount: ${e.first_line_indent}mm, all: true)`);
  if (e.hanging_indent && (e.hanging_indent as number) !== 0) a.push(`hanging-indent: ${e.hanging_indent}mm`);
  if (e.justify) a.push('justify: true');
  if (e.linebreaks && e.linebreaks !== 'auto') a.push(`linebreaks: ${typstStr(e.linebreaks as string)}`);
  return `#set par(${a.join(', ')})`;
}

function collectHeadingLevelsWithoutNumbering(elements: Map<ElementType, DTO>): number[] {
  const hidden: number[] = [];
  for (let lv = 1; lv <= 6; lv += 1) {
    const key = `heading_${lv}` as ElementType;
    const row = elements.get(key);
    if (row && row.numbering_enabled === false) hidden.push(lv);
  }
  return hidden;
}

function headingLine(e: DTO, hiddenLevels: number[]): string {
  const num = (e.numbering as string) ?? '1.1.1';
  if (num === 'none') return '#set heading(numbering: none)';
  if (hiddenLevels.length === 0) {
    return `#set heading(numbering: ${typstStr(num)})`;
  }
  const tuple =
    hiddenLevels.length === 1 ? `(${hiddenLevels[0]},)` : `(${hiddenLevels.join(', ')})`;
  const pat = typstStr(num);
  return `#set heading(numbering: (..args) => {
  let n = args.pos()
  let level = n.len()
  if ${tuple}.contains(level) {
    none
  } else {
    numbering(${pat}, ..n)
  }
})`;
}

function headingLevelLine(e: DTO, level: number): string {
  const args: string[] = [];
  if (e.outlined === false) args.push('outlined: false');
  if (e.bookmarked && e.bookmarked !== 'auto') args.push(`bookmarked: ${e.bookmarked}`);
  if (e.offset && (e.offset as number) !== 0) args.push(`offset: ${e.offset}`);
  const suffix = args.length ? `, ${args.join(', ')}` : '';
  const headingExpr = `heading(it.body${suffix})`;
  const tail =
    e.numbering_enabled === false
      ? `#box(${headingExpr}, inset: (left: ${UNNUMBERED_HEADING_LEFT_OUTDENT}))`
      : `#${headingExpr}`;

  // В Typst `#pagebreak` нельзя выполнять внутри `block[...]`, поэтому:
  // - при break_before: `it => [ #pagebreak(...); block[ <tail> ] ]`
  // - без break_before: `it => block[ <tail> ]`
  if (e.break_before) {
    return `#show heading.where(level: ${level}): it => [ #pagebreak(weak: true); #block[ ${tail} ] ]`;
  }

  return `#show heading.where(level: ${level}): it => block[ ${tail} ]`;
}

function equationLine(_e: DTO): string {
  return '';
}

function bulletListLine(e: DTO): string {
  const markers = (e.marker as string[]) ?? ['- ', '‣', '–'];
  const markersStr = markers.map(typstStr).join(', ');
  return `#set list(tight: ${e.tight ?? true}, indent: ${e.indent ?? 0}mm, body-indent: ${e.body_indent ?? 2.1166666667}mm, spacing: ${typstListSpacing((e.spacing as string) ?? 'auto')}, marker: (${markersStr}))`;
}

function numberedListLine(e: DTO): string {
  const a: string[] = [
    `tight: ${e.tight ?? true}`,
    `indent: ${e.indent ?? 0}mm`,
    `body-indent: ${e.body_indent ?? 2.1166666667}mm`,
    `spacing: ${typstListSpacing((e.spacing as string) ?? 'auto')}`,
  ];
  if (e.numbering && e.numbering !== '1.') a.push(`numbering: ${typstStr(e.numbering as string)}`);
  if (e.reversed) a.push('reversed: true');
  if (e.full) a.push('full: true');
  return `#set enum(${a.join(', ')})`;
}

function tableLine(e: DTO): string {
  const a: string[] = [`stroke: ${(e.stroke as number) ?? 0.1763888889}mm`];
  if (e.align && e.align !== 'auto') a.push(`align: ${e.align}`);
  a.push(`inset: ${((e.inset as number) ?? 1.7638888889)}mm`);
  if (e.fill && e.fill !== 'none') a.push(`fill: ${e.fill}`);
  return `#set table(${a.join(', ')})`;
}

function figureLine(e: DTO): string {
  const w = (e.width as number) ? `${e.width}mm` : 'auto';
  const h = (e.height as number) ? `${e.height}mm` : 'auto';
  const ia: string[] = [`width: ${w}`, `height: ${h}`];
  if (e.fit && e.fit !== 'cover') ia.push(`fit: ${typstStr(e.fit as string)}`);
  const parts: string[] = [`#set image(${ia.join(', ')})`];
  const fa: string[] = [];
  if (e.placement && e.placement !== 'none') fa.push(`placement: ${e.placement}`);
  fa.push(`gap: ${((e.gap as number) ?? 2.7516666667)}mm`);
  if (e.outlined === false) fa.push('outlined: false');
  if (fa.length) parts.push(`#set figure(${fa.join(', ')})`);
  return parts.join('\n');
}

function footnoteLine(e: DTO): string {
  const parts: string[] = [`#set footnote(numbering: ${typstStr((e.marker_format as string) ?? '1')})`];
  const ea: string[] = [
    `clearance: ${((e.clearance as number) ?? 4.2333333333)}mm`,
    `gap: ${((e.gap as number) ?? 2.1166666667)}mm`,
    `indent: ${((e.indent as number) ?? 4.2333333333)}mm`,
  ];
  parts.push(`#set footnote.entry(${ea.join(', ')})`);
  return parts.join('\n');
}

function quoteLine(e: DTO): string {
  const qa: string[] = [`block: ${e.block ?? true}`];
  if (e.quotes && e.quotes !== 'auto') qa.push(`quotes: ${e.quotes}`);
  return `#set quote(${qa.join(', ')})\n#show quote: set pad(x: ${e.indent ?? 6.35}mm)`;
}

function rawLine(e: DTO): string {
  const a: string[] = [];
  if (e.tab_size && (e.tab_size as number) !== 2) a.push(`tab-size: ${e.tab_size}`);
  if (e.align && e.align !== 'start') a.push(`align: ${e.align}`);
  if (e.theme === 'none') a.push('theme: none');
  return a.length ? `#set raw(${a.join(', ')})` : '';
}

function termsLine(e: DTO): string {
  const a: string[] = [`tight: ${e.tight ?? true}`];
  if (e.indent && (e.indent as number) !== 0) a.push(`indent: ${e.indent}mm`);
  a.push(`hanging-indent: ${((e.hanging_indent as number) ?? 8.4666666667)}mm`);
  if (e.spacing && e.spacing !== 'auto') a.push(`spacing: ${typstListSpacing(e.spacing as string)}`);
  return `#set terms(${a.join(', ')})`;
}

function outlineLine(e: DTO): string {
  const a: string[] = [];
  if (e.depth != null) a.push(`depth: ${e.depth}`);
  if (e.indent_mode === 'none') a.push('indent: 0mm');
  if (e.indent_mode === 'custom') a.push(`indent: ${(e.indent_mm as number) ?? 0}mm`);
  return a.length ? `#set outline(${a.join(', ')})` : '';
}

type ElementStyleBuilderKey = Exclude<ElementType, 'heading'>;

const BUILDERS: Record<ElementStyleBuilderKey, (e: DTO) => string> = {
  page: pageLine,
  document: documentLine,
  par: parLine,
  heading_1: (e) => headingLevelLine(e, 1),
  heading_2: (e) => headingLevelLine(e, 2),
  heading_3: (e) => headingLevelLine(e, 3),
  heading_4: (e) => headingLevelLine(e, 4),
  heading_5: (e) => headingLevelLine(e, 5),
  heading_6: (e) => headingLevelLine(e, 6),
  bullet_list: bulletListLine,
  numbered_list: numberedListLine,
  table: tableLine,
  figure: figureLine,
  footnote: footnoteLine,
  quote: quoteLine,
  raw: rawLine,
  equation: equationLine,
  terms: termsLine,
  outline: outlineLine,
};

function buildTypstPreamble(elements: Map<ElementType, DTO>): string {
  const hiddenHeadingLevels = collectHeadingLevelsWithoutNumbering(elements);
  const lines: string[] = [];
  for (const type of ALL_ELEMENT_PATHS) {
    const e = elements.get(type);
    if (!e) continue;
    if (type === 'heading') {
      const part = headingLine(e, hiddenHeadingLevels);
      if (part) lines.push(...part.split('\n'));
      continue;
    }
    const fn = BUILDERS[type];
    if (!fn) continue;
    const part = fn(e);
    if (part) lines.push(...part.split('\n'));
  }
  return lines.length ? lines.join('\n') + '\n' : '';
}

export async function loadProfileStyles(profileId: number): Promise<string> {
  const elements = new Map<ElementType, DTO>();

  await Promise.all(
    ALL_ELEMENT_PATHS.map(async (type) => {
      try {
        const path = /^heading_\d$/.test(type)
          ? `heading/${type.replace('heading_', '')}`
          : type === 'equation'
            ? 'equation'
            : type;
        const res = await fetch(`${API_BASE}/profiles/${profileId}/${path}`);
        if (res.ok) {
          elements.set(type, await res.json());
        }
      } catch {
        // skip failed elements
      }
    }),
  );

  return buildTypstPreamble(elements);
}
