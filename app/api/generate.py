"""
POST /profiles/{profile_id}/generate-pdf — загрузка Markdown, возврат PDF.
POST /profiles/{profile_id}/export-typ  — загрузка Markdown, возврат полного .typ.
GET  /profiles/{profile_id}/preamble     — текст преамбулы Typst.
"""

import logging
import re
from pathlib import Path, PurePosixPath
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from fastapi.responses import PlainTextResponse, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_profile_repository, get_title_page_repository
from app.database import get_session
from app.models.pydantic.page_editor import TitlePageContent
from app.models.sqlalchemy.image_asset import ImageAsset
from app.models.sqlalchemy.profile import Profile
from app.registry import RegistryError
from app.repositories.profile_repository import ProfileRepository
from app.repositories.title_page_repository import TitlePageRepository
from app.api.upload import IMAGES_DIR
from app.utils.pandoc_converter import PandocError, markdown_to_typst
from app.utils.typst_compiler import TypstCompileError, compile_typst_to_pdf
from app.utils.typst_source import build_typst_preamble, build_typst_source
from app.utils.typst_title_exporter import generate_fragment

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/profiles", tags=["generate"])

_ALLOWED_CONTENT_TYPES = {"text/markdown", "text/plain", "application/octet-stream"}
_ALLOWED_EXTENSIONS = {".md", ".markdown", ".txt"}
_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


async def _read_and_validate_markdown(file: UploadFile) -> bytes:
    """Read upload, validate, return content or raise HTTPException."""
    ext = PurePosixPath(file.filename or "").suffix.lower()
    if ext not in _ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file extension")
    if file.content_type:
        base_type = file.content_type.split(";")[0].strip().lower()
        if base_type not in _ALLOWED_CONTENT_TYPES:
            raise HTTPException(status_code=400, detail="Unsupported content type")
    content = await file.read()
    if len(content) > _MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 10 MB)")
    if not content.strip():
        raise HTTPException(status_code=400, detail="Empty Markdown file")
    return content


def _content_disposition_attachment(filename: str) -> str:
    """Build Content-Disposition header value for attachment download."""
    safe_ascii = filename.encode("ascii", errors="replace").decode("ascii")
    disp = f'attachment; filename="{safe_ascii}"'
    if filename != safe_ascii:
        disp += f"; filename*=UTF-8''{quote(filename, safe='.')}"
    return disp


# region TEMPORARY: SFU STU title page — remove this region to disable the option
TITLE_PAGE_ID_SFU_STU = -1

_SFU_STU_TITLE_TYPST = r"""
#let labeled-block(content, label) = {
  align(center, [
    #block(
      width: 15cm,
      inset: 0pt,
      [
        #content
        #v(-14pt)
        #line(length: 100%, stroke: 0.5pt)
        #v(-17pt)
        #text(size: 12pt, fill: black)[#label]
      ]
    )
    #v(4pt)
  ])
}

#let institute-name = "Институт космических и информационных технологий"
#let department-name = "Информационные системы и технологии"
#let work-type = "ОТЧЕТ О ПРАКТИЧЕСКОЙ РАБОТЕ №5.2"
#let work-theme = "ETL-пайплайн для загрузки данных из MinIO в PostgreSQL"
#let teacher-name = "К.И. Пахомова"
#let student-group = "КИ23-14Б"
#let student-id = "032319377"
#let student-name = "К.Д. Буданов"
#let city-year = "Красноярск 2026"

#page(
  paper: "a4",
  margin: (left: 3cm, right: 1.5cm, top: 2cm, bottom: 2cm),
  numbering: none,
  header: none,
  footer: none,
)[
  #set text(
    font: ("Times New Roman", "DejaVu Serif", "Libertinus Serif"),
    size: 14pt,
    lang: "ru",
  )

#align(center, [
  Министерство науки и высшего образования РФ \
  Федеральное государственное автономное \
  образовательное учреждение высшего образования \
  *"СИБИРСКИЙ ФЕДЕРАЛЬНЫЙ УНИВЕРСИТЕТ"*
])

#v(1cm)

#labeled-block(institute-name, "институт")
#labeled-block(department-name, "кафедра")

#v(3cm)

#align(center, [*#work-type*])
#labeled-block(work-theme, "тема")

#v(1.3fr)

#table(
  columns: (2fr, 1fr, 1fr),
  inset: 0pt,
  stroke: none,
  align: horizon,

  [Преподаватель],
  [
    #block(height: 1.5cm, [
      #align(center, [
        #v(22pt)
        #line(length: 80%, stroke: 0.5pt)
        #v(-17pt)
        #text(size: 12pt)[подпись, дата]
      ])
    ])
  ],
  [
    #block(height: 1.5cm, [
      #align(center, [
        #v(10pt)
        #teacher-name
        #v(-15pt)
        #line(length: 100%, stroke: 0.5pt)
        #v(-17pt)
        #text(size: 12pt)[инициалы, фамилия]
      ])
    ])
  ],

  [#h(-28pt)
  Студент
   #box(
     stroke: (bottom: 0.5pt),
     inset: 0pt,
     [#student-group, #student-id]
   )
   #v(-17pt)
   #text(size: 12pt)[номер группы, зачетной книжки]
  ],
  [
    #block(height: 1.5cm, [
      #align(center, [
        #v(10.5pt)
        #line(length: 80%, stroke: 0.5pt)
        #v(-17pt)
        #text(size: 12pt)[подпись, дата]
      ])
    ])
  ],
  [
    #block(height: 1.5cm, [
      #align(center, [
        #v(-2pt)
        #student-name
        #v(-15pt)
        #line(length: 100%, stroke: 0.5pt)
        #v(-17pt)
        #text(size: 12pt)[инициалы, фамилия]
      ])
    ])
  ],
)

#v(1.5fr)

#align(center, city-year)
]
"""
# endregion


