# Версии инструментов

Версии зафиксированы решением 6а в `AGENTS.md`. Обновлять только вместе и только
по команде владельца.

```versions
pandoc_server=3.9
pandoc_wasm=3.9
typst_server=0.14.2
typst_ts=0.14.2
typst_local=0.14.2
```

| Инструмент | Версия | Где задана / как проверена |
|---|---|---|
| Pandoc на сервере | 3.9 | `Dockerfile`: `ARG PANDOC_VERSION=3.9`; `tests/test_versions.py` |
| Pandoc в `pandoc-wasm` | 3.9 | `pandoc-wasm` 1.0.1, `node_modules/pandoc-wasm/pandoc-version.txt` |
| Typst CLI на сервере | 0.14.2 | `Dockerfile`: `ARG TYPST_VERSION=0.14.2` |
| Компилятор Typst в `typst.ts` | 0.14.2 | `@myriaddreamin/typst.ts` 0.7.0-rc2; определяется `frontend/scripts/typst-ts-version.mjs` через `#sys.version` |
| Typst CLI в локальной среде | 0.14.2 | `typst --version`; используется для прототипов и golden-проверок |

На сервере версии Typst CLI и `typst.ts` совпадают (0.14.2), блокера B-06 нет.
