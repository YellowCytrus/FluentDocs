// S8: скорость компиляции документа 120+ страниц с рантаймом вида fd.
// Меряется CLI-прокси (typst compile), не браузерный typst.ts.
#set page(paper: "a4", margin: (top: 2cm, bottom: 2cm, left: 3cm, right: 1.5cm))
#set text(font: "Libertinus Serif", size: 14pt, lang: "ru")

// Аналог fd.line-pitch: множитель -> leading.
#let line-pitch(multiplier) = multiplier * 0.65em

#set par(leading: line-pitch(1.5), justify: true, first-line-indent: (amount: 1.25cm, all: true))
#set heading(numbering: "1.1")
#set table(stroke: 0.5pt, inset: 4pt)

#for i in range(1, 121) {
  pagebreak(weak: true)
  heading(level: 1)[Раздел #i]
  par(lorem(90))
  par(lorem(90))
  if calc.rem(i, 10) == 0 {
    table(
      columns: 3,
      [№], [Показатель], [Значение],
      ..range(1, 8).map(j => ([#j], [Строка #j], [#(j * i)])).flatten(),
    )
  }
  if calc.rem(i, 15) == 0 {
    footnote([Сноска на странице #i.])
  }
}
