// S13. Оглавление без дублей: один авторитетный заголовок.
//
// Заголовки пересобираются проходом по верхнеуровневым элементам тела.
// `outlined: false` убирает запись из #outline(), `numbering: none` даёт
// запись/тело без номера, а счётчик восстанавливается, чтобы следующий
// раздел получил 1, а не 2.
//
// Компиляция: typst compile S13-outline-single-entry.typ /tmp/S13.pdf

#set heading(numbering: "1.1")

#let rules = (
  "Введение": (mode: "none", outlined: false),
  "Скрытый": (mode: "continue", outlined: false),
)

#let units = [
  = Введение

  Текст введения.

  = Раздел

  Текст раздела.

  == Подраздел

  Текст подраздела.

  = Скрытый

  Текст скрытого раздела.

  = Второй

  Текст второго раздела.
]

#let process(body) = {
  for it in body.children {
    if it.func() == heading {
      let rule = rules.at(it.body.text, default: (mode: "continue", outlined: true))
      if rule.mode == "none" {
        // Ненумерованный заголовок не должен сдвигать общий счётчик.
        context {
          let before = counter(heading).get()
          heading(
            level: it.depth,
            numbering: none,
            outlined: rule.outlined,
            it.body,
          )
          counter(heading).update(before)
        }
      } else {
        heading(
          level: it.depth,
          numbering: "1.1",
          outlined: rule.outlined,
          it.body,
        )
      }
    } else {
      it
    }
  }
}

#outline()
#process(units)
