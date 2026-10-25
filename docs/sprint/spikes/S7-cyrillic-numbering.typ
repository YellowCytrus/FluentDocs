// S7: кириллическая нумерация ru_sfu (без Ё З Й О Ч Ь Ы Ъ).
#set page(paper: "a4", margin: 2cm)

#let ru-sfu-alphabet = "АБВГДЕЖИКЛМНПРСТУФХЦШЩЭЮЯ".clusters()

#let ru-sfu(n) = {
  let index = n - 1
  if index >= 0 and index < ru-sfu-alphabet.len() {
    ru-sfu-alphabet.at(index)
  } else {
    numbering("1", n)
  }
}

// Заголовки: А, А.1, А.1.1 (режим приложения).
#let appendix-heading(..nums) = {
  let n = nums.pos()
  let head = ru-sfu(n.at(0))
  if n.len() == 1 { head } else { head + "." + numbering("1.1", ..n.slice(1)) }
}

#set heading(numbering: appendix-heading)

// Списки: А), Б), В) на первом уровне.
#set enum(numbering: (..nums) => ru-sfu(nums.pos().first()) + ")")

= Первое приложение

== Подраздел приложения

+ Пункт списка
+ Второй пункт
+ Третий пункт

= Второе приложение

== Подраздел второго приложения
