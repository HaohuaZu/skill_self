from __future__ import annotations

import html as html_lib
import re

from markdown_it import MarkdownIt
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import TextLexer, get_lexer_by_name
from pygments.style import Style
from pygments.token import Comment, Keyword, Name, Operator, String, Text
from pygments.util import ClassNotFound


BAUHAUS_STYLES = {
    "container": 'max-width: 100%; margin: 0 auto; padding: 24px 20px 48px 20px; font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 16px; line-height: 1.65 !important; color: #1a1a1a !important; background-color: #ffffff !important; word-wrap: break-word;',
    "h1": "font-size: 34px; font-weight: 900; color: #e30613 !important; line-height: 1.2 !important; margin: 38px 0 16px; letter-spacing: -0.02em; text-transform: uppercase;",
    "h2": "font-size: 26px; font-weight: 700; color: #004d9f !important; line-height: 1.35 !important; margin: 32px 0 16px;",
    "h3": "font-size: 21px; font-weight: 600; color: #1a1a1a !important; line-height: 1.4 !important; margin: 28px 0 14px;",
    "h4": "font-size: 18px; font-weight: 600; color: #1a1a1a !important; line-height: 1.4 !important; margin: 24px 0 12px;",
    "p": "margin: 18px 0 !important; line-height: 1.65 !important; color: #1a1a1a !important;",
    "strong": "font-weight: 900; color: #e30613 !important;",
    "em": "font-style: italic; color: #555 !important;",
    "a": "color: #004d9f !important; text-decoration: none; border-bottom: 2px solid #f5a623; padding-bottom: 1px;",
    "ul": "margin: 16px 0; padding-left: 28px; list-style-type: disc !important; list-style-position: outside; margin-left: 0;",
    "ol": "margin: 16px 0; padding-left: 28px; list-style-type: decimal !important; list-style-position: outside; margin-left: 0;",
    "li": "margin: 8px 0; line-height: 1.65 !important; color: #1a1a1a !important; display: list-item !important;",
    "blockquote": "margin: 24px 0; padding: 16px 20px; background-color: #fff4d6 !important; border-left: 6px solid #f5a623; color: #333 !important; border-radius: 0;",
    "code": 'font-family: "SF Mono", Consolas, monospace; padding: 3px 6px; background-color: #f0f0f0 !important; color: #004d9f !important; border-radius: 0; font-size: 13px !important; line-height: 1.5 !important;',
    "pre": "margin: 24px 0; padding: 20px; background-color: #f0f0f0 !important; border-radius: 0; overflow-x: auto; font-size: 13px !important; line-height: 1.5 !important; border-left: 6px solid #e30613;",
    "code_block_shell": "margin: 24px 0; padding: 20px; background-color: #f0f0f0 !important; border-radius: 0; overflow-x: auto; font-size: 13px !important; line-height: 1.5 !important; border-left: 6px solid #e30613; font-variant-ligatures: none; tab-size: 2;",
    "code_block_header": "margin-bottom: 12px; white-space: nowrap;",
    "code_block_code": 'display: block; font-size: inherit !important; line-height: inherit !important; font-style: normal !important; white-space: pre !important; word-break: keep-all !important; overflow-wrap: normal !important; word-wrap: normal !important; font-family: "SF Mono", Consolas, monospace;',
    "image_grid": "display: block; overflow-x: scroll; overflow-y: hidden; white-space: nowrap; width: 100%; margin: 24px 0; padding: 4px 0 10px 0; -webkit-overflow-scrolling: touch;",
    "image_grid_table": "border-collapse: separate; border-spacing: 12px 0;",
    "grid_card": "background-color: #ffffff !important; border-radius: 16px !important; box-sizing: border-box; box-shadow: 0 10px 24px rgba(15,23,42,0.14), 0 2px 8px rgba(15,23,42,0.08); border: 1px solid #e8e8e8; padding: 8px; overflow: hidden;",
    "grid_img": "display: block; vertical-align: top; margin: 0 !important; background-color: #ffffff !important; box-sizing: border-box; object-fit: contain;",
    "list_shell": "margin: 16px 0; padding-left: 0; list-style: none !important; margin-left: 0;",
    "list_item": "margin: 8px 0; line-height: 1.65 !important; color: #1a1a1a !important; list-style: none !important;",
    "list_marker": "display: inline-block; width: 22px; color: #1a1a1a !important; font-weight: 700;",
    "list_body": "display: inline; color: #1a1a1a !important;",
    "hr": "margin: 36px auto; border: none; height: 3px; background-color: #1a1a1a !important; width: 100%;",
    "img": "display:block; width:100%; max-width:100%; height:auto; margin:30px auto !important; padding:8px !important; border-radius:0 !important; box-sizing:border-box; border:3px solid #1a1a1a;",
    "table": "width: 100%; margin: 24px 0; border-collapse: collapse; font-size: 15px;",
    "th": "background-color: #004d9f !important; padding: 16px 16px; text-align: left; font-weight: 700; color: #ffffff !important; border: 3px solid #1a1a1a;",
    "td": "padding: 16px 16px; border: 3px solid #1a1a1a; color: #1a1a1a !important; font-weight: 500;",
    "tr": "border: none;",
}

