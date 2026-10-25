// S10: снятие номера у заголовка по тексту (структурная сущность).
// Показ-правило заменяет заголовок на такой же с numbering: none
// и компенсирует уже выполненный шаг счётчика.
// Ограничение: у ненумерованного заголовка не должно быть подразделов
// (иначе они получат номер 0.1) — для «Введения»/«Заключения» это норма.
#set page(paper: "a4", margin: 2cm)
#set heading(numbering: "1.")

#let unnumbered-titles = ("Введение", "Заключение")

#show heading.where(level: 1): it => {
  if it.numbering != none and unnumbered-titles.contains(it.body.text.trim()) {
    let current = counter(heading).get()
    counter(heading).update(current.slice(0, -1) + (current.last() - 1,))
    heading(level: 1, numbering: none, it.body)
  } else {
    it
  }
}

= Введение

Текст введения.

= Первый раздел

== Подраздел первого раздела

Текст подраздела.

= Второй раздел

Текст второго раздела.

= Заключение

Текст заключения.
