// Profile
export interface Profile {
  id: number;
  name: string;
}

export interface ProfileCreate {
  name: string;
}

export interface ProfileUpdate {
  name?: string;
}

// ---------------------------------------------------------------------------
// Element style DTOs (match backend Pydantic schemas)
// ---------------------------------------------------------------------------

export interface BulletListStyles {
  tight: boolean;
  marker: string[];
  indent: number;
  body_indent: number;
  spacing: 'auto' | 'tight' | 'loose';
  text_override: TextOverrideStyles | null;
}

export interface BulletListStylesUpdate {
  tight?: boolean;
  marker?: string[];
  indent?: number;
  body_indent?: number;
  spacing?: 'auto' | 'tight' | 'loose';
}

export interface DocumentStyles {
  font_size: number;
  line_spacing: number;
  font: string;
  weight: string;
  style: string;
  fill: string;
  lang: string;
  region: string | null;
  tracking: number;
  word_spacing: number;
  hyphenate: boolean | null;
  ligatures: boolean;
  number_type: string;
  number_width: string;
  justify: boolean;
}

export interface DocumentStylesUpdate {
  font_size?: number;
  line_spacing?: number;
  font?: string;
  weight?: string;
  style?: string;
  fill?: string;
  lang?: string;
  region?: string | null;
  tracking?: number;
  word_spacing?: number;
  hyphenate?: boolean | null;
  ligatures?: boolean;
  number_type?: string;
  number_width?: string;
  justify?: boolean;
}

export interface FigureStyles {
  width: number;
  height: number;
  placement: string;
  gap: number;
  outlined: boolean;
  fit: string;
  caption_template?: string | null;
  text_override: TextOverrideStyles | null;
}

export interface FigureStylesUpdate {
  width?: number;
  height?: number;
  placement?: string;
  gap?: number;
  outlined?: boolean;
  fit?: string;
  caption_template?: string | null;
}

export interface FootnoteStyles {
  marker_format: '1' | 'a' | 'A' | 'i' | 'I' | '*';
  clearance: number;
  gap: number;
  indent: number;
  text_override: TextOverrideStyles | null;
}

export interface FootnoteStylesUpdate {
  marker_format?: '1' | 'a' | 'A' | 'i' | 'I' | '*';
  clearance?: number;
  gap?: number;
  indent?: number;
}

export interface HeadingStyles {
  numbering: string;
}

export interface HeadingStylesUpdate {
  numbering?: string;
}

export interface NumberedListStyles {
  tight: boolean;
  indent: number;
  body_indent: number;
  spacing: 'auto' | 'tight' | 'loose';
  numbering: string;
  start: number | null;
  full: boolean;
  reversed: boolean;
  number_align: string;
  text_override: TextOverrideStyles | null;
}

export interface NumberedListStylesUpdate {
  tight?: boolean;
  indent?: number;
  body_indent?: number;
  spacing?: 'auto' | 'tight' | 'loose';
  numbering?: string;
  start?: number | null;
  full?: boolean;
  reversed?: boolean;
  number_align?: string;
}

export interface OutlineStyles {
  depth: number | null;
  indent_mode: 'auto' | 'none' | 'custom';
  indent_mm: number;
  text_override: TextOverrideStyles | null;
}

export interface OutlineStylesUpdate {
  depth?: number | null;
  indent_mode?: 'auto' | 'none' | 'custom';
  indent_mm?: number;
}

export interface PageStyles {
  paper: string;
  flipped: boolean;
  margin_top: number;
  margin_bottom: number;
  margin_left: number;
  margin_right: number;
  columns: number;
  numbering: string;
  number_align: string;
}

export interface PageStylesUpdate {
  paper?: string;
  flipped?: boolean;
  margin_top?: number;
  margin_bottom?: number;
  margin_left?: number;
  margin_right?: number;
  columns?: number;
  numbering?: string;
  number_align?: string;
}

export interface ParStyles {
  spacing: number;
  first_line_indent: number;
  hanging_indent: number;
  linebreaks: string;
  text_override: TextOverrideStyles | null;
}

export interface ParStylesUpdate {
  spacing?: number;
  first_line_indent?: number;
  hanging_indent?: number;
  linebreaks?: string;
  text_override?: TextOverrideStyles | null;
}

export interface QuoteStyles {
  indent: number;
  block: boolean;
  quotes: string;
  text_override: TextOverrideStyles | null;
}

export interface QuoteStylesUpdate {
  indent?: number;
  block?: boolean;
  quotes?: string;
}

export interface RawStyles {
  tab_size: number;
  align: string;
  theme: string;
  text_override: TextOverrideStyles | null;
}

export interface RawStylesUpdate {
  tab_size?: number;
  align?: string;
  theme?: string;
}

export interface EquationStyles {
  text_override: TextOverrideStyles | null;
}

export interface EquationStylesUpdate {
  text_override?: TextOverrideStyles | null;
}

export interface HeadingLevelStyles {
  level: number;
  break_before: boolean;
  numbering_enabled: boolean;
  text_override: TextOverrideStyles | null;
}

export interface HeadingLevelStylesUpdate {
  break_before?: boolean;
  numbering_enabled?: boolean;
  text_override?: TextOverrideStyles | null;
}

export interface TextOverrideStyles {
  font: string;
  font_size: number;
  weight: string;
  style: string;
  fill: string;
  lang: string;
  region: string | null;
  tracking: number;
  word_spacing: number;
  hyphenate: boolean | null;
  ligatures: boolean;
  number_type: string;
  number_width: string;
}

export interface TableStyles {
  stroke: number;
  align: string;
  inset: number;
  fill: string;
  text_override: TextOverrideStyles | null;
}

export interface TableStylesUpdate {
  stroke?: number;
  align?: string;
  inset?: number;
  fill?: string;
}

export interface TermsStyles {
  tight: boolean;
  indent: number;
  hanging_indent: number;
  spacing: 'auto' | 'tight' | 'loose';
  text_override: TextOverrideStyles | null;
}

export interface TermsStylesUpdate {
  tight?: boolean;
  indent?: number;
  hanging_indent?: number;
  spacing?: 'auto' | 'tight' | 'loose';
}

// Element types for API paths
export type ElementType =
  | 'bullet_list'
  | 'document'
  | 'equation'
  | 'figure'
  | 'footnote'
  | 'heading'
  | 'heading_1'
  | 'heading_2'
  | 'heading_3'
  | 'heading_4'
  | 'heading_5'
  | 'heading_6'
  | 'numbered_list'
  | 'outline'
  | 'page'
  | 'par'
  | 'quote'
  | 'raw'
  | 'table'
  | 'terms';
