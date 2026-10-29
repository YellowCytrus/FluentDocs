// S12. Политики столкновения вставок на 600 элементах верхнего уровня.
//
// Проверяет: проход по верхнеуровневым элементам тела, определение вида
// предыдущего/текущего элемента, четыре политики 5.1 и совпадение CLI/typst.ts.
// Компиляция: typst compile S12-collisions.typ /tmp/S12.pdf

#set page(width: 150mm, height: 220mm, margin: 15mm)
#set text(font: "Libertinus Serif", size: 10pt)
#set par(leading: 0.65em)

#let total = 600
#let gap = 1.2em

// Вид элемента: заголовок, таблица, цитата или абзац.
#let kind(i) = {
  if calc.rem(i, 11) == 0 { "heading_1" }
  else if calc.rem(i, 13) == 0 { "table" }
  else if calc.rem(i, 17) == 0 { "quote" }
  else { "par" }
}

// Вставки: перед таблицей и после заголовка/абзаца.
#let has-before(cur) = cur == "table"
#let has-after(prev) = prev == "heading_1" or prev == "par"

// Правило хранится у текущего элемента: первое подходящее по виду предыдущего.
#let policy-for(prev, cur) = {
  if prev == "heading_1" and cur == "table" { "keep_previous" }
  else if prev == "par" and cur == "table" { "drop_both" }
  else if prev == "quote" and cur == "table" { "keep_current" }
  else { "keep_both" }
}

#let unit(i) = {
  let cur = kind(i)
  if cur == "heading_1" {
    heading(level: 1, [Раздел #i])
  } else if cur == "table" {
    table(
      columns: (1fr, 1fr),
      [Ключ #i], [Значение #i],
      [Параметр], [Данные],
    )
  } else if cur == "quote" {
    quote(block: true)[Цитата #i]
  } else {
    par[Абзац #i. Текст для проверки прохода по элементам тела.]
  }
}

#let body = {
  for i in range(total) {
    let prev = if i == 0 { none } else { kind(i - 1) }
    let cur = kind(i)
    let policy = if prev == none { "keep_both" } else { policy-for(prev, cur) }
    let before = has-before(cur)
    let after = prev != none and has-after(prev)
    let show-before = before and (policy == "keep_current" or policy == "keep_both")
    let show-after = after and (policy == "keep_previous" or policy == "keep_both")
    if show-after { v(gap) }
    if show-before { v(gap) }
    unit(i)
  }
}

#body