async def _resolve_title_source(
    title_page_id: int | None,
    title_repo: TitlePageRepository,
) -> tuple[str | None, bool]:
    """Возвращает Typst-фрагмент титульника и признак «до преамбулы».

    SFU-титульник идёт перед преамбулой, чтобы правило профиля
    ``show table.cell`` не переопределяло подписи на титульной странице.
    """
    if title_page_id is None:
        return None, False
    if title_page_id == TITLE_PAGE_ID_SFU_STU:
        return (
            _SFU_STU_TITLE_TYPST.strip() + "\n#pagebreak()\n#counter(page).update(2)\n",
            True,
        )
    title_page = await title_repo.get_by_id(title_page_id)
    if title_page is None:
        raise HTTPException(status_code=404, detail="Title page not found")
    tc = TitlePageContent.model_validate(title_page.content)
    return (
        generate_fragment(
            tc.elements,
            tc.paper,
            tc.variables,
            ignore_document_styles=tc.ignore_document_styles,
        ),
        False,
    )


def _build_profile_source(
    profile: Profile,
    typst_body: str,
    *,
    title_source: str | None,
    title_before_prefix: bool,
) -> str:
    """Единая сборка для PDF и export-typ; ошибки реестра → 409."""
    try:
        return build_typst_source(
            profile,
            typst_body,
            title_source=title_source,
            title_before_prefix=title_before_prefix,
        )
    except RegistryError as e:
        raise HTTPException(status_code=409, detail=f"Invalid profile options: {e}") from e


