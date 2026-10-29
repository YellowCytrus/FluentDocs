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

  // Формат нумерации по уровню: {n}, {letter} или шаблон Typst.
  let numbered-list-numbering(config) = (..nums) => {
    let values = nums.pos()
    let level = values.len()
    let formats = config.numbered_list.level_formats
    let rendered = if formats.len() == 0 {
      numbering(config.numbered_list.numbering, ..values)
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
    let result = if prefix == "" { rendered } else { [#prefix #rendered] }
    if config.numbered_list.wrap_mode == "left_margin" {
      [#result\u{00A0}]
    } else {
      result
    }
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
  let around-item(config, item) = {
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
    } else if item.type == "pagebreak" {
      pagebreak(weak: item.weak)
    }
  }

  // Все вставки списка; пустой список ничего не добавляет.
  let around-items(config, items) = {
    for item in items {
      around-item(config, item)
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

  // Сопоставление текста правила: equals / contains / regex.
  let matches-text(match, text) = {
    let hay = if match.case_insensitive { lower(text) } else { text }
    let needle = if match.case_insensitive { lower(match.value) } else { match.value }
    if match.mode == "equals" {
      hay == needle
    } else if match.mode == "contains" {
      hay.contains(needle)
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
      let entity = find-entity(config, "heading", it.body.text.trim(), it.depth)
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
    let heading-text = it.body.text.trim()
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
        let text = heading.body.text.trim()
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
          }
          before = add-content(
            before,
            [
              #counter("figure-n").update(0)
              #counter("table-n").update(0)
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
    let before = around-items(config, caption-cfg.caption_around.before)
    let after = around-items(config, caption-cfg.caption_around.after)
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
    let before = around-items(config, caption-cfg.caption_around.before)
    let after = around-items(config, caption-cfg.caption_around.after)
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
    align(alignment(caption-cfg.caption_align), body)
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
    let figure-n = counter("figure-n")
    let table-n = counter("table-n")

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
      it
    } else {
      caption-for(
        config, config.figure, figure-data, figure-counters, figure-n, it,
      )
    }

    // Шесть уровней заголовков: каждый шаблон ведёт свои счётчики.
    show heading.where(level: 1): it => caption-heading(
      caption-heading(it, 1, figure-data, figure-counters, figure-n),
      1, table-data, table-counters, table-n,
    )
    show heading.where(level: 2): it => caption-heading(
      caption-heading(it, 2, figure-data, figure-counters, figure-n),
      2, table-data, table-counters, table-n,
    )
    show heading.where(level: 3): it => caption-heading(
      caption-heading(it, 3, figure-data, figure-counters, figure-n),
      3, table-data, table-counters, table-n,
    )
    show heading.where(level: 4): it => caption-heading(
      caption-heading(it, 4, figure-data, figure-counters, figure-n),
      4, table-data, table-counters, table-n,
    )
    show heading.where(level: 5): it => caption-heading(
      caption-heading(it, 5, figure-data, figure-counters, figure-n),
      5, table-data, table-counters, table-n,
    )
    show heading.where(level: 6): it => caption-heading(
      caption-heading(it, 6, figure-data, figure-counters, figure-n),
      6, table-data, table-counters, table-n,
    )
    body
  }

  let with-text-overrides(config, body) = {
    show par: it => text-override-body(it, config.par.text_override)
    show list: it => text-override-body(it, config.bullet_list.text_override)
    show enum: it => text-override-body(it, config.numbered_list.text_override)
    show table.cell: it => text-override-body(it, config.table.text_override)
    show quote: it => text-override-body(it, config.quote.text_override)
    show raw.where(block: true): it => text-override-body(it, config.raw.text_override)
    show raw.where(block: false): it => text-override-body(it, config.raw.text_override)
    show figure: it => text-override-body(it, config.figure.text_override)
    show footnote.entry: it => text-override-body(it, config.footnote.text_override)
    show terms: it => text-override-body(it, config.terms.text_override)
    show outline: it => text-override-body(it, config.outline.text_override)
    show math.equation.where(block: true): it => {
      let equation = if config.equation.body_indent != 0 {
        pad(left: config.equation.body_indent * 1mm, it)
      } else {
        it
      }
      text-override-body(equation, config.equation.text_override)
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
      body-indent: if config.numbered_list.wrap_mode == "left_margin" {
        let shifted = config.numbered_list.body_indent - config.numbered_list.left_margin_offset
        if shifted > 0 { shifted * 1mm } else { 0mm }
      } else {
        config.numbered_list.body_indent * 1mm
      },
      spacing: list-spacing(config.numbered_list.spacing, config.numbered_list.tight_spacing, config.numbered_list.loose_spacing),
      numbering: numbered-list-numbering(config),
    )
    if config.numbered_list.start != none {
      enum-args.insert("start", config.numbered_list.start)
    }
    if config.numbered_list.full or config.numbered_list.level_formats.len() > 0 {
      enum-args.insert("full", true)
    }
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
