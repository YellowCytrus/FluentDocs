// Библиотека оформления FluentDocs.
// Получает конфиг профиля (словарь fd-config) и применяет все правила
// оформления к телу документа. Логика намеренно оставлена в Typst,
// чтобы превью и PDF исполняли один и тот же исходник.
#let fd = {
  // --- вспомогательные преобразования ---

  // Алиасы шрифтов, которых может не быть в окружении Typst.
  let font(f) = {
    let s = f.trim()
    let key = lower(s)
    if s == "" {
      "libertinus serif"
    } else if key == "times new roman" or key == "times" {
      "Libertinus Serif"
    } else if key == "arial" or key == "helvetica" {
      "DejaVu Sans"
    } else if key == "courier new" or key == "courier" {
      "DejaVu Sans Mono"
    } else {
      f
    }
  }

  // Цвет из строки профиля; none используется для отсутствия заливки.
  let paint(s) = {
    if s == "none" { none } else { rgb(s) }
  }

  let alignment-part(p) = {
    if p == "left" { left }
    else if p == "right" { right }
    else if p == "center" { center }
    else if p == "start" { start }
    else if p == "end" { end }
    else if p == "top" { top }
    else if p == "bottom" { bottom }
    else if p == "horizon" { horizon }
    else if p == "vertical" { vertical }
    else { auto }
  }

  // Строки вида "center+bottom" и "end+top" из старых enum.
  let alignment(s) = {
    if s == "auto" {
      auto
    } else {
      let out = none
      for part in s.split("+") {
        let value = alignment-part(part)
        out = if out == none { value } else { out + value }
      }
      if out == none { auto } else { out }
    }
  }

  // Межстрочный интервал (leading): мм или множитель высоты строки.
  // Обслуживает document.line_spacing в абзацах.
  let line-pitch(config) = {
    let spacing = config.document.line_spacing
    if spacing.mode == "mm" {
      spacing.value * 1mm
    } else {
      let natural = config.document.line_height_em
      (spacing.value * natural - (natural - config.document.default_leading_em)) * 1em
    }
  }

  // Полный шаг строки: leading + высота строки шрифта.
  // Обслуживает единицу around.blank: одна пустая строка = один шаг.
  // Считается от кегля документа, а не от кегля текущего элемента.
  let line-step(config, spacing) = {
    if spacing.mode == "mm" {
      spacing.value * 1mm + (config.document.line_height_em - config.document.default_leading_em) * config.document.font_size * 1pt
    } else {
      spacing.value * config.document.line_height_em * config.document.font_size * 1pt
    }
  }

  // Длина интервала в em от кегля документа (для опций spacing_before/after).
  let spacing-length(config, value) = value * config.document.font_size * 1pt

  // Нумерация страниц: пропуск первой и сдвиг начального номера.
  // Два аргумента нужны Typst для видимого номера (текущий и всего).
  let page-number(pattern, skip, start, n, total) = {
    if skip and n == 1 {
      none
    } else {
      numbering(pattern, n + start - 1, total + start - 1)
    }
  }

  // Интервал списка: tight/loose — значения реестра, auto — штатный Typst.
  let list-spacing(s, tight, loose) = {
    if s == "tight" { tight * 1em } else if s == "loose" { loose * 1em } else { auto }
  }

  // --- окружение элемента (around) ---

  // Пустая строка: weak при collapse=max (заменяет штатный интервал),
  // жёсткая при sum (добавляется к штатному). count = 0 даёт v(0).
  let around-blank(item, collapse, step) = {
    v(item.count * step, weak: collapse == "max")
  }

  // Одна вставка окружения. Обслуживает опции around.<element>.before/after.
  let around-item(config, item, collapse) = {
    if item.type == "blank" {
      let step = if item.line_spacing.mode == "multiplier" {
        // Множитель пустой строки — доля полного шага строки документа.
        item.line_spacing.value * line-step(config, config.document.line_spacing)
      } else {
        line-step(config, item.line_spacing)
      }
      around-blank(item, collapse, step)
    } else if item.type == "text" {
      let body = [#item.content]
      let styled = if item.text_override != none {
        text-override-body(body, item.text_override)
      } else {
        body
      }
      align(alignment(item.align), styled)
    } else if item.type == "line" {
      block(line(length: item.length * 1%, stroke: item.stroke_mm * 1mm))
    } else if item.type == "pagebreak" {
      pagebreak(weak: item.weak)
    }
  }

  // Оборачивает элемент вставками before/after; пустой around не меняет вывод.
  let around-with-config(config, cfg, it) = {
    if cfg.before.len() == 0 and cfg.after.len() == 0 {
      it
    } else {
      for item in cfg.before {
        around-item(config, item, cfg.collapse)
      }
      it
      for item in cfg.after {
        around-item(config, item, cfg.collapse)
      }
    }
  }

  let around-body(config, target, it) = {
    around-with-config(config, config.around.at(target), it)
  }

  // --- структурные сущности ---

  // Регистр текста по значению apply.case.
  let apply-case(s, mode) = {
    if mode == "upper" {
      upper(s)
    } else if mode == "lower" {
      lower(s)
    } else if mode == "first_upper" {
      let clusters = s.clusters()
      if clusters.len() == 0 { s } else { upper(clusters.at(0)) + clusters.slice(1).join("") }
    } else {
      s
    }
  }

  // Сопоставление текста правила: equals / contains / regex.
  let matches-text(match, text) = {
    let hay = if match.case_insensitive { lower(text) } else { text }
    let needle = if match.case_insensitive { lower(match.value) } else { match.value }
    if match.mode == "equals" {
      hay == needle
    } else if match.mode == "contains" {
      if match.target == "paragraph" { hay.starts-with(needle) } else { hay.contains(needle) }
    } else {
      regex(needle).matches(hay).len() > 0
    }
  }

  // Первая подходящая сущность; порядок в списке — приоритет.
  let find-entity(config, target, text, level) = {
    let found = none
    for entity in config.structural.entities {
      if entity.match.target != target { continue }
      if target == "heading" and entity.match.level != "any" {
        if int(entity.match.level) != level { continue }
      }
      if matches-text(entity.match, text) {
        found = entity
        break
      }
    }
    found
  }

  // Оформление текста сущности: регистр, жирность, свой стиль.
  let entity-text(entity, content) = {
    let styled = content
    if entity.apply.case != "none" {
      styled = apply-case(styled.text, entity.apply.case)
    }
    if entity.apply.bold { styled = strong(styled) }
    styled
  }

  let entity-around(config, entity) = {
    let cfg = entity.apply.around
    if cfg.before.len() == 0 and cfg.after.len() == 0 {
      none
    } else {
      cfg
    }
  }

  // --- нумерация приложений ---

  let in-appendix = state("fd-in-appendix", false)
  let appendix-counter = counter("fd-appendix-letter")
  let appendix-alphabets = (
    ru_sfu: "АБВГДЕЖИКЛМНПРСТУФХЦШЩЭЮЯ",
    latin: "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    arabic: "0123456789",
  )

  // Буква приложения по номеру 1…; после алфавита — удвоение (АА, АБ…).
  let appendix-letter(config, index) = {
    let letters = appendix-alphabets.at(config.appendix.alphabet).clusters()
    if config.appendix.overflow == "double" and index > letters.len() {
      let first = calc.floor((index - 1) / letters.len())
      let second = calc.rem(index - 1, letters.len())
      letters.at(first - 1) + letters.at(second)
    } else {
      letters.at(calc.min(index, letters.len()) - 1)
    }
  }

  // Заголовок приложения одной строкой по шаблону {service} {letter}. {title}.
  let appendix-heading-body(config, it) = {
    let text = it.body.text.trim()
    let parts = text.split(" ")
    let service = if parts.len() > 0 { parts.at(0) } else { "" }
    let title = if parts.len() > 1 { parts.slice(1).join(" ") } else { "" }
    service = apply-case(service, config.appendix.service_case)
    title = apply-case(title, config.appendix.title_case)
    let letter = appendix-letter(config, appendix-counter.get().first())
    let rendered = config.appendix.template
    rendered = rendered.replace("{service}", service)
    rendered = rendered.replace("{letter}", letter)
    rendered = rendered.replace("{title}", title)
    if config.appendix.bold { strong(rendered) } else { rendered }
  }

  let bool-value(s) = {
    if s == "true" { true } else if s == "false" { false } else { auto }
  }

  // --- текст и его локальные переопределения ---

  // Аргументы #set text(...): поля, совпадающие с нейтральными значениями,
  // не передаются, чтобы переопределение не сбрасывало внешний стиль.
  let text-args(s) = {
    let args = (size: s.font_size * 1pt)
    let f = font(s.font)
    if f != "libertinus serif" { args.insert("font", f) }
    if s.weight != "regular" { args.insert("weight", s.weight) }
    if s.style != "normal" { args.insert("style", s.style) }
    if s.fill != "black" { args.insert("fill", paint(s.fill)) }
    if s.lang != "en" { args.insert("lang", s.lang) }
    if s.region != none { args.insert("region", s.region) }
    if s.tracking != 0 { args.insert("tracking", s.tracking * 1pt) }
    if s.word_spacing != 100 { args.insert("spacing", s.word_spacing * 1%) }
    if s.hyphenate != auto { args.insert("hyphenate", s.hyphenate) }
    if not s.ligatures { args.insert("ligatures", false) }
    if s.number_type != "auto" { args.insert("number-type", s.number_type) }
    if s.number_width != "auto" { args.insert("number-width", s.number_width) }
    args
  }

  let text-override-body(it, value) = {
    if value != none {
      [#set text(..text-args(value)); #it]
    } else {
      it
    }
  }

  // --- заголовки ---

  // Нумерация с исключёнными (ненумерованными) уровнями.
  // В приложении вместо номера раздела — буква приложения.
  let heading-numbering(config) = {
    let pattern = config.heading.numbering
    if pattern == "none" {
      none
    } else {
      let hidden = ()
      for level in config.heading_levels {
        if not level.numbering_enabled { hidden.push(level.level) }
      }
      (..args) => {
        let numbers = args.pos()
        if in-appendix.get() {
          let relative = numbers.slice(1)
          if hidden.contains(numbers.len()) {
            none
          } else {
            let relative = numbers.slice(1).map(number => str(number)).join(".")
            appendix-letter(config, appendix-counter.get().first()) + "." + relative
          }
        } else if hidden.len() > 0 and hidden.contains(numbers.len()) {
          none
        } else {
          numbering(pattern, ..numbers)
        }
      }
    }
  }

  // Текст заголовка: стиль уровня или сущности и, для приложения, шаблон строки.
  let heading-body(it, level, config, entity) = {
    let body = if level.numbering_enabled {
      it
    } else {
      box(it, inset: (left: config.heading.unnumbered_indent * 1em))
    }
    let override = if entity != none and entity.apply.text_override != none {
      entity.apply.text_override
    } else {
      level.text_override
    }
    let content = if entity != none and entity.apply.appendix {
      appendix-heading-body(config, it)
    } else if entity != none {
      entity-text(entity, it.body)
    } else {
      body
    }
    text-override-body(content, override)
  }

  let show-heading(it, level, config, target) = {
    let heading-text = it.body.text.trim()
    let entity = find-entity(config, "heading", heading-text, level.level)
    let numbering-enabled = if entity == none { true } else { entity.apply.numbering }
    let outlined = if entity == none { it.outlined } else { entity.apply.outlined }
    let need-unnumber = entity != none and not numbering-enabled and it.numbering != none
    let need-outline = entity != none and outlined != it.outlined

    if need-unnumber or need-outline {
      let current = counter(heading).get()
      if current.len() > 0 {
        counter(heading).update(current.slice(0, -1) + (current.last() - 1,))
      }
      if entity != none and entity.apply.appendix and it.numbering != none {
        appendix-counter.step()
        in-appendix.update(true)
        for number in range(1, 7) {
          counter("figure-h" + str(number)).update(0)
        }
        counter("figure-n").update(0)
        counter(figure).update(0)
        counter(math.equation).update(0)
      }
      [
        #set text(size: config.document.font_size * 1pt)
        #heading(
          level: it.level,
          numbering: if need-unnumber { none } else { it.numbering },
          outlined: outlined,
          it.body,
        )
      ]
    } else {
      let heading = block(
        above: spacing-length(config, level.spacing_before),
        below: spacing-length(config, level.spacing_after),
        sticky: config.heading.keep_with_next,
        [#heading-body(it, level, config, entity)],
      )
      let aligned = if entity != none and entity.apply.align != "auto" {
        align(alignment(entity.apply.align), heading)
      } else {
        heading
      }
      let content = if level.break_before or (entity != none and entity.apply.break_before) {
        [#pagebreak(weak: true); #aligned]
      } else {
        aligned
      }
      let entity-cfg = if entity != none { entity-around(config, entity) } else { none }
      if entity-cfg != none {
        around-with-config(config, entity-cfg, content)
      } else {
        around-body(config, target, content)
      }
    }
  }

  // --- подпись рисунка по шаблону ---

  let caption-regex = regex(
    "\\{([hH][1-6]|[Nn]|[Cc][Oo][Nn][Tt][Ee][Nn][Tt])\\}",
  )

  let caption-segments(template) = {
    let segments = ()
    let last = 0
    for match in template.matches(caption-regex) {
      if match.start > last {
        segments.push(("literal", template.slice(last, match.start)))
      }
      let raw = lower(match.captures.at(0))
      if raw == "n" {
        segments.push(("n", ""))
      } else if raw == "content" {
        segments.push(("content", ""))
      } else {
        segments.push(("h", raw))
      }
      last = match.end
    }
    if last < template.len() {
      segments.push(("literal", template.slice(last, template.len())))
    }
    segments
  }

  let caption-data(template) = {
    let segments = caption-segments(template)
    let levels = ()
    let has-n = false
    let has-content = false
    for (kind, value) in segments {
      if kind == "h" {
        let level = int(value.slice(1, 2))
        if not levels.contains(level) { levels.push(level) }
      } else if kind == "n" {
        has-n = true
      } else if kind == "content" {
        has-content = true
      }
    }
    (
      segments: segments,
      levels: levels.sorted(),
      has-n: has-n,
      has-content: has-content,
    )
  }

  let caption-heading(it, level, data, counters, figure-n) = {
    if data.levels.contains(level) {
      counters.at(level - 1).step()
      for deeper in data.levels {
        if deeper > level {
          counters.at(deeper - 1).update(0)
        }
      }
      if figure-n != none { figure-n.update(0) }
    }
    it
  }

  let caption-body(it, data, counters, figure-n) = context {
    let number = if figure-n == none {
      none
    } else {
      let value = figure-n.get().first() + 1
      figure-n.step()
      str(value)
    }
    let chapter-values = (:)
    for level in data.levels {
      chapter-values.insert(
        "h" + str(level),
        counters.at(level - 1).display("1"),
      )
    }
    [
      #for (kind, value) in data.segments {
        if kind == "literal" {
          value
        } else if kind == "content" {
          it.body
        } else if kind == "n" {
          number
        } else {
          chapter-values.at(value)
        }
      }
      #if not data.has-content { [ #it.body] }
    ]
  }

  let with-caption(config, body) = {
    let template = config.figure.caption_template
    if template != none {
      let data = caption-data(template)
      if data.levels.len() > 0 or data.has-n {
        let counters = range(1, 7).map(level => counter("figure-h" + str(level)))
        let figure-n = if data.has-n { counter("figure-n") } else { none }

        set figure(numbering: none)
        // Show-правила объявляются по одному в этой же области видимости:
        // правила внутри циклов не действуют на тело после цикла.
        show heading.where(level: 1): it => caption-heading(
          it, 1, data, counters, figure-n,
        )
        show heading.where(level: 2): it => caption-heading(
          it, 2, data, counters, figure-n,
        )
        show heading.where(level: 3): it => caption-heading(
          it, 3, data, counters, figure-n,
        )
        show heading.where(level: 4): it => caption-heading(
          it, 4, data, counters, figure-n,
        )
        show heading.where(level: 5): it => caption-heading(
          it, 5, data, counters, figure-n,
        )
        show heading.where(level: 6): it => caption-heading(
          it, 6, data, counters, figure-n,
        )
        show figure.caption: it => caption-body(it, data, counters, figure-n)
        body
      } else {
        body
      }
    } else {
      body
    }
  }

  let with-text-overrides(config, body) = {
    show par: it => text-override-body(
      around-body(config, "par", it), config.par.text_override,
    )
    show list: it => text-override-body(
      around-body(config, "bullet_list", it), config.bullet_list.text_override,
    )
    show enum: it => text-override-body(
      around-body(config, "numbered_list", it), config.numbered_list.text_override,
    )
    show table.cell: it => text-override-body(it, config.table.text_override)
    show quote: it => text-override-body(
      around-body(config, "quote", it), config.quote.text_override,
    )
    show raw.where(block: true): it => text-override-body(
      around-body(config, "raw", it), config.raw.text_override,
    )
    show raw.where(block: false): it => text-override-body(
      it, config.raw.text_override,
    )
    show figure: it => text-override-body(
      around-body(
        config,
        if it.kind == table { "table" } else { "figure" },
        it,
      ),
      config.figure.text_override,
    )
    show footnote.entry: it => text-override-body(it, config.footnote.text_override)
    show terms: it => text-override-body(
      around-body(config, "terms", it), config.terms.text_override,
    )
    show outline: it => text-override-body(it, config.outline.text_override)
    show math.equation.where(block: true): it => {
      let equation = if config.equation.body_indent != 0 {
        pad(left: config.equation.body_indent * 1mm, it)
      } else {
        it
      }
      text-override-body(
        around-body(config, "equation", equation), config.equation.text_override,
      )
    }
    show math.equation.where(block: false): it => text-override-body(
      it, config.equation.text_override,
    )
    body
  }

  // Поля страницы: книжные или альбомные. Обслуживает page.margin_landscape_*.
  let page-margins(page) = if page.flipped {
    (
      top: page.margin_landscape_top * 1mm,
      bottom: page.margin_landscape_bottom * 1mm,
      left: page.margin_landscape_left * 1mm,
      right: page.margin_landscape_right * 1mm,
    )
  } else {
    (
      top: page.margin_top * 1mm,
      bottom: page.margin_bottom * 1mm,
      left: page.margin_left * 1mm,
      right: page.margin_right * 1mm,
    )
  }

  // --- применение конфига ---

  let apply(config, body) = {
    // Страница.
    set page(
      paper: config.page.paper,
      flipped: config.page.flipped,
      margin: page-margins(config.page),
      columns: config.page.columns,
      numbering: if config.page.numbering == "none" {
        none
      } else if config.page.numbering_skip_first or config.page.numbering_start != 1 {
        page-number.with(
          config.page.numbering,
          config.page.numbering_skip_first,
          config.page.numbering_start,
        )
      } else {
        config.page.numbering
      },
      number-align: alignment(config.page.number_align),
    )

    // Глобальный текст.
    set text(..text-args(config.document))

    // Абзац: leading из документа, остальное из par.
    let par-args = (
      leading: line-pitch(config),
      spacing: config.par.spacing * 1mm,
    )
    if config.document.justify { par-args.insert("justify", true) }
    if config.par.first_line_indent != 0 {
      par-args.insert(
        "first-line-indent",
        (amount: config.par.first_line_indent * 1mm, all: true),
      )
    }
    if config.par.hanging_indent != 0 {
      par-args.insert("hanging-indent", config.par.hanging_indent * 1mm)
    }
    if config.par.linebreaks != "auto" {
      par-args.insert("linebreaks", config.par.linebreaks)
    }
    set par(..par-args)

    // Заголовки.
    set heading(numbering: heading-numbering(config))

    // Штатные интервалы блоков: значения реестра вместо скрытых констант Typst.
    show figure: set block(
      above: spacing-length(config, config.figure.spacing_before),
      below: spacing-length(config, config.figure.spacing_after),
    )
    show figure.where(kind: table): set block(
      above: spacing-length(config, config.table.spacing_before),
      below: spacing-length(config, config.table.spacing_after),
    )
    show math.equation.where(block: true): set block(
      above: spacing-length(config, config.equation.spacing_before),
      below: spacing-length(config, config.equation.spacing_after),
    )
    show raw.where(block: true): set block(
      above: spacing-length(config, config.raw.spacing_before),
      below: spacing-length(config, config.raw.spacing_after),
    )
    show quote: set block(
      above: spacing-length(config, config.quote.spacing_before),
      below: spacing-length(config, config.quote.spacing_after),
    )
    show list: set block(
      above: spacing-length(config, config.bullet_list.spacing_before),
      below: spacing-length(config, config.bullet_list.spacing_after),
    )
    show enum: set block(
      above: spacing-length(config, config.numbered_list.spacing_before),
      below: spacing-length(config, config.numbered_list.spacing_after),
    )
    // Обёртка, а не set block: spacing списка определений применяется один раз
    // ко всему блоку, а не к каждому внутреннему блоку термина.
    show terms: it => block(
      above: spacing-length(config, config.terms.spacing_before),
      below: spacing-length(config, config.terms.spacing_after),
      it,
    )

    // Маркированный список.
    set list(
      tight: config.bullet_list.tight,
      indent: config.bullet_list.indent * 1mm,
      body-indent: config.bullet_list.body_indent * 1mm,
      spacing: list-spacing(config.bullet_list.spacing, config.bullet_list.tight_spacing, config.bullet_list.loose_spacing),
      marker: config.bullet_list.marker,
    )

    // Нумерованный список.
    let enum-args = (
      tight: config.numbered_list.tight,
      indent: config.numbered_list.indent * 1mm,
      body-indent: config.numbered_list.body_indent * 1mm,
      spacing: list-spacing(config.numbered_list.spacing, config.numbered_list.tight_spacing, config.numbered_list.loose_spacing),
    )
    if config.numbered_list.numbering != "1." {
      enum-args.insert("numbering", config.numbered_list.numbering)
    }
    if config.numbered_list.start != none {
      enum-args.insert("start", config.numbered_list.start)
    }
    if config.numbered_list.full { enum-args.insert("full", true) }
    if config.numbered_list.reversed { enum-args.insert("reversed", true) }
    if config.numbered_list.number_align != "end+top" {
      enum-args.insert(
        "number-align",
        alignment(config.numbered_list.number_align),
      )
    }
    set enum(..enum-args)

    // Таблица.
    let table-args = (
      stroke: config.table.stroke * 1mm,
      inset: config.table.inset * 1mm,
    )
    if config.table.align != "auto" {
      table-args.insert("align", alignment(config.table.align))
    }
    if config.table.fill != "none" {
      table-args.insert("fill", paint(config.table.fill))
    }
    set table(..table-args)

    // Изображение и рисунок.
    let image-args = (
      width: if config.figure.width == 0 {
        auto
      } else {
        config.figure.width * 1mm
      },
      height: if config.figure.height == 0 {
        auto
      } else {
        config.figure.height * 1mm
      },
    )
    if config.figure.fit != "cover" {
      image-args.insert("fit", config.figure.fit)
    }
    set image(..image-args)

    let figure-args = (gap: config.figure.gap * 1mm)
    if config.figure.placement != "none" {
      figure-args.insert(
        "placement",
        if config.figure.placement == "auto" {
          auto
        } else if config.figure.placement == "top" {
          top
        } else {
          bottom
        },
      )
    }
    if not config.figure.outlined {
      figure-args.insert("outlined", false)
    }
    set figure(..figure-args)

    // Сноски.
    set footnote(numbering: config.footnote.marker_format)
    set footnote.entry(
      clearance: config.footnote.clearance * 1mm,
      gap: config.footnote.gap * 1mm,
      indent: config.footnote.indent * 1mm,
      separator: line(
        length: config.footnote.separator_length * 1%,
        stroke: config.footnote.separator_stroke * 1mm,
      ),
    )

    // Цитата.
    let quote-args = (block: config.quote.block)
    if config.quote.quotes != "auto" {
      quote-args.insert("quotes", bool-value(config.quote.quotes))
    }
    set quote(..quote-args)
    show quote: set pad(x: config.quote.indent * 1mm)

    // Список определений.
    set terms(
      tight: config.terms.tight,
      indent: config.terms.indent * 1mm,
      hanging-indent: config.terms.hanging_indent * 1mm,
      spacing: list-spacing(config.terms.spacing, config.terms.tight_spacing, config.terms.loose_spacing),
    )

    // Код: правила нужны только при отличии от дефолтов Typst.
    if (
      config.raw.tab_size != 2
        or config.raw.align != "start"
        or config.raw.theme != "auto"
    ) {
      let raw-args = (:)
      if config.raw.tab_size != 2 {
        raw-args.insert("tab-size", config.raw.tab_size)
      }
      if config.raw.align != "start" {
        raw-args.insert("align", alignment(config.raw.align))
      }
      if config.raw.theme == "none" {
        raw-args.insert("theme", none)
      }
      set raw(..raw-args)
    }

    // Оглавление.
    let outline-args = (:)
    if config.outline.depth != none {
      outline-args.insert("depth", config.outline.depth)
    }
    if config.outline.indent_mode == "none" {
      outline-args.insert("indent", 0mm)
    } else if config.outline.indent_mode == "custom" {
      outline-args.insert("indent", config.outline.indent_mm * 1mm)
    }
    if outline-args.len() > 0 {
      set outline(..outline-args)
    }

    // Стили уровней заголовков. Идут после правил счётчиков подписей.
    show heading.where(level: 1): it => show-heading(
      it, config.heading_levels.at(0), config, "heading_1",
    )
    show heading.where(level: 2): it => show-heading(
      it, config.heading_levels.at(1), config, "heading_2",
    )
    show heading.where(level: 3): it => show-heading(
      it, config.heading_levels.at(2), config, "heading_3",
    )
    show heading.where(level: 4): it => show-heading(
      it, config.heading_levels.at(3), config, "heading_4",
    )
    show heading.where(level: 5): it => show-heading(
      it, config.heading_levels.at(4), config, "heading_5",
    )
    show heading.where(level: 6): it => show-heading(
      it, config.heading_levels.at(5), config, "heading_6",
    )

    let content = with-text-overrides(config, with-caption(config, body))
    content
  }

  (apply: apply)
}
