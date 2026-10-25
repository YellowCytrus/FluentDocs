#heading(level: 1, numbering: none)[Заголовок без номера]
<заголовок-без-номера>
Текст с обычной ссылкой @fig:x и на таблицу @tbl:y.

#figure(image("sample.png", width: 50.0%),
  caption: [
    Подпись рисунка
  ]
)
<fig:x>

#figure(
  align(center)[#table(
    columns: 2,
    align: (auto,auto,),
    table.header([A], [B],),
    table.hline(),
    [1], [2],
  )]
  , caption: [Подпись таблицы]
  , kind: table
  )
<tbl:y>

$ a^2 + b^2 = c^2 $ {\#eq:z}

#block[
Содержимое fenced-div с атрибутами.

] <note>
#block(fill: luma(230), inset: 4pt)[Сырой Typst из raw_attribute]
Обычный код:

```python
print("hello")
```
