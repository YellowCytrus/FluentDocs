// S3: двойная линия под шапкой таблицы.
// Шапка содержит: текст, hline, тонкую распорку, второй hline.
// Вся конструкция лежит в table.header, поэтому повторяется на продолжениях.
#set page(margin: (top: 2cm, bottom: 2cm, left: 2cm, right: 2cm))

#table(
  columns: 2,
  stroke: 0.3pt,
  table.header(
    [Показатель], [Значение],
    table.hline(stroke: 0.6pt),
    table.cell(colspan: 2, inset: (top: 0pt, bottom: 0pt), stroke: none, [#v(0.5mm)]),
    table.hline(stroke: 0.6pt),
  ),
  ..range(1, 81).map(i => ([Строка #i], [#i])).flatten(),
)
