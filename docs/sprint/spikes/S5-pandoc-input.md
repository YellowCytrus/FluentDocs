# Заголовок без номера {-}

Текст с обычной ссылкой [@fig:x] и на таблицу [@tbl:y].

![Подпись рисунка](sample.png){#fig:x width=50%}

| A | B |
|---|---|
| 1 | 2 |

: Подпись таблицы {#tbl:y}

$$a^2 + b^2 = c^2$$ {#eq:z}

::: {#note .warning data-role="box"}
Содержимое fenced-div с атрибутами.
:::

```{=typst}
#block(fill: luma(230), inset: 4pt)[Сырой Typst из raw_attribute]
```

Обычный код:

```python
print("hello")
```
