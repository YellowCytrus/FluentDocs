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

  // Буква текущего приложения для подписей рисунков/таблиц.
  // Обслуживает caption.<kind> и сброс нумерации в приложении.
  let appendix-state = state("fd-appendix-letter", none)

  // Глубина, номера предков и отступы тела для собственного рендера enum.
  // Нужны, чтобы продолжение пункта начиналось у левого поля, а вложенные
  // списки сохраняли относительный отступ.
  let list-depth-state = state("fd-list-depth", 0)
  let list-counts-state = state("fd-list-counts", (0, 0, 0, 0, 0, 0))
  let list-body-offset-state = state(
    "fd-list-body-offset",
    (0pt, 0pt, 0pt, 0pt, 0pt, 0pt),
  )

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
  // total необязателен: стандартная запись Typst вызывает функцию номера
  // страницы только с текущим номером, без общего числа страниц.
  let page-number(pattern, skip, start, n, ..rest) = {
    let total = if rest.pos().len() > 0 { rest.pos().at(0) } else { n }
    if skip and n == 1 {
      none
    } else if pattern.contains("/") {
      numbering(pattern, n + start - 1, total + start - 1)
    } else {
      numbering(pattern, n + start - 1)
    }
  }

  // Интервал списка: tight/loose — значения реестра, auto — штатный Typst.
  let list-spacing(s, tight, loose) = {
    if s == "tight" { tight * 1em } else if s == "loose" { loose * 1em } else { auto }
  }

  // Алфавиты нумерованных списков (без Ё, З, Й, О, Ч, Ь, Ы, Ъ для ru_sfu).
  let list-alphabets = (
    ru_sfu: "абвгдежиклмнпрстуфхцшщэюя",
    latin: "abcdefghijklmnopqrstuvwxyz",
  )

  // Буква списка по номеру 1…; после алфавита — удвоение, без падения.
  let list-letter-label(letters, index) = {
    let value = calc.max(1, index)
    let out = ()
    while value > 0 {
      value = value - 1
      out.push(letters.at(calc.rem(value, letters.len())))
      value = calc.floor(value / letters.len())
    }
    out.rev().join("")
  }

  // Маркер списка по уровням: {n}, {letter} или шаблон Typst.
  // Обслуживает numbered_list.level_formats, alphabet, full, numbering.
  let list-marker(config, values) = {
    let level = values.len()
    let formats = config.numbered_list.level_formats
    let rendered = if formats.len() == 0 {
      let shown = if config.numbered_list.full {
        values
      } else {
        (values.last(),)
      }
      numbering(config.numbered_list.numbering, ..shown)
    } else {
      let format = formats.at(calc.min(level, formats.len()) - 1).format
      let current = values.last()
      let has-letter = format.contains("{letter}")
      let has-number = format.contains("{n}")
      let base = if has-letter {
        let letters = list-alphabets.at(config.numbered_list.alphabet).clusters()
        format.replace("{letter}", list-letter-label(letters, current))
      } else {
        format
      }
      if has-letter or has-number {
        base.replace("{n}", str(current))
      } else {
        numbering(base, current)
      }
    }
    let prefix = ""
    if config.numbered_list.full and level > 1 and formats.len() > 0 {
      for value in values.slice(0, level - 1) {
        prefix = prefix + str(value) + "."
      }
    }
    if prefix == "" { rendered } else { [#prefix #rendered] }
  }

  // Собственный рендер enum: маркер ставится в поле, тело идёт потоком.
  // Обслуживает numbered_list.wrap_mode: left_margin и body_text.
  let list-render(config, it) = {
    let depth = list-depth-state.get()
    let counts = list-counts-state.get()
    let children = it.children
    let count = children.len()
    let reversed = it.reversed or (depth == 0 and config.numbered_list.reversed)
    let first-number = if depth == 0 and config.numbered_list.start != none {
      config.numbered_list.start
    } else if it.start == auto {
      if reversed { count } else { 1 }
    } else {
      it.start
    }
    let entries = ()
    for (index, child) in children.enumerate() {
      let number = if child.number != auto {
        child.number
      } else if reversed {
        first-number - index
      } else {
        first-number + index
      }
      let values = counts.slice(0, depth)
      values.push(number)
      let next-counts = ()
      for (idx, value) in counts.enumerate() {
        next-counts.push(
          if idx == depth { number } else if idx > depth { 0 } else { value },
        )
      }
      entries.push((
        marker: list-marker(config, values),
        body: child.body,
        counts: next-counts,
      ))
    }

    let marker-width = 0pt
    for entry in entries {
      let width = measure(entry.marker).width
      if width > marker-width { marker-width = width }
    }
    let gap = config.numbered_list.body_indent * 1mm
    let spacing = list-spacing(
      config.numbered_list.spacing,
      config.numbered_list.tight_spacing,
      config.numbered_list.loose_spacing,
    )
    // auto — штатный шаг строки, явные tight/loose — ровно своё значение.
    // tight не добавляет par.spacing и не меняет auto.
    let item-spacing = if spacing == auto { line-pitch(config) } else { spacing }

    // Вложенный список в left_margin начинается от текста родителя;
    // в body_text тело уже сдвинуто, поэтому достаточно indent.
    let parent-offset = if depth > 0 {
      list-body-offset-state.get().at(depth - 1)
    } else {
      0pt
    }
    let list-offset = config.numbered_list.indent * 1mm
    if depth > 0 and config.numbered_list.wrap_mode == "left_margin" {
      list-offset = list-offset + parent-offset
    }
    let body-offset = marker-width + gap
    let vertical = if config.numbered_list.number_align.contains("bottom") {
      bottom
    } else {
      top
    }
    let horizontal = if config.numbered_list.number_align.contains("start") {
      start
    } else {
      end
    }
    // В left_margin продолжение идёт у левого поля, поэтому нижний маркер
    // ушёл бы под последнюю строку. Для bottom маркер выносится в поле
    // страницы на ширину колонки маркера с зазором body_indent.
    let marker-shift = if vertical == bottom and config.numbered_list.wrap_mode == "left_margin" {
      -body-offset
    } else {
      0pt
    }

    let rendered = ()
    for (index, entry) in entries.enumerate() {
      let marker = block(
        width: marker-width,
        align(horizontal, entry.marker),
      )
      let next-offsets = ()
      for (idx, value) in list-body-offset-state.get().enumerate() {
        next-offsets.push(if idx == depth { body-offset } else { value })
      }
      let item = block(width: 100%, {
        place(vertical + left, dx: marker-shift, marker)
        [#list-depth-state.update(depth + 1)]
        [#list-counts-state.update(entry.counts)]
        [#list-body-offset-state.update(next-offsets)]
        if config.numbered_list.wrap_mode == "left_margin" {
          set par(first-line-indent: (amount: body-offset, all: true))
          entry.body
        } else {
          block(inset: (left: body-offset), entry.body)
        }
        [#list-depth-state.update(depth)]
      })
      rendered.push(item)
      if index < count - 1 {
        rendered.push(v(item-spacing))
      }
    }
    block(
      inset: (left: list-offset),
      stack(dir: ttb, spacing: 0pt, ..rendered),
    )
  }

  // --- окружение элемента (around) ---

  // Пустая строка: полный шаг строки; на верху страницы пропадает.
  // Обслуживает элемент around item type=blank (AGENTS 5.1).
  let around-blank(config, item) = {
    let step = if item.line_spacing.mode == "multiplier" {
      // Множитель пустой строки — доля полного шага строки документа.
      item.line_spacing.value * line-step(config, config.document.line_spacing)
    } else {
      line-step(config, item.line_spacing)
    }
    let margin = if config.page.flipped {
      config.page.margin_landscape_top
    } else {
      config.page.margin_top
    }
    context {
      // Верх страницы: here().position().y близко к верхнему полю (плюс
      // высота строки). Пустая строка там не создаёт зазор.
      if here().position().y > margin * 1mm + 12pt {
        v(step)
      }
    }
  }

  // Одна вставка окружения. Обслуживает опции around.<element>.before/after.
  // skip-pagebreak нужен для подписи: разрыв страницы внутри figure
  // Typst запрещает, поэтому его выносит наружу show figure.
  let around-item(config, item, skip-pagebreak: false) = {
    if item.type == "blank" {
      around-blank(config, item)
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
    } else if item.type == "pagebreak" and not skip-pagebreak {
      pagebreak(weak: item.weak)
    }
  }

  // Все вставки списка; пустой список ничего не добавляет.
  let around-items(config, items, skip-pagebreak: false) = {
    for item in items {
      around-item(config, item, skip-pagebreak: skip-pagebreak)
    }
  }

  // Разрывы страниц из окружения подписи вне figure: внутри подписи
  // pagebreak запрещён Typst.
  let around-pagebreaks(items) = {
    for item in items {
      if item.type == "pagebreak" {
        pagebreak(weak: item.weak)
      }
    }
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

  // Текст из content с сохранением вложенных strong/emph/sequence.
  // Нужен для форматированных заголовков: у strong нет поля text.
  let content-text(content) = {
    if content.func() == text {
      content.text
    } else {
      let fields = content.fields()
      if "children" in fields {
        let out = ""
        for child in fields.children {
          out = out + content-text(child)
        }
        out
      } else if "body" in fields {
        content-text(fields.body)
      } else {
        ""
      }
    }
  }

  // Регистр для content с сохранением разметки (абзацные сущности).
  let content-case(content, mode) = {
    if mode == "upper" {
      upper(content)
    } else if mode == "lower" {
      lower(content)
    } else if mode == "first_upper" {
      if content.func() == text {
        let clusters = content.text.clusters()
        if clusters.len() == 0 {
          content
        } else {
          upper(clusters.at(0)) + lower(clusters.slice(1).join(""))
        }
      } else {
        content
      }
    } else {
      content
    }
  }

  // Сопоставление текста правила: equals / contains / starts_with / regex.
  let matches-text(match, text) = {
    let hay = if match.case_insensitive { lower(text) } else { text }
    let needle = if match.case_insensitive { lower(match.value) } else { match.value }
    if match.mode == "equals" {
      hay == needle
    } else if match.mode == "contains" {
      hay.contains(needle)
    } else if match.mode == "starts_with" {
      hay.starts-with(needle)
    } else {
      hay.contains(regex(needle))
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

  // Оформление текста сущности: регистр, жирность.
  let entity-text(entity, content) = {
    let styled = content
    if entity.apply.case != "none" {
      styled = apply-case(styled.text, entity.apply.case)
    }
    if entity.apply.bold { styled = strong(styled) }
    styled
  }

  // Непустое окружение сущности или none.
  let entity-around(config, entity) = {
    let cfg = entity.apply.around
    if cfg.before.len() == 0 and cfg.after.len() == 0 {
      none
    } else {
      cfg
    }
  }

  // --- нумерация приложений и своих счётчиков ---

  let appendix-alphabets = (
    ru_sfu: "АБВГДЕЖИКЛМНПРСТУФХЦШЩЭЮЯ",
    latin: "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
  )

  // Номер приложения: arabic — 1-based десятичное число (1, 2, …, 999),
  // остальные алфавиты — буквы. После алфавита — удвоение (АА, АБ…), после
  // исчерпания удвоения — тройное сочетание (ААА, ААБ…); это продолжение
  // режима double, а не отдельный режим. Индекс не выходит за границы массива
  // (appendix.start до 999 и длинные серии приложений).
  let appendix-letter(config, index) = {
    let value = calc.max(1, index)
    if config.appendix.alphabet == "arabic" {
      str(value)
    } else {
      let letters = appendix-alphabets.at(config.appendix.alphabet).clusters()
      if config.appendix.overflow == "double" {
        let digits = ()
        while value > 0 {
          value = value - 1
          digits.push(letters.at(calc.rem(value, letters.len())))
          value = calc.floor(value / letters.len())
        }
        digits.rev().join("")
      } else {
        letters.at(calc.min(value, letters.len()) - 1)
      }
    }
  }

  // Собственный счётчик правила берётся из group или id.
  let entity-group(entity) = {
    if entity.numbering.group == "" { entity.id } else { entity.numbering.group }
  }

  // Приложение — явный пресет numbering.kind, а не догадка по шаблону.
  let is-appendix(entity) = {
    if entity == none { false } else { entity.numbering.kind == "appendix" }
  }

  // Увеличивает счётчик уровня и сбрасывает более глубокие.
  let step-array(values, level) = {
    range(0, 6).map(i => {
      if i == level - 1 { values.at(i) + 1 }
      else if i > level - 1 { 0 }
      else { values.at(i) }
    })
  }

  // Строка номера своего правила: Typst-шаблон или плейсхолдер {letter}.
  let own-base-value(config, entity, family) = {
    let shifted = family + entity.numbering.start - 1
    if entity.numbering.template.contains("{letter}") {
      entity.numbering.template.replace(
        "{letter}",
        appendix-letter(config, shifted),
      )
    } else {
      numbering(entity.numbering.template, shifted)
    }
  }

  // Подпись подраздела своего счётчика: {prefix} и {n}.
  let own-sub-text(entity, base, subs, level) = {
    let parts = range(1, level).map(i => str(subs.at(i)))
    entity.numbering.sub_template
      .replace("{prefix}", base)
      .replace("{n}", parts.join("."))
  }

  // Заголовок приложения целиком: шаблон appendix.template с {title} в любом месте.
  // apply.case сущности применяется после appendix.*_case; apply.bold действует
  // вместе с appendix.bold (достаточно одного).
  let appendix-heading-text(config, entity, heading-text, letter) = {
    let parts = heading-text.split(" ").filter(part => part != "")
    let service = if parts.len() > 0 { parts.at(0) } else { "" }
    let title = if parts.len() > 1 { parts.slice(1).join(" ") } else { "" }
    let rendered = config.appendix.template
      .replace("{service}", apply-case(service, config.appendix.service_case))
      .replace("{letter}", letter)
      .replace("{title}", apply-case(title, config.appendix.title_case))
    let cased = apply-case(rendered, entity.apply.case)
    if config.appendix.bold or entity.apply.bold { strong(cased) } else { cased }
  }

  // Подзаголовок приложения: буква вместо номера раздела, sub_template.
  // apply.case/bold текущего правила подзаголовка применяется после
  // appendix.title_case; appendix.bold действует глобально.
  let appendix-sub-text(config, current, parent, heading-text, letter, subs, level) = {
    let parts = range(1, level).map(i => str(subs.at(i)))
    let prefix = parent.numbering.sub_template
      .replace("{prefix}", letter)
      .replace("{n}", parts.join("."))
    let title = apply-case(heading-text, config.appendix.title_case)
    let rendered = prefix + " " + title
    let cased = if current == none {
      rendered
    } else {
      apply-case(rendered, current.apply.case)
    }
    let bold = if current == none {
      config.appendix.bold
    } else {
      config.appendix.bold or current.apply.bold
    }
    if bold { strong(cased) } else { cased }
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
  // Приложения и свои счётчики выводят номер вручную (см. heading-content).
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
        if hidden.len() > 0 and hidden.contains(numbers.len()) {
          none
        } else {
          numbering(pattern, ..numbers)
        }
      }
    }
  }

  // Идентификатор вида элемента верхнего уровня.
  let element-kind(it) = {
    let fields = it.fields()
    if it.func() == heading {
      "heading_" + str(it.depth)
    } else if it.func() == figure {
      if "kind" in fields and fields.kind == table { "table" } else { "figure" }
    } else if it.func() == math.equation and "block" in fields and fields.block {
      "equation"
    } else if it.func() == quote {
      "quote"
    } else if it.func() == raw and "block" in fields and fields.block {
      "raw"
    } else if it.func() == terms {
      "terms"
    } else if it.func() == list.item {
      "bullet_list"
    } else if it.func() == enum.item {
      "numbered_list"
    } else {
      "par"
    }
  }

  // Окружение элемента: у заголовка приоритет у правила сущности.
  let around-config(config, kind, it) = {
    if kind.starts-with("heading_") and it.func() == heading {
      let entity = find-entity(config, "heading", content-text(it.body).trim(), it.depth)
      if entity != none and entity-around(config, entity) != none {
        entity.apply.around
      } else {
        config.around.at(kind)
      }
    } else if kind == "par" {
      let entity = find-entity(
        config,
        "paragraph",
        content-text(it).trim(),
        0,
      )
      if entity != none and entity-around(config, entity) != none {
        entity.apply.around
      } else {
        config.around.at(kind)
      }
    } else {
      config.around.at(kind)
    }
  }

  // Политика столкновения: первое правило по виду предыдущего, иначе keep_both.
  let collision-policy(cfg, previous) = {
    let policy = "keep_both"
    for rule in cfg.before_collisions {
      if rule.previous == "any" or rule.previous == previous {
        policy = rule.policy
        break
      }
    }
    policy
  }

  // Вставки на границе двух элементов по политике 5.1.
  let collision-content(config, cfg, previous, previous-after) = {
    let current-before = cfg.before
    if previous == none {
      around-items(config, current-before)
    } else if previous-after.len() == 0 {
      around-items(config, current-before)
    } else if current-before.len() == 0 {
      around-items(config, previous-after)
    } else {
      let policy = collision-policy(cfg, previous)
      if policy == "keep_previous" {
        around-items(config, previous-after)
      } else if policy == "keep_current" {
        around-items(config, current-before)
      } else if policy == "drop_both" {
        none
      } else {
        around-items(config, previous-after) + around-items(config, current-before)
      }
    }
  }

  // Склейка контента: none означает «пока пусто».
  let add-content(current, next) = {
    if current == none { next } else { current + next }
  }

  // Контент заголовка: один авторитетный heading, без второго внутри show.
  // Номера своих счётчиков и приложений приходят готовой строкой (custom-body)
  // и выводятся при numbering: none, поэтому #outline() видит тот же текст.
  let heading-content(config, it, custom-body: none, force-none: false) = {
    let level = it.depth
    let level-cfg = config.heading_levels.at(level - 1)
    let heading-text = content-text(it.body).trim()
    let entity = find-entity(config, "heading", heading-text, level)
    let numbering-value = if force-none { none } else { heading-numbering(config) }
    let body = if custom-body != none {
      custom-body
    } else if entity != none {
      entity-text(entity, it.body)
    } else if not level-cfg.numbering_enabled {
      box(it.body, inset: (left: config.heading.unnumbered_indent * 1em))
    } else {
      it.body
    }

    let override = if entity != none and entity.apply.text_override != none {
      entity.apply.text_override
    } else {
      level-cfg.text_override
    }
    let body = text-override-body(body, override)
    let heading-el = heading(
      level: level,
      numbering: numbering-value,
      outlined: if entity == none { true } else { entity.apply.outlined },
      body,
    )
    let block-el = block(
      above: spacing-length(config, level-cfg.spacing_before),
      below: spacing-length(config, level-cfg.spacing_after),
      sticky: config.heading.keep_with_next,
      heading-el,
    )
    let aligned = if entity != none and entity.apply.align != "auto" {
      align(alignment(entity.apply.align), block-el)
    } else {
      block-el
    }
    if level-cfg.break_before or (entity != none and entity.apply.break_before) {
      pagebreak(weak: true) + aligned
    } else {
      aligned
    }
  }

  // Группирует верхнеуровневые элементы в единицы вида элемента.
  let body-units(body) = {
    let units = ()
    let current-kind = none
    let current = none
    for child in body.children {
      let kind = element-kind(child)
      if kind == "par" {
        if child.func() == parbreak {
          if current-kind == "par" {
            current = current + child
            units = units + ((kind: current-kind, content: current),)
            current-kind = none
            current = none
          }
        } else if current-kind == "par" {
          current = current + child
        } else {
          if current-kind != none {
            units = units + ((kind: current-kind, content: current),)
          }
          current-kind = "par"
          current = child
        }
      } else if kind == "bullet_list" or kind == "numbered_list" {
        if current-kind == kind {
          current = current + child
        } else {
          if current-kind != none {
            units = units + ((kind: current-kind, content: current),)
          }
          current-kind = kind
          current = child
        }
      } else {
        if current-kind != none {
          units = units + ((kind: current-kind, content: current),)
          current-kind = none
          current = none
        }
        units = units + ((kind: kind, content: child),)
      }
    }
    if current-kind != none {
      units = units + ((kind: current-kind, content: current),)
    }
    units
  }

  // Проход по телу: вставки around с политиками столкновений и заголовки.
  let with-around-and-headings(config, body) = {
    let out = none
    let previous = none
    let previous-after = ()
    let appendix-active = none
    let own-active = none
    let none-active = false
    let own-families = (:)
    let own-subs = (:)
    let appendix-count = 0
    let appendix-subs = (0, 0, 0, 0, 0, 0)
    for unit in body-units(body) {
      let kind = unit.kind
      let cfg = around-config(config, kind, unit.content)
      let content = if kind.starts-with("heading_") {
        let heading = unit.content
        let level = heading.depth
        let text = content-text(heading.body).trim()
        let entity = find-entity(config, "heading", text, level)
        let appendix = level == 1 and is-appendix(entity)
        let mode = if entity == none { "continue" } else { entity.numbering.mode }
        let group = if entity == none { "" } else { entity-group(entity) }
        let custom-body = none
        let force-none = false
        let before = none
        let appendix-letter-value = none

        if appendix {
          appendix-count = appendix-count + 1
          appendix-subs = (0, 0, 0, 0, 0, 0)
          let letter = appendix-letter(
            config,
            appendix-count + entity.numbering.start - 1,
          )
          appendix-letter-value = letter
          custom-body = appendix-heading-text(config, entity, text, letter)
          custom-body = custom-body + metadata((
            fd-appendix-kind: "heading",
            fd-appendix-letter: letter,
            fd-appendix-level: 1,
          ))
          force-none = true
          // Сброс счётчиков рисунков/таблиц/формул в начале приложения.
          for number in range(1, 7) {
            before = add-content(
              before,
              [#counter("figure-h" + str(number)).update(0)],
            )
            before = add-content(
              before,
              [#counter("table-h" + str(number)).update(0)],
            )
            before = add-content(
              before,
              [#counter("formula-h" + str(number)).update(0)],
            )
          }
          before = add-content(
            before,
            [
              #counter("figure-n").update(0)
              #counter("table-n").update(0)
              #counter("formula-n").update(0)
              #counter(figure).update(0)
              #counter(math.equation).update(0)
            ],
          )
        } else if appendix-active != none and level > 1 {
          appendix-subs = step-array(appendix-subs, level)
          let parent = appendix-active
          let letter = appendix-letter(
            config,
            appendix-count + parent.numbering.start - 1,
          )
          custom-body = appendix-sub-text(
            config,
            entity,
            parent,
            text,
            letter,
            appendix-subs,
            level,
          )
          custom-body = custom-body + metadata((
            fd-appendix-kind: "sub",
            fd-appendix-letter: letter,
            fd-appendix-level: level,
          ))
          force-none = true
        } else if mode == "own" {
          let family = if own-families.keys().contains(group) {
            own-families.at(group)
          } else {
            0
          }
          let subs = if own-subs.keys().contains(group) {
            own-subs.at(group)
          } else {
            (0, 0, 0, 0, 0, 0)
          }
          let active-group = if own-active == none {
            ""
          } else {
            entity-group(own-active)
          }
          if level == 1 or active-group != group {
            family = family + 1
            subs = (0, 0, 0, 0, 0, 0)
          }
          subs = step-array(subs, level)
          own-families.insert(group, family)
          own-subs.insert(group, subs)
          let base = own-base-value(config, entity, family)
          let prefix = if level == 1 {
            base
          } else {
            own-sub-text(entity, base, subs, level)
          }
          custom-body = [#prefix #entity-text(entity, heading.body)]
          force-none = true
        } else if mode == "none" or (none-active and level > 1) {
          force-none = true
        } else if own-active != none and level > 1 and (entity == none or mode == "continue") {
          let parent = own-active
          let parent-group = entity-group(parent)
          let family = own-families.at(parent-group)
          let subs = if own-subs.keys().contains(parent-group) {
            own-subs.at(parent-group)
          } else {
            (0, 0, 0, 0, 0, 0)
          }
          subs = step-array(subs, level)
          own-subs.insert(parent-group, subs)
          let base = own-base-value(config, parent, family)
          let prefix = own-sub-text(parent, base, subs, level)
          let body = if entity == none {
            heading.body
          } else {
            entity-text(entity, heading.body)
          }
          custom-body = [#prefix #body]
          force-none = true
        }

        if level == 1 {
          before = add-content(
            before,
            [#appendix-state.update(appendix-letter-value)],
          )
        }
        let rendered = heading-content(
          config,
          heading,
          custom-body: custom-body,
          force-none: force-none,
        )
        let rendered = if before == none { rendered } else { before + rendered }

        if appendix {
          appendix-active = entity
          own-active = none
          none-active = false
        } else if appendix-active != none and level > 1 {
          none-active = false
        } else if mode == "own" {
          appendix-active = none
          own-active = entity
          none-active = false
        } else if mode == "none" or (none-active and level > 1) {
          if level == 1 {
            appendix-active = none
            own-active = none
          }
          none-active = true
        } else if level == 1 {
          appendix-active = none
          own-active = none
          none-active = false
        }
        rendered
      } else if kind == "par" {
        let text = content-text(unit.content).trim()
        let entity = find-entity(config, "paragraph", text, 0)
        if entity == none {
          unit.content
        } else {
          let body = content-case(unit.content, entity.apply.case)
          let body = if entity.apply.bold { strong(body) } else { body }
          let body = if entity.apply.text_override != none {
            text-override-body(body, entity.apply.text_override)
          } else {
            body
          }
          let body = if entity.apply.align != "auto" {
            align(alignment(entity.apply.align), body)
          } else {
            body
          }
          // Абзацные правила («где…») выводятся без отступа первой строки.
          [#set par(first-line-indent: 0pt); #body]
        }
      } else {
        unit.content
      }
      let spacer = collision-content(config, cfg, previous, previous-after)
      out = add-content(out, spacer + content)
      previous = kind
      previous-after = cfg.after
    }
    let tail = around-items(config, previous-after)
    if out == none { tail } else { out + tail }
  }

  // --- подписи рисунков и таблиц ---

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

  // Счётчики подписи: отдельные для рисунков и таблиц.
  let caption-heading(it, level, data, counters, number-counter) = {
    if data != none and data.levels.contains(level) {
      counters.at(level - 1).step()
      for deeper in data.levels {
        if deeper > level {
          counters.at(deeper - 1).update(0)
        }
      }
      if number-counter != none { number-counter.update(0) }
    }
    it
  }

  // Значение {hN}: в приложении уровень 1 заменяется буквой приложения.
  let caption-chapter-value(level, counters) = {
    if level == 1 {
      let letter = appendix-state.get()
      if letter != none { letter } else { counters.at(0).display("1") }
    } else {
      counters.at(level - 1).display("1")
    }
  }

  let caption-body(
    config,
    caption-cfg,
    it,
    data,
    counters,
    number-counter,
  ) = context {
    let number = if number-counter == none {
      none
    } else {
      let value = number-counter.get().first() + 1
      number-counter.step()
      str(value)
    }
    let chapter-values = (:)
    for level in data.levels {
      chapter-values.insert(
        "h" + str(level),
        caption-chapter-value(level, counters),
      )
    }
    let content = [
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
      #if not data.has-content { [#caption-cfg.caption_separator #it.body] }
    ]
    let content = text-override-body(content, caption-cfg.caption_text_override)
    let before = around-items(config, caption-cfg.caption_around.before, skip-pagebreak: true)
    let after = around-items(config, caption-cfg.caption_around.after, skip-pagebreak: true)
    if before == none and after == none {
      content
    } else if before == none {
      content + after
    } else if after == none {
      before + content
    } else {
      before + content + after
    }
  }

  // Подпись без шаблона: только текст, без английского «Table 1».
  let caption-plain(config, caption-cfg, it) = {
    let content = text-override-body(it.body, caption-cfg.caption_text_override)
    let before = around-items(config, caption-cfg.caption_around.before, skip-pagebreak: true)
    let after = around-items(config, caption-cfg.caption_around.after, skip-pagebreak: true)
    if before == none and after == none {
      content
    } else if before == none {
      content + after
    } else if after == none {
      before + content
    } else {
      before + content + after
    }
  }

  // Нативная подпись рисунка без шаблона: сохраняет «Figure 1: …»,
  // но применяет окружение, стиль и выравнивание из опций.
  let caption-native(config, caption-cfg, it) = {
    let content = text-override-body(it, caption-cfg.caption_text_override)
    let before = around-items(config, caption-cfg.caption_around.before, skip-pagebreak: true)
    let after = around-items(config, caption-cfg.caption_around.after, skip-pagebreak: true)
    if before == none and after == none {
      content
    } else if before == none {
      content + after
    } else if after == none {
      before + content
    } else {
      before + content + after
    }
  }

  let caption-for(config, caption-cfg, data, counters, number-counter, it) = {
    let body = if data == none {
      caption-plain(config, caption-cfg, it)
    } else {
      caption-body(config, caption-cfg, it, data, counters, number-counter)
    }
    // block(width: 100%) обязателен: align по естественной ширине подписи
    // не сдвигает сам блок подписи.
    block(width: 100%, align(alignment(caption-cfg.caption_align), body))
  }

  // Число ячеек в таблице, включая вложенную шапку. Нужно для внешних
  // границ: Typst не сообщает число строк таблицы напрямую.
  let table-cell-count(children) = {
    let count = 0
    for child in children {
      if child.func() == table.cell {
        count += 1
      } else if child.func() == table.header {
        count += table-cell-count(child.children)
      }
    }
    count
  }

  let table-row-count(it) = {
    let columns = it.columns.len()
    if columns == 0 { 0 } else { calc.floor(table-cell-count(it.children) / columns) }
  }

  let table-header-row-count(it) = {
    let columns = it.columns.len()
    let cells = 0
    for child in it.children {
      if child.func() == table.header {
        cells += table-cell-count(child.children)
      }
    }
    if columns == 0 { 0 } else { calc.floor(cells / columns) }
  }

  // Сетка таблицы: внешние и внутренние линии включаются отдельно.
  // Обслуживает table.border_* и table.header_double_line.
  let table-stroke(config, it) = {
    let columns = it.columns.len()
    let original-header-rows = table-header-row-count(it)
    let line = config.table.stroke * 1mm
    let double = config.table.header_double_line and original-header-rows > 0
    // Двойная линия добавляет маркер и зазор, повтор без двойной линии — маркер.
    let extra-rows = if double {
      2
    } else if not config.table.repeat_header and original-header-rows > 0 {
      1
    } else {
      0
    }
    let rows = table-row-count(it) + extra-rows
    let header-rows = original-header-rows + extra-rows
    (x, y) => (
      top: if y == 0 {
        if config.table.border_top { line } else { none }
      } else if header-rows > 0 and y <= header-rows {
        // Линию под шапкой рисует hline Pandoc или двойная линия.
        none
      } else if config.table.border_inside_horizontal {
        line
      } else {
        none
      },
      bottom: if y == rows - 1 {
        if config.table.border_bottom { line } else { none }
      } else if double and y == header-rows - 1 {
        none
      } else {
        none
      },
      left: if x == 0 {
        if config.table.border_left { line } else { none }
      } else if config.table.border_inside_vertical {
        line
      } else {
        none
      },
      right: if x == columns - 1 {
        if config.table.border_right { line } else { none }
      } else {
        none
      },
    )
  }

  // Метка-охранник, чтобы show table не пересобирал собственную шапку.
  let table-double-marker = "FD_TABLE_DOUBLE_HEADER"
  let table-has-marker(children) = {
    for child in children {
      if child.func() == table.cell {
        let body = child.body
        if body.func() == metadata and body.value == table-double-marker {
          return true
        }
      }
    }
    false
  }

  let table-header-rebuilt(config, header, columns, double) = {
    if double {
      table.header(
        repeat: config.table.repeat_header,
        ..header.children,
        table.hline(stroke: config.table.header_double_stroke * 1mm),
        table.cell(
          colspan: columns,
          inset: (top: 0pt, bottom: 0pt),
          stroke: none,
          metadata(table-double-marker),
        ),
        table.cell(
          colspan: columns,
          inset: (top: 0pt, bottom: 0pt),
          stroke: none,
          v(config.table.header_double_gap * 1mm),
        ),
        table.hline(stroke: config.table.header_double_stroke * 1mm),
      )
    } else {
      table.header(
        repeat: config.table.repeat_header,
        ..header.children,
        table.cell(
          colspan: columns,
          inset: (top: 0pt, bottom: 0pt),
          stroke: none,
          metadata(table-double-marker),
        ),
      )
    }
  }

  // Номер таблицы для метки продолжения: {h1}.{n}, {h1}.{h2}.{n} или {n}.
  let table-number-preview(data, counters, number-counter) = {
    let n = number-counter.get().first() + 1
    let parts = ()
    if data != none {
      for level in data.levels {
        parts.push(caption-chapter-value(level, counters))
      }
    }
    parts.push(str(n))
    parts.join(".")
  }

  // Номер формулы по шаблону: {n} и {h1}…{h6}.
  let formula-number-string(data, counters, n) = {
    let chapter-values = (:)
    if data != none {
      for level in data.levels {
        chapter-values.insert("h" + str(level), caption-chapter-value(level, counters))
      }
    }
    let out = none
    if data == none {
      out = str(n)
    } else {
      for (kind, value) in data.segments {
        if kind == "literal" {
          out = if out == none { value } else { out + value }
        } else if kind == "n" {
          out = if out == none { str(n) } else { out + str(n) }
        } else if kind == "content" {
          // В шаблоне номера {content} не используется.
        } else {
          let chapter = chapter-values.at(value)
          out = if out == none { chapter } else { out + chapter }
        }
      }
    }
    if out == none { str(n) } else { out }
  }

  // Подпись формулы: {n} — готовый номер, {content} — текст после двоеточия.
  let formula-caption-content(config, number, content, data, counters) = {
    if data == none {
      text-override-body(content, config.equation.caption_text_override)
    } else {
      let chapter-values = (:)
      for level in data.levels {
        chapter-values.insert("h" + str(level), caption-chapter-value(level, counters))
      }
      let out = none
      for (kind, value) in data.segments {
        let piece = if kind == "literal" {
          value
        } else if kind == "n" {
          number
        } else if kind == "content" {
          content
        } else {
          chapter-values.at(value)
        }
        out = if out == none { piece } else { out + piece }
      }
      if not data.has-content {
        out = if out == none { content } else { out + config.equation.caption_separator + content }
      }
      text-override-body(out, config.equation.caption_text_override)
    }
  }

  // Формула с номером справа; без номера возвращается только тело.
  let formula-numbered(config, body, number) = {
    let formula-align = if config.equation.align == "auto" {
      center
    } else {
      alignment(config.equation.align)
    }
    if number == "" {
      block(width: 100%, align(formula-align, body))
    } else {
      grid(
        columns: (1fr, auto),
        column-gutter: 1em,
        align(formula-align, body),
        align(right, text(number)),
      )
    }
  }

  let with-caption(config, body) = {
    let figure-data = if config.figure.caption_template == none {
      none
    } else {
      caption-data(config.figure.caption_template)
    }
    let table-data = if config.table.caption_template == none {
      none
    } else {
      caption-data(config.table.caption_template)
    }
    let figure-counters = range(1, 7).map(level => counter("figure-h" + str(level)))
    let table-counters = range(1, 7).map(level => counter("table-h" + str(level)))
    let formula-counters = range(1, 7).map(level => counter("formula-h" + str(level)))
    let figure-n = counter("figure-n")
    let table-n = counter("table-n")
    let formula-n = counter("formula-n")
    let formula-data = if config.equation.numbering_enabled {
      caption-data(config.equation.numbering_template)
    } else {
      none
    }
    let formula-caption-data = if config.equation.caption_template == none {
      none
    } else {
      caption-data(config.equation.caption_template)
    }

    // Отдельные счётчики и шаблоны; сброс — на заголовках уровня 1 и в приложении.
    // Таблица и её подпись стоят по левой границе (СТУ 7.7.3).
    show figure.where(kind: table): set align(left)
    show figure.where(kind: table): set figure.caption(
      position: if config.table.caption_position == "above" { top } else { bottom },
    )
    show figure.where(kind: image): set figure.caption(
      position: if config.figure.caption_position == "above" { top } else { bottom },
    )
    // Нумерация нужна для ссылок @tbl; сама подпись выводится своей строкой.
    show figure.where(kind: table): set figure(
      numbering: "1",
    )
    show figure.where(kind: image): set figure(
      numbering: if figure-data == none { "1" } else { none },
    )

    show figure.caption.where(kind: table): it => caption-for(
      config, config.table, table-data, table-counters, table-n, it,
    )
    show figure.caption.where(kind: image): it => if figure-data == none {
      block(
        width: 100%,
        align(
          alignment(config.figure.caption_align),
          caption-native(config, config.figure, it),
        ),
      )
    } else {
      caption-for(
        config, config.figure, figure-data, figure-counters, figure-n, it,
      )
    }

    // Разрывы страниц из caption_around выносятся за пределы figure:
    // внутри контейнера подписи Typst их запрещает.
    show figure.where(kind: table): it => {
      around-pagebreaks(config.table.caption_around.before)
      if config.table.continuation_label {
        context {
          let number = table-number-preview(table-data, table-counters, table-n)
          [#metadata(number) <fd-table-start>]
          // Без своего шаблона подписи table-n не шагает в caption-plain.
          if table-data == none { table-n.step() }
          it
          [#metadata(none) <fd-table-end>]
        }
      } else {
        it
      }
      around-pagebreaks(config.table.caption_around.after)
    }
    show figure.where(kind: image): it => {
      around-pagebreaks(config.figure.caption_around.before)
      it
      around-pagebreaks(config.figure.caption_around.after)
    }

    // Формула с подписью приходит из Pandoc как terms.item с math.equation
    // в term. Обычные definition lists возвращаются без изменений.
    show terms.item: it => {
      if it.term.func() == math.equation {
        {
          around-pagebreaks(config.equation.caption_around.before)
          context {
            let number = if config.equation.numbering_enabled {
              let n = formula-n.get().first() + 1
              let value = formula-number-string(formula-data, formula-counters, n)
              formula-n.step()
              value
            } else {
              ""
            }
            let content = if it.description.func() == block {
              it.description.body
            } else {
              it.description
            }
            let caption = formula-caption-content(
              config,
              number,
              content,
              formula-caption-data,
              formula-counters,
            )
            // Терм из Pandoc — блочная формула; рендерим её как встроенную,
            // чтобы show math.equation не добавил второй номер.
            let term-equation = math.equation(it.term.body, block: false)
            let formula-body = if config.equation.body_indent != 0 {
              pad(
                left: config.equation.body_indent * 1mm,
                text-override-body(term-equation, config.equation.text_override),
              )
            } else {
              text-override-body(term-equation, config.equation.text_override)
            }
            let formula = formula-numbered(config, formula-body, number)
            let caption-block = block(
              width: 100%,
              align(alignment(config.equation.caption_align), caption),
            )
            let before = around-items(
              config,
              config.equation.caption_around.before,
              skip-pagebreak: true,
            )
            let after = around-items(
              config,
              config.equation.caption_around.after,
              skip-pagebreak: true,
            )
            let caption-stack = if before == none and after == none {
              caption-block
            } else if before == none {
              caption-block + after
            } else if after == none {
              before + caption-block
            } else {
              before + caption-block + after
            }
            let content-body = if config.equation.caption_position == "above" {
              caption-stack + formula
            } else {
              formula + caption-stack
            }
            block(
              above: spacing-length(config, config.equation.spacing_before),
              below: spacing-length(config, config.equation.spacing_after),
              content-body,
            )
          }
          around-pagebreaks(config.equation.caption_around.after)
        }
      } else {
        it
      }
    }

    show math.equation.where(block: true): it => {
      if config.equation.numbering_enabled {
        context {
          let n = formula-n.get().first() + 1
          let number = formula-number-string(formula-data, formula-counters, n)
          formula-n.step()
          let body = if config.equation.body_indent != 0 {
            pad(
              left: config.equation.body_indent * 1mm,
              text-override-body(it, config.equation.text_override),
            )
          } else {
            text-override-body(it, config.equation.text_override)
          }
          formula-numbered(config, body, number)
        }
      } else {
        let body = if config.equation.body_indent != 0 {
          pad(left: config.equation.body_indent * 1mm, it)
        } else {
          it
        }
        formula-numbered(
          config,
          text-override-body(body, config.equation.text_override),
          "",
        )
      }
    }

    // Шесть уровней заголовков: каждый шаблон ведёт свои счётчики.
    show heading.where(level: 1): it => caption-heading(
      caption-heading(
        caption-heading(it, 1, figure-data, figure-counters, figure-n),
        1, table-data, table-counters, table-n,
      ),
      1, formula-data, formula-counters, formula-n,
    )
    show heading.where(level: 2): it => caption-heading(
      caption-heading(
        caption-heading(it, 2, figure-data, figure-counters, figure-n),
        2, table-data, table-counters, table-n,
      ),
      2, formula-data, formula-counters, formula-n,
    )
    show heading.where(level: 3): it => caption-heading(
      caption-heading(
        caption-heading(it, 3, figure-data, figure-counters, figure-n),
        3, table-data, table-counters, table-n,
      ),
      3, formula-data, formula-counters, formula-n,
    )
    show heading.where(level: 4): it => caption-heading(
      caption-heading(
        caption-heading(it, 4, figure-data, figure-counters, figure-n),
        4, table-data, table-counters, table-n,
      ),
      4, formula-data, formula-counters, formula-n,
    )
    show heading.where(level: 5): it => caption-heading(
      caption-heading(
        caption-heading(it, 5, figure-data, figure-counters, figure-n),
        5, table-data, table-counters, table-n,
      ),
      5, formula-data, formula-counters, formula-n,
    )
    show heading.where(level: 6): it => caption-heading(
      caption-heading(
        caption-heading(it, 6, figure-data, figure-counters, figure-n),
        6, table-data, table-counters, table-n,
      ),
      6, formula-data, formula-counters, formula-n,
    )
    body
  }

  // Регистр записи оглавления. first_upper сохраняет strong/emph и меняет
  // только текстовые узлы, чтобы форматированные заголовки не ломались.
  let outline-first-upper(content, first) = {
    if content.func() == text {
      let clusters = content.text.clusters()
      if clusters.len() == 0 {
        (content, first)
      } else if first {
        (upper(clusters.at(0)) + lower(clusters.slice(1).join("")), false)
      } else {
        (lower(content.text), false)
      }
    } else if content.func() == strong {
      let inner = outline-first-upper(content.body, first)
      (strong(inner.at(0)), inner.at(1))
    } else if content.func() == emph {
      let inner = outline-first-upper(content.body, first)
      (emph(inner.at(0)), inner.at(1))
    } else {
      let fields = content.fields()
      if "children" in fields {
        let out = none
        let is-first = first
        for child in fields.children {
          let inner = outline-first-upper(child, is-first)
          out = if out == none { inner.at(0) } else { out + inner.at(0) }
          is-first = inner.at(1)
        }
        (if out == none { content } else { out }, is-first)
      } else if "body" in fields {
        (content, first)
      } else {
        (content, first)
      }
    }
  }

  let outline-case(content, mode) = {
    if mode == "upper" {
      upper(content)
    } else if mode == "lower" {
      lower(content)
    } else if mode == "first_upper" {
      outline-first-upper(content, true).at(0)
    } else {
      content
    }
  }

  // Метаданные структурного приложения: не зависят от текста шаблона и bold.
  let appendix-meta(content) = {
    if content.func() == metadata {
      let value = content.value
      if type(value) == dictionary and "fd-appendix-kind" in value {
        return value
      }
    } else {
      let fields = content.fields()
      if "children" in fields {
        for child in fields.children {
          let found = appendix-meta(child)
          if found != none { return found }
        }
      } else if "body" in fields {
        return appendix-meta(fields.body)
      }
    }
    none
  }

  // Номер страницы в формате page.numbering (римские, «1 / N» и т. д.).
  let outline-page(config, loc) = {
    let n = counter(page).at(loc).first()
    let total = counter(page).final().first()
    if config.page.numbering == "none" {
      str(n + config.page.numbering_start - 1)
    } else {
      let value = page-number(
        config.page.numbering,
        config.page.numbering_skip_first,
        config.page.numbering_start,
        n,
        total,
      )
      if value == none { "" } else { value }
    }
  }

  // Запись оглавления: регистр, отточие и группировка приложений.
  // Обслуживает outline.entry_case и outline.appendix_grouping.
  let outline-entry(config, it) = context {
    let default-entry = link(
      it.element.location(),
      it.indented(it.prefix(), it.inner()),
    )
    if it.element.func() != heading {
      return default-entry
    }

    let meta = appendix-meta(it.element.body)
    let is-appendix = meta != none
    let normal-entry = {
      // Своя запись нужна и при entry_case = none: стандартная запись Typst
      // не учитывает numbering_start/skip_first в номере страницы.
      let body = if config.outline.entry_case == "none" or is-appendix {
        it.body()
      } else {
        outline-case(it.body(), config.outline.entry_case)
      }
      let page = outline-page(config, it.element.location())
      link(
        it.element.location(),
        it.indented(
          it.prefix(),
          [#body #box(width: 1fr, repeat[.]) #page],
        ),
      )
    }

    if not config.outline.appendix_grouping {
      return normal-entry
    }

    let headings = query(heading.where(outlined: true))
    let current = it.element
    let current-index = none
    for (index, heading) in headings.enumerate() {
      if heading.location() == current.location() {
        current-index = index
        break
      }
    }
    if current-index == none {
      return normal-entry
    }

    let level-one = ()
    for (index, heading) in headings.enumerate() {
      if heading.level == 1 { level-one.push(index) }
    }
    let runs = ()
    let current-run = ()
    for index in level-one {
      let heading-meta = appendix-meta(headings.at(index).body)
      if heading-meta != none and heading-meta.fd-appendix-kind == "heading" {
        current-run.push(index)
      } else {
        if current-run.len() > 0 {
          runs.push(current-run)
          current-run = ()
        }
      }
    }
    if current-run.len() > 0 { runs.push(current-run) }

    let run = none
    if meta != none and meta.fd-appendix-kind == "heading" {
      for candidate in runs {
        if candidate.contains(current-index) {
          run = candidate
          break
        }
      }
    } else if meta != none and meta.fd-appendix-kind == "sub" {
      for candidate in runs {
        if candidate.any(index => {
          let parent-meta = appendix-meta(headings.at(index).body)
          (
            parent-meta != none
              and parent-meta.fd-appendix-letter == meta.fd-appendix-letter
          )
        }) {
          run = candidate
          break
        }
      }
    }

    if run != none and run.len() >= config.outline.appendix_min_group {
      if meta != none and meta.fd-appendix-kind == "sub" {
        return none
      }
      let first-index = run.first()
      if current-index != first-index {
        return none
      }
      let first = headings.at(first-index)
      let last = headings.at(run.last())
      let first-meta = appendix-meta(first.body)
      let last-meta = appendix-meta(last.body)
      let text = config.outline.appendix_group_template
        .replace("{first}", str(first-meta.fd-appendix-letter))
        .replace("{last}", str(last-meta.fd-appendix-letter))
      let first-page = outline-page(config, first.location())
      let last-page = outline-page(config, last.location())
      return link(
        first.location(),
        it.indented(
          none,
          [#text #box(width: 1fr, repeat[.]) #first-page–#last-page],
        ),
      )
    }

    normal-entry
  }

  let with-text-overrides(config, body) = {
    show par: it => text-override-body(it, config.par.text_override)
    show list: it => text-override-body(it, config.bullet_list.text_override)
    show enum: it => text-override-body(it, config.numbered_list.text_override)
    show table.cell: it => {
      if (
        config.table.italic_letters
          and it.body.func() == text
          and it.body.text.clusters().len() == 1
          and regex("[A-Za-zΑ-Ωα-ω]") in it.body.text
      ) {
        // Только ячейка ровно из одной латинской/греческой буквы (СТУ 7.7.5).
        let fields = it.fields()
        let body = fields.remove("body")
        text-override-body(
          table.cell(emph(body), ..fields),
          config.table.text_override,
        )
      } else {
        text-override-body(it, config.table.text_override)
      }
    }
    show quote: it => text-override-body(it, config.quote.text_override)
    show raw.where(block: true): it => text-override-body(it, config.raw.text_override)
    show raw.where(block: false): it => text-override-body(it, config.raw.text_override)
    show figure: it => text-override-body(it, config.figure.text_override)
    show footnote.entry: it => text-override-body(it, config.footnote.text_override)
    show terms: it => text-override-body(it, config.terms.text_override)
    show outline: it => {
      if config.outline.omit_when_pages_lte > 0 {
        context {
          if counter(page).final().first() <= config.outline.omit_when_pages_lte {
            none
          } else {
            text-override-body(it, config.outline.text_override)
          }
        }
      } else {
        text-override-body(it, config.outline.text_override)
      }
    }
    show outline.entry: it => outline-entry(config, it)
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
    let page-numbering = if config.page.numbering == "none" {
      none
    } else if config.page.numbering_skip_first or config.page.numbering_start != 1 {
      page-number.with(
        config.page.numbering,
        config.page.numbering_skip_first,
        config.page.numbering_start,
      )
    } else {
      config.page.numbering
    }
    let page-args = (
      paper: config.page.paper,
      flipped: config.page.flipped,
      margin: page-margins(config.page),
      columns: config.page.columns,
      numbering: page-numbering,
      number-align: alignment(config.page.number_align),
    )
    if config.table.continuation_label {
      // Метки продолжения таблицы живут в колонтитуле: диапазон страниц
      // определяется метками до/после figure таблицы (S2).
      page-args.insert(
        "header",
        context {
          let here-page = here().page()
          let starts = query(<fd-table-start>)
          let ends = query(<fd-table-end>)
          let out = none
          for (index, start) in starts.enumerate() {
            if index < ends.len() {
              let end = ends.at(index)
              let start-page = start.location().page()
              let end-page = end.location().page()
              if here-page > start-page and here-page <= end-page {
                let number = str(start.value)
                let template = if here-page == end-page {
                  config.table.final_template
                } else {
                  config.table.continuation_template
                }
                let label = text-override-body(
                  [#template.replace("{n}", number)],
                  config.table.text_override,
                )
                let line = align(right, label)
                out = if out == none { line } else { out + linebreak() + line }
              }
            }
          }
          out
        },
      )
    }
    set page(..page-args)

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

    // Нумерованный список: собственный рендер, чтобы точно управлять
    // положением маркера и продолжения строки.
    show enum: it => list-render(config, it)

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

    // Сетка по сторонам, повтор шапки и двойная линия под шапкой.
    // Функция stroke в поле — признак уже пересобранной таблицы.
    show table: it => {
      if type(it.stroke) == function {
        it
      } else {
        let header = it.children.find(child => child.func() == table.header)
        if header != none and table-has-marker(header.children) {
          it
        } else {
          let double = config.table.header_double_line
          let rebuild = header != none and (double or not config.table.repeat_header)
          let fields = it.fields()
          let children = fields.remove("children")
          if double or not config.table.border_inside_horizontal {
            children = children.filter(child => child.func() != table.hline)
          }
          if rebuild {
            let columns = it.columns.len()
            children = children.map(child => if child.func() == table.header {
              table-header-rebuilt(config, child, columns, double)
            } else {
              child
            })
          }
          fields.insert("stroke", table-stroke(config, it))
          table(..fields, ..children)
        }
      }
    }

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
    // Таблица внутри figure иначе не разрывается между страницами.
    show figure.where(kind: table): set block(breakable: true)

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
    if config.outline.indent_mode == "step" {
      outline-args.insert(
        "indent",
        (level) => level * config.outline.indent_mm * 1mm,
      )
    } else {
      outline-args.insert(
        "indent",
        (level) => {
          let levels = config.outline.indent_per_level
          if levels.len() == 0 {
            0mm
          } else {
            let index = calc.min(level, levels.len() - 1)
            levels.at(index) * 1mm
          }
        },
      )
    }
    // set вне блока if: правило видимо всему телу apply.
    set outline(..outline-args)

    // Заголовки и вокруг-вставки обрабатываются одним проходом по телу,
    // чтобы у заголовка был ровно один элемент (без дублей в оглавлении).
    let transformed = with-around-and-headings(config, body)
    let content = with-text-overrides(config, with-caption(config, transformed))
    content
  }

  (apply: apply)
}
