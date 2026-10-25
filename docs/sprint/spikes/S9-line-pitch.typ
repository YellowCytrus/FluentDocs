// S9: калибровка множителя межстрочного интервала.
// natural-line-height-em измерен по базовым линиям Libertinus Serif (14pt):
// при leading=0.65em расстояние между базовыми линиями = 1.308em.
// fd.line-pitch(m) даёт leading, при котором baseline = m * natural.
#let natural-line-height-em = 1.308
#let default-leading-em = 0.65

#let line-pitch(multiplier) = (
  multiplier * natural-line-height-em - (natural-line-height-em - default-leading-em)
) * 1em

#let multiplier = float(sys.inputs.at("mult", default: "1.5"))

#set page(paper: "a4", margin: 3cm)
#set text(font: "Libertinus Serif", size: 14pt, lang: "ru")
#set par(leading: line-pitch(multiplier), justify: false)
#lorem(80)
