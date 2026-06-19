import re

import pycrdt
import requests


AFFINE_BASE = "https://docs.ravonzz174.ru"

AFFINE_URL_PATTERN = re.compile(
    r"https?://docs\.ravonzz174\.ru/workspace/([a-zA-Z0-9-]+)/([a-zA-Z0-9]+)"
)


def parse_affine_url(url: str) -> tuple[str, str] | None:
    match = AFFINE_URL_PATTERN.search(url)
    if match:
        return match.group(1), match.group(2)
    return None


def safe_get(block, key, default=None):
    try:
        val = block[key]
        if hasattr(val, "to_py"):
            return val.to_py()
        return val
    except Exception:
        return default


def delta_to_text(val) -> str:
    if val is None:
        return ""
    if hasattr(val, "to_py"):
        val = val.to_py()
    if isinstance(val, list):
        return "".join(
            op.get("insert", "") for op in val if isinstance(op, dict)
        )
    if isinstance(val, str):
        return val
    return ""


def get_all_block_keys(block) -> list:
    try:
        return list(block.keys()) if hasattr(block, "keys") else []
    except Exception:
        return []


def image_block_to_markdown(block, workspace_id: str) -> str:
    source_id = safe_get(block, "prop:sourceId", "")
    caption = delta_to_text(safe_get(block, "prop:caption"))
    alt = caption or "image"

    if source_id:
        img_url = f"{AFFINE_BASE}/api/workspaces/{workspace_id}/blobs/{source_id}"
        md = f"![{alt}]({img_url})"
    else:
        md = f"![{alt}](<!-- sourceId not found -->)"

    if caption:
        md += f"\n*{caption}*"
    return md


def table_block_to_markdown(block) -> str:
    all_keys = get_all_block_keys(block)

    columns = {}
    for key in all_keys:
        if key.startswith("prop:columns.") and key.endswith(".order"):
            col_id = key[len("prop:columns.") : -len(".order")]
            columns[col_id] = safe_get(block, key, 0)

    rows = {}
    for key in all_keys:
        if key.startswith("prop:rows.") and key.endswith(".order"):
            row_id = key[len("prop:rows.") : -len(".order")]
            rows[row_id] = safe_get(block, key, 0)

    sorted_cols = sorted(columns.keys(), key=lambda c: columns[c])
    sorted_rows = sorted(rows.keys(), key=lambda r: rows[r])

    if not sorted_cols or not sorted_rows:
        return "*(пустая таблица)*"

    cells = {}
    for key in all_keys:
        if key.startswith("prop:cells.") and key.endswith(".text"):
            rest = key[len("prop:cells.") : -len(".text")]
            if ":" in rest:
                row_id, col_id = rest.split(":", 1)
                cells[(row_id, col_id)] = delta_to_text(safe_get(block, key, ""))

    header_row = sorted_rows[0]
    headers = [cells.get((header_row, col_id), "") for col_id in sorted_cols]
    if not any(headers):
        headers = [str(i + 1) for i in range(len(sorted_cols))]

    lines = []
    lines.append("| " + " | ".join(h.replace("|", "\\|") for h in headers) + " |")
    lines.append("| " + " | ".join("---" for _ in sorted_cols) + " |")

    for row_id in sorted_rows[1:]:
        row_cells = [
            cells.get((row_id, col_id), "").replace("|", "\\|").replace("\n", " ")
            for col_id in sorted_cols
        ]
        lines.append("| " + " | ".join(row_cells) + " |")

    return "\n".join(lines)


HEADING_MAP = {
    "h1": "#",
    "h2": "##",
    "h3": "###",
    "h4": "####",
    "h5": "#####",
    "h6": "######",
}


def block_to_markdown(
    blocks_map, block_id: str, workspace_id: str, depth: int = 0
) -> str:
    try:
        block = blocks_map[block_id]
    except Exception:
        return ""
    if block is None:
        return ""

    flavour = safe_get(block, "sys:flavour", "")
    children_ids = safe_get(block, "sys:children", []) or []
    lines = []

    if flavour == "affine:paragraph":
        ptype = safe_get(block, "prop:type", "text")
        text = delta_to_text(safe_get(block, "prop:text"))
        prefix = HEADING_MAP.get(ptype, "")
        if prefix:
            lines.append(f"{prefix} {text}")
        elif text:
            lines.append(text)

    elif flavour == "affine:list":
        ltype = safe_get(block, "prop:type", "bulleted")
        text = delta_to_text(safe_get(block, "prop:text"))
        checked = safe_get(block, "prop:checked", False)
        indent = "  " * depth
        if ltype == "todo":
            marker = "- [x]" if checked else "- [ ]"
        elif ltype == "numbered":
            marker = "1."
        else:
            marker = "-"
        lines.append(f"{indent}{marker} {text}")

    elif flavour == "affine:code":
        lang = safe_get(block, "prop:language", "")
        text = delta_to_text(safe_get(block, "prop:text"))
        lines.append(f"```{lang}\n{text}\n```")

    elif flavour == "affine:image":
        lines.append(image_block_to_markdown(block, workspace_id))

    elif flavour == "affine:table":
        lines.append(table_block_to_markdown(block))
        return "\n".join(lines)

    elif flavour == "affine:divider":
        lines.append("---")

    elif flavour == "affine:bookmark":
        url = safe_get(block, "prop:url", "")
        title = safe_get(block, "prop:title", url) or url
        lines.append(f"[{title}]({url})")

    for child_id in children_ids:
        child_md = block_to_markdown(blocks_map, child_id, workspace_id, depth + 1)
        if child_md:
            lines.append(child_md)

    return "\n\n".join(filter(None, lines))


def yjs_to_markdown(raw_bytes: bytes, workspace_id: str) -> str:
    ydoc = pycrdt.Doc()
    ydoc.apply_update(raw_bytes)

    blocks_map = ydoc.get("blocks", type=pycrdt.Map)

    root_id = None
    for key in blocks_map.keys():
        if safe_get(blocks_map[key], "sys:flavour") == "affine:page":
            root_id = key
            break

    if not root_id:
        return "Корневой блок не найден"

    root_children = safe_get(blocks_map[root_id], "sys:children", []) or []

    parts = []
    for child_id in root_children:
        md = block_to_markdown(blocks_map, child_id, workspace_id)
        if md:
            parts.append(md)

    return "\n\n".join(parts)


def fetch_affine_document(url: str) -> str:
    parsed = parse_affine_url(url)
    if not parsed:
        return f"Ошибка: не удалось распарсить URL '{url}'"

    workspace_id, doc_id = parsed
    api_url = f"{AFFINE_BASE}/api/workspaces/{workspace_id}/docs/{doc_id}"

    try:
        resp = requests.get(api_url, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        return f"Ошибка при загрузке документа: {e}"

    return yjs_to_markdown(resp.content, workspace_id)
