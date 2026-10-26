#let fd-config = (
  page: (
    paper: "a4",
    flipped: false,
    margin_top: 25.0,
    margin_bottom: 25.0,
    margin_left: 25.0,
    margin_right: 25.0,
    columns: 1,
    numbering: "none",
    number_align: "center+bottom",
  ),
  document: (
    font_size: 12.0,
    line_spacing: (
      mode: "mm",
      value: 5.08,
    ),
    font: "Merriweather",
    weight: "regular",
    style: "normal",
    fill: "black",
    lang: "en",
    region: none,
    tracking: 0.0,
    word_spacing: 100.0,
    hyphenate: auto,
    ligatures: true,
    number_type: "auto",
    number_width: "auto",
    justify: false,
    line_height_em: 1.308,
    default_leading_em: 0.65,
  ),
  par: (
    spacing: 4.2333333333,
    first_line_indent: 0.0,
    hanging_indent: 0.0,
    linebreaks: "auto",
    text_override: none,
  ),
  heading: (
    numbering: "1.1.1",
    unnumbered_indent: -0.3,
  ),
  heading_levels: (
    (
      level: 1,
      break_before: false,
      numbering_enabled: true,
      text_override: none,
    ),
    (
      level: 2,
      break_before: false,
      numbering_enabled: true,
      text_override: none,
    ),
    (
      level: 3,
      break_before: false,
      numbering_enabled: true,
      text_override: none,
    ),
    (
      level: 4,
      break_before: false,
      numbering_enabled: true,
      text_override: none,
    ),
    (
      level: 5,
      break_before: false,
      numbering_enabled: true,
      text_override: none,
    ),
    (
      level: 6,
      break_before: false,
      numbering_enabled: true,
      text_override: none,
    ),
  ),
  bullet_list: (
    tight: true,
    marker: (
      "- ",
      "‣",
      "–",
    ),
    indent: 0.0,
    body_indent: 2.1166666667,
    spacing: "auto",
    tight_spacing: 0.5,
    loose_spacing: 1.0,
    text_override: none,
  ),
  numbered_list: (
    tight: true,
    indent: 0.0,
    body_indent: 2.1166666667,
    spacing: "auto",
    numbering: "1.",
    start: none,
    full: false,
    reversed: false,
    number_align: "end+top",
    tight_spacing: 0.5,
    loose_spacing: 1.0,
    text_override: none,
  ),
  terms: (
    tight: true,
    indent: 0.0,
    hanging_indent: 8.4666666667,
    spacing: "auto",
    tight_spacing: 0.5,
    loose_spacing: 1.0,
    text_override: none,
  ),
  table: (
    stroke: 0.1763888889,
    align: "auto",
    inset: 1.7638888889,
    fill: "none",
    text_override: none,
  ),
  figure: (
    width: 4.2333333333,
    height: 0.0,
    placement: "none",
    gap: 2.7516666667,
    outlined: true,
    fit: "cover",
    caption_template: none,
    text_override: none,
  ),
  equation: (
    text_override: none,
  ),
  quote: (
    indent: 6.35,
    block: true,
    quotes: "auto",
    text_override: none,
  ),
  footnote: (
    marker_format: "1",
    clearance: 4.2333333333,
    gap: 2.1166666667,
    indent: 4.2333333333,
    text_override: none,
  ),
  raw: (
    tab_size: 2,
    align: "start",
    theme: "auto",
    text_override: none,
  ),
  outline: (
    depth: none,
    indent_mode: "auto",
    indent_mm: 0.0,
    text_override: none,
  ),
  around: (
    heading_1: (
      before: (),
      after: (),
      collapse: "max",
    ),
    heading_2: (
      before: (),
      after: (),
      collapse: "max",
    ),
    heading_3: (
      before: (),
      after: (),
      collapse: "max",
    ),
    heading_4: (
      before: (),
      after: (),
      collapse: "max",
    ),
    heading_5: (
      before: (),
      after: (),
      collapse: "max",
    ),
    heading_6: (
      before: (),
      after: (),
      collapse: "max",
    ),
    par: (
      before: (),
      after: (),
      collapse: "max",
    ),
    bullet_list: (
      before: (),
      after: (),
      collapse: "max",
    ),
    numbered_list: (
      before: (),
      after: (),
      collapse: "max",
    ),
    table: (
      before: (),
      after: (),
      collapse: "max",
    ),
    figure: (
      before: (),
      after: (),
      collapse: "max",
    ),
    equation: (
      before: (),
      after: (),
      collapse: "max",
    ),
    quote: (
      before: (),
      after: (),
      collapse: "max",
    ),
    raw: (
      before: (),
      after: (),
      collapse: "max",
    ),
    terms: (
      before: (),
      after: (),
      collapse: "max",
    ),
  ),
)

// --- document body ---
= Списки
<списки>
== Маркированный список
<маркированный-список>
- Первый уровень
  - Второй уровень
    - Третий уровень
- Ещё один первый уровень
  - Ещё один второй уровень

== Нумерованный список
<нумерованный-список>
+ Первый уровень
  + Второй уровень
    + Третий уровень
+ Ещё один первый уровень
  + Ещё один второй уровень
