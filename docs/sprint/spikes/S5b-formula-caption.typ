// S5b: подпись формулы строкой ": Подпись" после $$...$$.
// Pandoc 3.9 превращает такую пару в определение-список:
//   / $ E = m c^2 $: #block[Подпись формулы]
// Перехват: terms.item, у которого term — math.equation.
#set page(paper: "a4", margin: 2cm)
#set heading(numbering: "1.1")

#let formula-n = counter("formula")

// Шаблон подписи формулы: {n} — номер, {content} — текст после двоеточия.
#let formula-caption(n, content) = [Формула #n — #content]

#show terms.item: it => {
  if it.term.func() == math.equation {
    formula-n.step()
    align(center, block(above: 1em, below: 1em)[
      #it.term
      #linebreak()
      #context formula-caption(
        formula-n.display("1"),
        if it.description.func() == block { it.description.body } else { it.description },
      )
    ])
  } else {
    it
  }
}

= Формулы
/ $ E = m c^2 $: #block[
Подпись формулы
]

/ $ a^2 + b^2 = c^2 $: #block[
Вторая подпись
]

Обычный список определений:

/ Термин: #block[
Определение термина
]
