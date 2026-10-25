// S6: авто-пропуск оглавления, если страниц <= N.
// Порог передаётся через --input threshold=N (по умолчанию 3).
#let threshold = int(sys.inputs.at("threshold", default: "3"))

#set page(paper: "a4", margin: 2cm)
#set heading(numbering: "1.1")

#context {
  let total = counter(page).final().first()
  if total > threshold {
    outline(title: [Содержание], indent: auto)
    pagebreak()
  }
}

#for i in range(1, 3) [
  = Раздел #i
  #lorem(400)
  #lorem(400)
]
