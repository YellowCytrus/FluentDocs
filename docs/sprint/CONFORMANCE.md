# CONFORMANCE — соответствие профиля «СТУ СФУ» правилам класса A

Правила взяты из `docs/sprint/FluentDocs_SFU_rules_plan_v2.md`: 78 правил класса A
и 2 правила класса AUTO (для полноты).
Столбцы: id правила → опции реестра → тест рендера (pdfplumber) или пометка.
Профиль собирается скриптом `scripts/seed_sfu_profile.py` из реестра; отдельного
кода оформления для СФУ нет.

Проверки G6: `tests/test_g6_seed.py` (значения и источники),
`tests/test_g6_conformance.py` (эталонный документ + профиль СФУ → PDF).

| id | Опции | Тест / измерение | Статус |
|---|---|---|---|
| `page.margins.portrait` | `page.margin_top/bottom/left/right` | `test_sfu_conformance_render` | реализовано |
| `page.margins.landscape` | `page.margin_landscape_*` | `test_page_landscape_render`, `test_page_landscape_options` | реализовано |
| `page.numbering` | `page.numbering`, `page.number_align`, `page.numbering_skip_first`, `page.numbering_start` | `test_sfu_conformance_render`, `test_page_numbering_render` | реализовано |
| `text.font.name` | `document.font` | `test_sfu_conformance_render` (алиас TNR → Libertinus Serif) | реализовано |
| `text.font.size` | `document.font_size`, `*.text_override.font_size` | `test_sfu_conformance_render` | реализовано |
| `text.font.color` | `document.fill` | — | не измеряется: цвет по умолчанию чёрный, отдельного PDF-теста нет |
| `text.alignment` | `document.justify` | — | не измеряется: выравнивание по ширине не даёт устойчивой метрики pdfplumber |
| `text.indent.first_line` | `par.first_line_indent` | `test_sfu_conformance_render` | реализовано |
| `text.line_spacing` | `document.line_spacing` | `test_sfu_line_spacing_multiplier_render`, `test_line_spacing_multiplier_render` | реализовано |
| `structural.heading` | `structural.entities` (`apply.case/align/bold/break_before`, `around`) | `test_sfu_conformance_render`, `test_structural_align_and_around` | реализовано |
| `referat.template` | — | — | отложено владельцем (`OWNER_DECISIONS` 12) |
| `referat.keywords_uppercase` | — | — | отложено владельцем (`OWNER_DECISIONS` 12) |
| `toc.required_for_length` | `outline.omit_when_pages_lte` | `test_g4_toc_skip_render` | реализовано |
| `toc.indent_levels` | `outline.indent_mode`, `outline.indent_per_level` | `test_outline_indent_render` | реализовано |
| `toc.matches_headings` | `outline.entry_case` | — | не измеряется: записи строятся из тех же заголовков |
| `toc.appendix_grouping` | `outline.appendix_grouping`, `outline.appendix_min_group`, `outline.appendix_group_template` | `test_g4_toc_appendix_grouping_render` | реализовано |
| `heading.h1` | `heading.h1.numbering_enabled`, `heading.h1.break_before`, `heading.h1.spacing_before/after`, `heading.numbering` | `test_sfu_conformance_render`, `test_element_spacing_render` | реализовано |
| `heading.h2` | `heading.h2.numbering_enabled`, `heading.h2.break_before`, `heading.h2.spacing_before/after`, `heading.numbering` | `test_sfu_conformance_render`, `test_element_spacing_render` | реализовано |
| `heading.h3` | `heading.h3.numbering_enabled`, `heading.h3.break_before`, `heading.h3.spacing_before/after`, `heading.numbering` | `test_sfu_conformance_render`, `test_element_spacing_render` | реализовано |
| `heading.h4` | `heading.h4.numbering_enabled`, `heading.h4.break_before`, `heading.h4.spacing_before/after`, `heading.numbering` | `test_sfu_conformance_render`, `test_element_spacing_render` | реализовано |
| `heading.h5` | `heading.h5.numbering_enabled`, `heading.h5.break_before`, `heading.h5.spacing_before/after`, `heading.numbering` | `test_sfu_conformance_render`, `test_element_spacing_render` | реализовано |
| `heading.h6` | `heading.h6.numbering_enabled`, `heading.h6.break_before`, `heading.h6.spacing_before/after`, `heading.numbering` | `test_sfu_conformance_render`, `test_element_spacing_render` | реализовано |
| `heading.spacing_before` | `heading.h1..h6.spacing_before`, `heading.keep_with_next` | `test_element_spacing_render` | реализовано |
| `heading.spacing_after` | `heading.h1..h6.spacing_after` | `test_element_spacing_render` | реализовано |
| `heading.no_hyphenation` | `document.hyphenate` (наследуется заголовками) | — | не измеряется: проверка переносов в заголовке отдельного теста не имеет |
| `list.item` | `bullet_list.body_indent`, `numbered_list.body_indent`, `numbered_list.wrap_mode` | `test_list_item_wrapped_line_indent`, `test_numbered_list_wrap_mode_render` | реализовано |
| `list.lettered` | `numbered_list.alphabet`, `numbered_list.level_formats` | `test_numbered_list_level_formats_render`, `test_numbered_list_alphabet_latin_render` | реализовано |
| `list.nested_numeric` | `numbered_list.level_formats` | `test_numbered_list_level_formats_render`, `test_numbered_list_nested_indent_render` | реализовано |
| `list.marker_alphabetical` | `bullet_list.marker`, `numbered_list.alphabet` | — | не измеряется: маркер виден в тексте, отдельного теста алфавита маркеров нет |
| `figure.caption` | `figure.caption_template/position/align/separator/text_override/around` | `test_figure_caption_render`, `test_figure_caption_align_render` | реализовано |
| `figure.spacing_before` | `figure.spacing_before` | `test_element_spacing_render` | реализовано |
| `figure.spacing_after` | `figure.spacing_after` | `test_element_spacing_render` | реализовано |
| `figure.image` | `figure.width`, `figure.fit`, `figure.gap` | `test_sfu_conformance_render` | реализовано |
| `figure.section_numbering` | `figure.caption_template` (`{h1}.{n}`) | `test_caption_counters_separate_render` | реализовано |
| `figure.appendix_numbering` | `figure.caption_template` + структурная сущность приложения | `test_caption_appendix_letter_render` | реализовано |
| `figure.placement_after_reference` | — | — | отложено: нужны ссылки на рисунки (новый синтаксис) |
| `figure.explanatory_data` | — | — | отложено: нужен новый синтаксис Markdown |
| `figure.multi_sheet_label` | — | — | отложено: нужен новый синтаксис Markdown |
| `formula.body` | `equation.align`, `equation.body_indent`, `equation.text_override` | `test_g5_equation_align_render`, `test_equation_body_indent_render` | реализовано |
| `formula.explanation` | `structural.entities` (`target: paragraph`, `starts_with`) | `test_g5_formula_explanation_paragraph_render` | реализовано |
| `formula.spacing_before` | `equation.spacing_before` | `test_element_spacing_render` | реализовано |
| `formula.spacing_after` | `equation.spacing_after` | `test_element_spacing_render` | реализовано |
| `formula.body_indent` | `equation.body_indent` | `test_equation_body_indent_render`, `test_sfu_conformance_render` | реализовано |
| `formula.section_numbering` | `equation.numbering_enabled`, `equation.numbering_template` | `test_g5_equation_numbering_section_render`, `test_sfu_conformance_render` | реализовано |
| `formula.appendix_numbering` | `equation.numbering_template` + буква приложения | `test_g5_equation_numbering_appendix_render` | реализовано |
| `formula.line_continuation` | — | — | отложено: нужен разбор структуры формулы; остаётся ручной разрыв `\` |
| `formula.cross_reference` | — | — | отложено: нужен новый синтаксис Markdown |
| `bibliography.entry` | — | — | вне спринта (AGENTS 7) |
| `table.caption` | `table.caption_template/position/align/separator/text_override/around` | `test_table_caption_render`, `test_table_caption_position_render` | реализовано |
| `table.spacing_before` | `table.spacing_before` | `test_element_spacing_render` | реализовано |
| `table.spacing_after` | `table.spacing_after` | `test_element_spacing_render` | реализовано |
| `table.cell_padding` | `table.inset` | `test_g4_table_inset_and_font_render` | реализовано |
| `table.font.size` | `table.text_override.font_size` | `test_g4_table_inset_and_font_render`, `test_sfu_conformance_render` | реализовано |
| `table.body` | — | — | не измеряется: содержимое таблицы задаёт автор |
| `table.borders` | `table.border_*`, `table.stroke`, `table.header_double_line`, `table.repeat_header` | `test_g4_table_borders_render`, `test_g4_table_double_header_render` | реализовано |
| `table.section_numbering` | `table.caption_template` (`{h1}.{n}`) | `test_caption_counters_separate_render` | реализовано |
| `table.appendix_numbering` | `table.caption_template` + структурная сущность приложения | `test_caption_appendix_letter_render` | реализовано |
| `table.unit_label` | — | — | отложено: нужен новый синтаксис Markdown |
| `table.numbering_row_replacement` | — | — | не реализовано: вне объёма G4 (рекомендация) |
| `table.continuation_label` | `table.continuation_label`, `table.continuation_template`, `table.final_template` | `test_g4_table_continuation_label_render` | реализовано |
| `table.footnote` | — | — | отложено: нужен новый синтаксис Markdown |
| `table.italic_letters` | `table.italic_letters` | `test_g4_table_italic_letters_render` | реализовано |
| `reference.footnote` | `footnote.marker_format`, `footnote.separator_*`, `footnote.text_override` | `test_footnote_separator_render`, `test_footnote_text_override_in_pdf` | реализовано |
| `reference.figure_table_formula` | — | — | отложено: нужны ссылки (новый синтаксис) |
| `appendix.heading` | `appendix.template`, `appendix.service_case`, `appendix.title_case`, `appendix.bold` | `test_appendix_heading_one_line`, `test_sfu_conformance_render` | реализовано |
| `appendix.auto_letter` | `appendix.alphabet`, `appendix.overflow` | `test_appendix_letter_sequence`, `test_appendix_large_start_does_not_overflow` | реализовано |
| `appendix.continuation_label` | — | — | отложено: не реализовано |
| `appendix.section_numbering` | структурная сущность приложения (`numbering.kind=appendix`, `sub_template`) | `test_appendix_numbering_subheadings` | реализовано |
| `appendix.in_text_reference` | — | — | отложено: нужен новый синтаксис Markdown |
| `appendix.sheet_format` | `page.paper` | — | не реализовано: не-A4 листы и смена ориентации в середине не поддерживаются |
| `abbreviations.two_column_layout` | — | — | отложено: нужен новый синтаксис Markdown |
| `coursework.formula.section_numbering` | значения seed из `REGISTRY_SPEC.md` (G6) | — | значения есть; отдельного профиля и рендер-теста нет |
| `coursework.table.section_numbering` | значения seed из `REGISTRY_SPEC.md` (G6) | — | значения есть; отдельного профиля и рендер-теста нет |
| `coursework.figure.section_numbering` | значения seed из `REGISTRY_SPEC.md` (G6) | — | значения есть; отдельного профиля и рендер-теста нет |
| `graduation_qualification_work.formula.section_numbering` | значения seed из `REGISTRY_SPEC.md` (G6) | — | значения есть; отдельного профиля и рендер-теста нет |
| `graduation_qualification_work.table.section_numbering` | значения seed из `REGISTRY_SPEC.md` (G6) | — | значения есть; отдельного профиля и рендер-теста нет |
| `graduation_qualification_work.figure.section_numbering` | значения seed из `REGISTRY_SPEC.md` (G6) | — | значения есть; отдельного профиля и рендер-теста нет |
| `coursework.toc.form_t` | — | — | отложено в G4 |
| `graduation_qualification_work.referat.required` | — | — | отложено владельцем (`OWNER_DECISIONS` 12) |
| `graduation_qualification_work.structure.assignment_after_title` | — | — | вне спринта: титульные листы (AGENTS 7) |

## Что проверяет эталонный документ

`tests/test_g6_conformance.py` собирает документ со всеми элементами (структурный
заголовок, H1/H2, абзац, оба списка, таблица с подписью, рисунок с подписью,
формула с номером, сноска, приложение с подзаголовком) и профилем СФУ, затем
измеряет:

| Свойство | Значение СТУ | Измерение |
|---|---|---|
| Поля страницы | 20/20/30/10 мм | координаты текста |
| Шрифт и кегль | TNR 14 pt | `chars[].fontname` / `size`; TNR — алиас Libertinus Serif |
| Красная строка | 1,25 см | x0 первой строки абзаца |
| Межстрочный интервал | 1,5 | отношение шага строк к множителю 1,0 |
| Нумерация страниц | первая без номера, далее по центру внизу | текст и координаты |
| Заголовки | 1, 1.1; структурный — без номера | текст и центрирование |
| Подпись таблицы | над таблицей, слева, 14 pt | y-порядок, x0, кегль |
| Сетка таблицы | границы | число линий |
| Подпись рисунка | под рисунком, по центру, 14 pt | y-порядок, центр, кегль |
| Ширина рисунка | 165 мм | ширина изображения |
| Формула | отступ 1,25 см, номер справа | x0 тела, x1 номера |
| Сноска | 12 pt | кегль |
| Приложение | новая страница, ПРОПИСНЫЕ, жирный, «А.1» | координаты, шрифт, текст |

## Известные ограничения

- «Times New Roman» — алиас `Libertinus Serif` (`FONT_ALIASES`): метрически
  совместимый шрифт с открытой лицензией. Профиль хранит имя TNR.
- Подпись рисунка в Markdown — это alt-текст изображения
  (`![Подпись](sample.png){#fig:a}`); строка `: подпись` после изображения без
  метки превращается Pandoc в список определений — это ограничение Pandoc,
  а не профиля.
- Заголовки не имеют опций размера и отступа первой строки: СТУ задаёт для них
  только выравнивание, жирность и интервалы, поэтому правила отмечены как
  «не измеряется» или покрыты существующими тестами.