MARKDOWN_IMAGE_PATTERN = re.compile(r"!\[[^\]]*]\(([^)]+)\)")
HTML_IMAGE_PATTERN = re.compile(r'<img[^>]+src=["\']([^"\']+)["\']', re.IGNORECASE)
FEISHU_IMAGE_TOKEN_PATTERN = re.compile(r'<image\s+token="([^"]+)"[^/]*/>')
STYLE_ATTR_PATTERN = re.compile(r'\sstyle="([^"]*)"')
CLASS_ATTR_PATTERN = re.compile(r'\sclass="([^"]*)"')
LANGUAGE_CLASS_PATTERN = re.compile(r'language-([A-Za-z0-9_+#.-]+)')
LARK_TABLE_PATTERN = re.compile(r"<lark-table(?P<attrs>[^>]*)>(?P<body>.*?)</lark-table>", re.IGNORECASE | re.DOTALL)
LARK_TABLE_ROW_PATTERN = re.compile(r"<lark-tr>\s*(?P<body>.*?)\s*</lark-tr>", re.IGNORECASE | re.DOTALL)
LARK_TABLE_CELL_PATTERN = re.compile(r"<lark-td>\s*(?P<body>.*?)\s*</lark-td>", re.IGNORECASE | re.DOTALL)
QUOTE_CONTAINER_PATTERN = re.compile(r"<quote-container>\s*(?P<body>.*?)\s*</quote-container>", re.IGNORECASE | re.DOTALL)
GRID_PATTERN = re.compile(r"<grid(?P<attrs>[^>]*)>\s*(?P<body>.*?)\s*</grid>", re.IGNORECASE | re.DOTALL)
COLUMN_PATTERN = re.compile(r"<column(?P<attrs>[^>]*)>\s*(?P<body>.*?)\s*</column>", re.IGNORECASE | re.DOTALL)
CODE_BLOCK_PATTERN = re.compile(
    r"<pre(?P<pre_attrs>[^>]*)>\s*<code(?P<code_attrs>[^>]*)>(?P<code>.*?)</code>\s*</pre>",
    re.IGNORECASE | re.DOTALL,
)
IMAGE_PARAGRAPH_GROUP_PATTERN = re.compile(
    r"(?P<group>(?:<p[^>]*>\s*<img[^>]+>\s*</p>\s*){2,})",
    re.IGNORECASE | re.DOTALL,
)
IMAGE_TAG_PATTERN = re.compile(r"<img[^>]+>", re.IGNORECASE)
LIST_BLOCK_PATTERN = re.compile(r"<(?P<tag>ul|ol)(?P<attrs>[^>]*)>\s*(?P<body>.*?)\s*</(?P=tag)>", re.IGNORECASE | re.DOTALL)
LIST_ITEM_PATTERN = re.compile(r"<li(?P<attrs>[^>]*)>\s*(?P<body>.*?)\s*</li>", re.IGNORECASE | re.DOTALL)
MARKDOWN = MarkdownIt("commonmark", {"html": True, "linkify": True})
MARKDOWN.enable("table")


class RaphaelCodeStyle(Style):
    default_style = ""
    styles = {
        Text: "",
        Comment: "italic #6a737d",
        Keyword: "bold #d73a49",
        Operator: "#1a1a1a",
        String: "#24292e",
        Name.Attribute: "#6f42c1",
        Name.Function: "bold #6f42c1",
        Name.Class: "bold #6f42c1",
    }


PYGMENTS_FORMATTER = HtmlFormatter(nowrap=True, noclasses=True, style=RaphaelCodeStyle)


def extract_markdown_image_urls(markdown: str) -> list[str]:
    urls: list[str] = []
    for pattern in (MARKDOWN_IMAGE_PATTERN, HTML_IMAGE_PATTERN):
        for match in pattern.findall(markdown):
            if match not in urls:
                urls.append(match)
    return urls


