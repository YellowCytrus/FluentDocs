# Шрифты проекта

Сервер (`typst compile --font-path assets/fonts`) и браузер (`typst.ts`)
загружают одни и те же файлы. Это убирает CDN из паритета и делает превью
детерминированным.

- `pt-astra-serif_*.ttf` — PT Astra Serif 1.002, OFL-1.1, источник
  <https://archive.org/download/ttf-pt-public-pack/ttf-pt-public-pack-2024.09.02.tar.gz>.
- `LibertinusSerif-*.otf`, `NewCM*.otf`, `DejaVuSansMono*.ttf` — набор
  typst-assets v0.13.1 (те же файлы, что typst.ts раньше скачивал с CDN),
  лицензии OFL-1.1. Источник:
  <https://github.com/typst/typst-assets/tree/v0.13.1/files/fonts>.
