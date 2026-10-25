// S11: нумерация приложений: буква вместо номера раздела
// для подзаголовков, рисунков, таблиц и формул.
#set page(paper: "a4", margin: 2cm)

#let in-appendix = state("in-appendix", false)
#let appendix-letter = counter("appendix-letter")
#let letters = "АБВГДЕЖИКЛМНПРСТУФХЦШЩЭЮЯ".clusters()

#let letter() = letters.at(appendix-letter.get().first() - 1)

#let numbered(..nums) = {
  let n = nums.pos()
  if in-appendix.get() {
    letter() + "." + numbering("1", ..n)
  } else {
    numbering("1", ..n)
  }
}

#set heading(numbering: (..nums) => {
  let n = nums.pos()
  if in-appendix.get() {
    letter() + "." + numbering("1.1", ..n.slice(1))
  } else {
    numbering("1.1", ..n)
  }
})

#set figure(
  supplement: [Рисунок],
  numbering: (..nums) => numbered(..nums),
)
#show figure.where(kind: table): set figure(supplement: [Таблица])
#set math.equation(numbering: (..nums) => "(" + numbered(..nums) + ")")

// Начало приложения: верхний заголовок «ПРИЛОЖЕНИЕ X» включает режим.
#show heading.where(level: 1): it => {
  if it.numbering != none and it.body.text.trim().starts-with("ПРИЛОЖЕНИЕ") {
    if not in-appendix.get() {
      in-appendix.update(true)
      appendix-letter.step()
      counter(figure).update(0)
      counter(math.equation).update(0)
    }
    heading(level: 1, numbering: none, it.body)
  } else {
    it
  }
}

= ПРИЛОЖЕНИЕ

== Состав изделия

#figure(
  rect(width: 4cm, height: 1cm),
  caption: [Схема состава],
)

#figure(
  table(columns: 2, [A], [B], [1], [2]),
  caption: [Параметры],
  kind: table,
)

$ E = m c^2 $

== Второй подраздел

Текст.