def replace_feishu_image_tokens(markdown: str, mapping: dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        token = match.group(1)
        target = mapping.get(token)
        if not target:
            return match.group(0)
        return f"![{token}]({target})"

    return FEISHU_IMAGE_TOKEN_PATTERN.sub(replace, markdown)


def replace_image_urls(html: str, mapping: dict[str, str]) -> str:
    updated = html
    for source, target in mapping.items():
        updated = updated.replace(source, target)
    return updated


def preprocess_markdown(markdown: str) -> str:
    markdown = _convert_quote_containers(markdown)
    markdown = _convert_grid_blocks(markdown)
    markdown = _convert_lark_tables(markdown)
    lines = markdown.splitlines()
    normalized: list[str] = []
    for index, line in enumerate(lines):
        if (
            index > 0
            and re.match(r"^\s*(?:-|\*|\+|\d+\.)\s+", lines[index - 1])
            and line.strip()
            and not re.match(r"^\s*(?:-|\*|\+|\d+\.|#|>|```)", line)
            and (not normalized or normalized[-1] != "")
        ):
            normalized.append("")
        normalized.append(line)
    return "\n".join(normalized)


def _convert_quote_containers(markdown: str) -> str:
    def replace(match: re.Match[str]) -> str:
        body = re.sub(r"\s+", " ", match.group("body")).strip()
        if not body:
            return ""
        return "\n" + "\n".join(f"> {line}" for line in body.splitlines() if line.strip()) + "\n"

    return QUOTE_CONTAINER_PATTERN.sub(replace, markdown)


def _convert_grid_blocks(markdown: str) -> str:
    def replace(match: re.Match[str]) -> str:
        columns = COLUMN_PATTERN.findall(match.group("body"))
        images: list[str] = []
        for _, column_body in columns:
            for pattern in (MARKDOWN_IMAGE_PATTERN, HTML_IMAGE_PATTERN, FEISHU_IMAGE_TOKEN_PATTERN):
                for source in pattern.findall(column_body):
                    if source not in images:
                        images.append(source)
        if not images:
            return ""
        count = len(images)
        cols = min(max(count, 2), 3)
        image_markup = "".join(
            f'<td class="grid-card" style="{html_lib.escape(BAUHAUS_STYLES["grid_card"], quote=True)}">'
            f'<img src="{html_lib.escape(token)}" alt="" class="grid-img" style="{html_lib.escape(_grid_image_style(count), quote=True)}" />'
            "</td>"
            for token in images
        )
        return (
            f'\n<div class="image-grid" data-grid-cols="{cols}" style="{html_lib.escape(BAUHAUS_STYLES["image_grid"], quote=True)}">'
            f'<table class="image-grid-table" style="{html_lib.escape(_grid_table_style(count), quote=True)}"><tbody><tr>{image_markup}</tr></tbody></table>'
            "</div>\n"
        )

    return GRID_PATTERN.sub(replace, markdown)


def _grid_card_width(count: int) -> int:
    if count <= 2:
        return 420
    if count == 3:
        return 360
    return 320


def _grid_track_width(count: int) -> int:
    card_width = _grid_card_width(count)
    gap = 24
    return (card_width * count) + (gap * max(count - 1, 0)) + 24


def _grid_table_style(count: int) -> str:
    return f'{BAUHAUS_STYLES["image_grid_table"]} width: {_grid_track_width(count)}px;'


def _grid_image_style(count: int) -> str:
    width = f"{_grid_card_width(count)}px"
    return f"width: {width}; max-width: none; height: auto; {BAUHAUS_STYLES['grid_img']}"


def _grid_image_style_from_attrs(attrs: str) -> str:
    match = STYLE_ATTR_PATTERN.search(attrs)
    if match:
        return html_lib.unescape(match.group(1))
    return BAUHAUS_STYLES["grid_img"]


def _render_custom_lists(html: str) -> str:
    def replace(match: re.Match[str]) -> str:
        tag = match.group("tag").lower()
        items = LIST_ITEM_PATTERN.findall(match.group("body"))
        if not items:
            return match.group(0)
        rendered_items: list[str] = []
        for index, (_, body) in enumerate(items, start=1):
            marker = f"{index}." if tag == "ol" else "•"
            rendered_items.append(
                f'<li class="list-item" style="{html_lib.escape(BAUHAUS_STYLES["list_item"], quote=True)}">'
                f'<span class="list-marker" style="{html_lib.escape(BAUHAUS_STYLES["list_marker"], quote=True)}">{marker}</span>'
                f'<span class="list-body" style="{html_lib.escape(BAUHAUS_STYLES["list_body"], quote=True)}">{body.strip()}</span>'
                "</li>"
            )
        class_name = "list-ordered" if tag == "ol" else "list-unordered"
        return f'<{tag} class="{class_name}" style="{html_lib.escape(BAUHAUS_STYLES["list_shell"], quote=True)}">{"".join(rendered_items)}</{tag}>'

    return LIST_BLOCK_PATTERN.sub(replace, html)


def _preserve_indent(line: str) -> str:
    match = re.match(r"^[ \t]+", line)
    if not match:
        return line or "&nbsp;"
    raw = match.group(0)
    prefix = raw.replace("\t", "&nbsp;&nbsp;&nbsp;&nbsp;").replace(" ", "&nbsp;")
    return prefix + line[len(raw) :]


def _render_code_lines(highlighted: str) -> str:
    lines = highlighted.split("\n")
    rendered: list[str] = []
    for index, line in enumerate(lines):
        rendered.append(
            f'<span class="code-line" style="display: block; white-space: pre !important; word-break: keep-all !important; overflow-wrap: normal !important; word-wrap: normal !important;">{_preserve_indent(line)}</span>'
        )
        if index != len(lines) - 1:
            rendered.append("<br/>")
    return "".join(rendered)


def _convert_lark_tables(markdown: str) -> str:
    def replace_table(match: re.Match[str]) -> str:
        attrs = match.group("attrs")
        rows = LARK_TABLE_ROW_PATTERN.findall(match.group("body"))
        header_row = 'header-row="false"' not in attrs.lower()
        rendered_rows: list[str] = []
        for row_index, row in enumerate(rows):
            cells = [re.sub(r"\s+", " ", cell).strip() for cell in LARK_TABLE_CELL_PATTERN.findall(row)]
            if not cells:
                continue
            tag = "th" if header_row and row_index == 0 else "td"
            rendered_cells = "".join(f"<{tag}>{html_lib.escape(cell)}</{tag}>" for cell in cells)
            rendered_rows.append(f"<tr>{rendered_cells}</tr>")
        if not rendered_rows:
            return ""
        if header_row:
            head = f"<thead>{rendered_rows[0]}</thead>"
            body = f"<tbody>{''.join(rendered_rows[1:])}</tbody>" if len(rendered_rows) > 1 else ""
            return f"<table>{head}{body}</table>"
        return f"<table><tbody>{''.join(rendered_rows)}</tbody></table>"

    return LARK_TABLE_PATTERN.sub(replace_table, markdown)


def _apply_tag_style(html: str, tag: str, style: str) -> str:
    if tag == "img":
        return re.sub(
            rf"<{tag}(?P<attrs>[^>]*)>",
            lambda match: _preserve_tag(tag, match.group("attrs"))
            if "grid-img" in match.group("attrs")
            else _inject_style(tag, match.group("attrs"), style),
            html,
            flags=re.IGNORECASE,
        )
    if tag in {"table", "tr", "td"}:
        return re.sub(
            rf"<{tag}(?P<attrs>[^>]*)>",
            lambda match: _preserve_tag(tag, match.group("attrs"))
            if any(
                class_name in match.group("attrs")
                for class_name in ("image-grid-table", "grid-card")
            )
            else _inject_style(tag, match.group("attrs"), style),
            html,
            flags=re.IGNORECASE,
        )
    if tag in {"ul", "ol", "li"}:
        return re.sub(
            rf"<{tag}(?P<attrs>[^>]*)>",
            lambda match: _preserve_tag(tag, match.group("attrs"))
            if any(
                class_name in match.group("attrs")
                for class_name in ("list-ordered", "list-unordered", "list-item")
            )
            else _inject_style(tag, match.group("attrs"), style),
            html,
            flags=re.IGNORECASE,
        )
    return re.sub(
        rf"<{tag}(?P<attrs>[^>]*)>",
        lambda match: _inject_style(tag, match.group("attrs"), style),
        html,
        flags=re.IGNORECASE,
    )


def _merge_style_attr(attrs: str, style: str) -> str:
    match = STYLE_ATTR_PATTERN.search(attrs)
    if not match:
        return f'{attrs} style="{html_lib.escape(style, quote=True)}"'
    existing = html_lib.unescape(match.group(1))
    merged = f"{existing.rstrip(';')}; {style}" if existing.strip() else style
    return STYLE_ATTR_PATTERN.sub(
        f' style="{html_lib.escape(merged, quote=True)}"',
        attrs,
        count=1,
    )


def _merge_class_attr(attrs: str, class_name: str) -> str:
    match = CLASS_ATTR_PATTERN.search(attrs)
    if not match:
        return f'{attrs} class="{class_name}"'
    existing = match.group(1)
    classes = existing.split()
    if class_name not in classes:
        classes.append(class_name)
    return CLASS_ATTR_PATTERN.sub(f' class="{" ".join(classes)}"', attrs, count=1)


def _inject_style(tag: str, attrs: str, style: str) -> str:
    cleaned_attrs = attrs.rstrip()
    self_closing = cleaned_attrs.endswith("/")
    if self_closing:
        cleaned_attrs = cleaned_attrs[:-1].rstrip()
    cleaned_attrs = _merge_style_attr(cleaned_attrs, style)
    suffix = " /" if self_closing else ""
    return f"<{tag}{cleaned_attrs}{suffix}>"


def _preserve_tag(tag: str, attrs: str) -> str:
    cleaned_attrs = attrs.rstrip()
    self_closing = cleaned_attrs.endswith("/")
    if self_closing:
        cleaned_attrs = cleaned_attrs[:-1].rstrip()
    suffix = " /" if self_closing else ""
    return f"<{tag}{cleaned_attrs}{suffix}>"


def _extract_language(code_attrs: str) -> str:
    match = LANGUAGE_CLASS_PATTERN.search(code_attrs)
    if not match:
        return "text"
    return match.group(1).lower()


def _highlight_code(code: str, language: str) -> str:
    try:
        lexer = get_lexer_by_name(language)
    except ClassNotFound:
        lexer = TextLexer()
    return highlight(code, lexer, PYGMENTS_FORMATTER).rstrip()


def _render_code_blocks(html: str) -> str:
    def replace(match: re.Match[str]) -> str:
        code_attrs = match.group("code_attrs")
        raw_code = html_lib.unescape(match.group("code"))
        language = _extract_language(code_attrs)
        highlighted = _render_code_lines(_highlight_code(raw_code, language))
        dots = "".join(
            [
                '<span style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background: #ff5f56; margin-right: 6px;"></span>',
                '<span style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background: #ffbd2e; margin-right: 6px;"></span>',
                '<span style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background: #27c93f;"></span>',
            ]
        )
        return (
            f'<pre style="{html_lib.escape(BAUHAUS_STYLES["code_block_shell"], quote=True)}">'
            f'<div style="{html_lib.escape(BAUHAUS_STYLES["code_block_header"], quote=True)}">{dots}</div>'
            f'<code class="hljs language-{language}" style="{html_lib.escape(BAUHAUS_STYLES["code_block_code"], quote=True)}">{highlighted}</code>'
            "</pre>"
        )

    return CODE_BLOCK_PATTERN.sub(replace, html)


def _decorate_grid_image(image_html: str, count: int) -> str:
    grid_style = _grid_image_style(count)
    image_html = re.sub(
        r"<img(?P<attrs>[^>]+)>",
        lambda match: f'<img{_merge_style_attr(_merge_class_attr(match.group("attrs"), "grid-img"), grid_style)}>',
        image_html,
        count=1,
        flags=re.IGNORECASE,
    )
    return image_html


def _render_image_grids(html: str) -> str:
    def replace(match: re.Match[str]) -> str:
        images = IMAGE_TAG_PATTERN.findall(match.group("group"))
        if len(images) < 2:
            return match.group("group")
        count = len(images)
        decorated = "".join(
            f'<td class="grid-card" style="{html_lib.escape(BAUHAUS_STYLES["grid_card"], quote=True)}">{_decorate_grid_image(image, count)}</td>'
            for image in images
        )
        return (
            f'<div class="image-grid" style="{html_lib.escape(BAUHAUS_STYLES["image_grid"], quote=True)}">'
            f'<table class="image-grid-table" style="{html_lib.escape(_grid_table_style(count), quote=True)}"><tbody><tr>{decorated}</tr></tbody></table>'
            "</div>"
        )

    return IMAGE_PARAGRAPH_GROUP_PATTERN.sub(replace, html)


def render_bauhaus_html(markdown: str) -> str:
    html = MARKDOWN.render(preprocess_markdown(markdown))
    html = _render_custom_lists(html)
    for tag in ("h1", "h2", "h3", "h4", "p", "strong", "em", "a", "ul", "ol", "li", "blockquote", "code", "pre", "hr", "img", "table", "th", "td", "tr"):
        html = _apply_tag_style(html, tag, BAUHAUS_STYLES[tag])
    html = _render_code_blocks(html)
    html = _render_image_grids(html)
    return f'<section style="{html_lib.escape(BAUHAUS_STYLES["container"], quote=True)}">{html}</section>'
