// S10: исходный прототип снятия номера у заголовка по тексту.
// Исторический пример: показ-правило и компенсация счётчика. В этом файле
// подраздел ненумерованного заголовка всё ещё может получить 0.1.
// В G3a ограничение снято иначе (проход по телу, см. app/typst/fd.typ и
// docs/sprint/SPIKES.md S10); файл оставлен как исходный прототип.
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
