// S1: схлопывание «пустых строк» через v(weak: true).
#set page(paper: "a4", margin: 2cm)
#set par(leading: 8mm)
#show heading: set block(above: 0pt, below: 0pt)

#let gap(weak: bool, n: int) = v(n * 6mm, weak: weak)

// Сверху страницы слабый отступ не должен давать зазор.
#gap(weak: true, n: 4)
#heading(level: 1)[TOP-MARK]

#table(columns: 2, [TABLE-A], [1])
#gap(weak: true, n: 1)
#gap(weak: true, n: 2)
#heading(level: 1)[WEAK]

#table(columns: 2, [TABLE-B], [1])
#gap(weak: false, n: 1)
#gap(weak: false, n: 2)
#heading(level: 1)[HARD]