@router.get("/{profile_id}/preamble", response_class=PlainTextResponse)
async def get_preamble(
    profile_id: int,
    repo: ProfileRepository = Depends(get_profile_repository),
) -> PlainTextResponse:
    """Возвращает общий Typst-префикс профиля (fd + конфиг) для превью."""
    profile = await repo.get_by_id_with_styles(profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    try:
        preamble = build_typst_preamble(profile)
    except RegistryError as e:
        raise HTTPException(status_code=409, detail=f"Invalid profile options: {e}") from e
    return PlainTextResponse(preamble)


async def _resolve_image_asset_urls(
    typst_source: str, session: AsyncSession
) -> tuple[str, dict[str, bytes]]:
    """Находит в typst image(\".../image-assets/{id}/file\") или image(\"image-assets/{id}/file\"), подгружает файлы по id, возвращает (исходник с путями, asset_files)."""
    ids = list(
        {
            int(m.group(1))
            # FIXME что это блен, что за говнокодище
            for m in re.finditer(r'(?:https?://[^"]*?/)?image-assets/(\d+)/file', typst_source)
        }
    )
    asset_files: dict[str, bytes] = {}
    if ids:
        result = await session.execute(select(ImageAsset).where(ImageAsset.id.in_(ids)))
        assets = {a.id: a for a in result.scalars().all()}
        for aid in ids:
            asset = assets.get(aid)
            if not asset:
                continue
            path_key = f"image-assets/{aid}/file"
            file_path = IMAGES_DIR / Path(asset.path).name
            if file_path.is_file():
                asset_files[path_key] = file_path.read_bytes()
    modified = typst_source
    for m in re.finditer(
        r'image\s*\(\s*"(https?://[^"]*?/image-assets/(\d+)/file)"',
        typst_source,
    ):
        full_url, id_str = m.group(1), m.group(2)
        modified = modified.replace(full_url, f"image-assets/{id_str}/file", 1)
    return modified, asset_files


@router.post("/{profile_id}/generate-pdf", response_class=Response)
async def generate_pdf(
    profile_id: int,
    file: UploadFile,
    title_page_id: int | None = Query(
        None, description="ID титульной страницы для первой страницы PDF"
    ),
    repo: ProfileRepository = Depends(get_profile_repository),
    title_repo: TitlePageRepository = Depends(get_title_page_repository),
    session: AsyncSession = Depends(get_session),
) -> Response:
    """
    Загрузка Markdown-файла; конвертация в Typst со стилями профиля и компиляция в PDF.
    Возвращает байты PDF с Content-Disposition attachment.
    """
    profile = await repo.get_by_id_with_styles(profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    content = await _read_and_validate_markdown(file)

    try:
        typst_body = await markdown_to_typst(content)
    except PandocError as e:
        logger.exception("Pandoc failed: %s", e.stderr)
        raise HTTPException(status_code=500, detail="Markdown conversion failed") from e

    title_source, title_before_prefix = await _resolve_title_source(title_page_id, title_repo)
    full_typst = _build_profile_source(
        profile,
        typst_body,
        title_source=title_source,
        title_before_prefix=title_before_prefix,
    )

    full_typst, asset_files = await _resolve_image_asset_urls(full_typst, session)

    try:
        pdf_bytes = await compile_typst_to_pdf(
            full_typst, images_dir=IMAGES_DIR, asset_files=asset_files or None
        )
    except TypstCompileError as e:
        logger.exception("Typst compile failed: %s", e.stderr)
        raise HTTPException(status_code=500, detail="PDF compilation failed") from e

    filename = file.filename or "document.md"
    pdf_name = filename.rsplit(".", 1)[0] + ".pdf" if "." in filename else "document.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": _content_disposition_attachment(pdf_name)},
    )


@router.post("/{profile_id}/export-typ", response_class=PlainTextResponse)
async def export_typ(
    profile_id: int,
    file: UploadFile,
    title_page_id: int | None = Query(
        None, description="ID титульной страницы для первой страницы .typ"
    ),
    repo: ProfileRepository = Depends(get_profile_repository),
    title_repo: TitlePageRepository = Depends(get_title_page_repository),
) -> PlainTextResponse:
    """
    Загрузка Markdown-файла; конвертация в Typst со стилями профиля.
    Возвращает полный исходник .typ без компиляции в PDF.
    """
    profile = await repo.get_by_id_with_styles(profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    content = await _read_and_validate_markdown(file)

    try:
        typst_body = await markdown_to_typst(content)
    except PandocError as e:
        logger.exception("Pandoc failed: %s", e.stderr)
        raise HTTPException(status_code=500, detail="Markdown conversion failed") from e

    title_source, title_before_prefix = await _resolve_title_source(title_page_id, title_repo)
    full_typst = _build_profile_source(
        profile,
        typst_body,
        title_source=title_source,
        title_before_prefix=title_before_prefix,
    )

    filename = file.filename or "document.md"
    typ_name = filename.rsplit(".", 1)[0] + ".typ" if "." in filename else "document.typ"
    return PlainTextResponse(
        content=full_typst,
        headers={"Content-Disposition": _content_disposition_attachment(typ_name)},
    )
