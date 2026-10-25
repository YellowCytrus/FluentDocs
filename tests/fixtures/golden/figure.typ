#set page("a4", margin: (top: 25.0mm, bottom: 25.0mm, left: 25.0mm, right: 25.0mm))
#set text(size: 12.0pt, font: "Merriweather")
#set par(leading: 5.08mm)
#set par(spacing: 4.2333333333mm)
#set heading(numbering: "1.1.1")
#set list(tight: true, indent: 0.0mm, body-indent: 2.1166666667mm, spacing: auto, marker: ("- ", "‣", "–"))
#set enum(tight: true, indent: 0.0mm, body-indent: 2.1166666667mm, spacing: auto)
#set table(stroke: 0.1763888889mm, inset: 1.7638888889mm)
#set image(width: 4.2333333333mm, height: auto)
#set figure(gap: 2.7516666667mm)
#set footnote(numbering: "1")
#set footnote.entry(clearance: 4.2333333333mm, gap: 2.1166666667mm, indent: 4.2333333333mm)
#set quote(block: true)
#show quote: set pad(x: 6.35mm)
#set terms(tight: true, hanging-indent: 8.4666666667mm)
#show heading.where(level: 1): it => block[ #it ]
#show heading.where(level: 2): it => block[ #it ]
#show heading.where(level: 3): it => block[ #it ]
#show heading.where(level: 4): it => block[ #it ]
#show heading.where(level: 5): it => block[ #it ]
#show heading.where(level: 6): it => block[ #it ]

= Рисунок
<рисунок>
Ссылка на рисунок: @fig:sample.

#figure(image("sample.png", width: 60.0%),
  caption: [
    Рисунок 1 --- Эталонное изображение
  ]
)
<fig:sample>

Текст после рисунка.
