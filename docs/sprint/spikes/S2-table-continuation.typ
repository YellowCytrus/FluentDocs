// S2: метки «Продолжение/Окончание таблицы N» по страницам таблицы.
// Диапазон страниц таблицы определяется метками до и после таблицы.
#set page(
  paper: "a4",
  margin: (top: 3cm, bottom: 2cm, left: 2cm, right: 2cm),
  header: context {
    let start = query(<t-start>).first().location().page()
    let end = query(<t-end>).first().location().page()
    let here-page = here().page()
    if here-page > start and here-page <= end {
      align(right, text(size: 10pt, style: "italic")[
        #if here-page == end [Окончание таблицы 1] else [Продолжение таблицы 1]
      ])
    }
  },
)

#metadata(none) <t-start>
#table(
  columns: 3,
  table.header([№], [Показатель], [Значение]),
  ..range(1, 121).map(i => ([#i], [Строка #i], [#(i * 10)])).flatten(),
)
#metadata(none) <t-end>
