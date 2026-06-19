import io
import zipfile
from pathlib import Path

from markitdown import MarkItDown
from markitdown_ocr import register_converters

from .affine import fetch_affine_document
from .client import get_client, get_model

_markitdown = MarkItDown()


class _OpenAICompatWrapper:
    """Wraps Anthropic client to provide OpenAI-compatible chat.completions interface for markitdown-ocr."""

    def __init__(self, anthropic_client, model):
        self._client = anthropic_client
        self._model = model
        self.chat = _ChatCompat(anthropic_client, model)


class _ChatCompat:

    def __init__(self, anthropic_client, model):
        self.completions = _CompletionsCompat(anthropic_client, model)


class _CompletionsCompat:

    def __init__(self, anthropic_client, model):
        self._client = anthropic_client
        self._model = model

    def create(self, model=None, messages=None, **kwargs):
        anthropic_messages = []
        for msg in messages:
            content_parts = []
            content = msg.get("content", "")
            if isinstance(content, str):
                content_parts.append({"type": "text", "text": content})
            elif isinstance(content, list):
                for part in content:
                    if part.get("type") == "text":
                        content_parts.append({"type": "text", "text": part["text"]})
                    elif part.get("type") == "image_url":
                        url = part["image_url"]["url"]
                        content_parts.append({
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": url.split(";")[0].split(":")[1],
                                "data": url.split(",")[1],
                            },
                        })
            anthropic_messages.append({"role": msg["role"], "content": content_parts})

        response = self._client.messages.create(
            model=model or self._model,
            max_tokens=4096,
            messages=anthropic_messages,
        )

        text = ""
        for block in response.content:
            if block.type == "text":
                text += block.text

        return _OpenAIResponse(text)


class _OpenAIResponse:

    def __init__(self, text):
        self.choices = [_OpenAIChoice(text)]


class _OpenAIChoice:

    def __init__(self, text):
        self.message = _OpenAIMessage(text)


class _OpenAIMessage:

    def __init__(self, text):
        self.content = text


# Initialize OCR with LLM Vision
_ocr_initialized = False
_ocr_error = None
try:
    _client = get_client()
    _model = get_model()
    _openai_compat = _OpenAICompatWrapper(_client, _model)
    register_converters(_markitdown, llm_client=_openai_compat, llm_model=_model)
    _ocr_initialized = True
except Exception as e:
    _ocr_error = str(e)


TOOLS = [
    {
        "name": "read_pdf",
        "description": "Extract text content from a PDF file. Returns the full text of the document in markdown format.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Absolute path to the PDF file",
                },
            },
            "required": ["file_path"],
        },
    },
    {
        "name": "read_docx",
        "description": "Extract text content from a DOCX (Microsoft Word) file. Returns the full text in markdown format.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Absolute path to the DOCX file",
                },
            },
            "required": ["file_path"],
        },
    },
    {
        "name": "read_pptx",
        "description": "Extract text content from a PPTX (PowerPoint) file. Returns text from all slides in markdown format.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Absolute path to the PPTX file",
                },
            },
            "required": ["file_path"],
        },
    },
    {
        "name": "read_xlsx",
        "description": "Extract content from an XLSX (Excel) file. Returns the spreadsheet data in markdown table format.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Absolute path to the XLSX file",
                },
            },
            "required": ["file_path"],
        },
    },
    {
        "name": "read_text_file",
        "description": "Read content of a text-based file (source code, text files, etc).",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Absolute path to the text file",
                },
            },
            "required": ["file_path"],
        },
    },
    {
        "name": "list_zip",
        "description": "List all files inside a ZIP archive. Returns a list of file paths within the archive.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Absolute path to the ZIP file",
                },
            },
            "required": ["file_path"],
        },
    },
    {
        "name": "read_zip_file",
        "description": "Read the content of a specific file inside a ZIP archive. Can read both text and binary files (binary files are returned as base64 or skipped).",
        "input_schema": {
            "type": "object",
            "properties": {
                "zip_path": {
                    "type": "string",
                    "description": "Absolute path to the ZIP file",
                },
                "inner_path": {
                    "type": "string",
                    "description": "Path of the file inside the ZIP archive",
                },
            },
            "required": ["zip_path", "inner_path"],
        },
    },
    {
        "name": "read_affine",
        "description": "Fetch and parse an Affine document from docs.ravonzz174.ru. Converts the document to markdown format. Use this when the assignment description contains a link to an Affine document.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Full URL to the Affine document (e.g., https://docs.ravonzz174.ru/workspace/{workspace_id}/{doc_id})",
                },
            },
            "required": ["url"],
        },
    },
]


def _execute_read_pdf(args: dict) -> str:
    try:
        result = _markitdown.convert(args["file_path"])
        return result.text_content or "PDF file contains no extractable text."
    except Exception as e:
        return f"Error reading PDF: {e}"


def _execute_read_docx(args: dict) -> str:
    try:
        result = _markitdown.convert(args["file_path"])
        return result.text_content or "DOCX file contains no text."
    except Exception as e:
        return f"Error reading DOCX: {e}"


def _execute_read_pptx(args: dict) -> str:
    try:
        result = _markitdown.convert(args["file_path"])
        return result.text_content or "PPTX file contains no text."
    except Exception as e:
        return f"Error reading PPTX: {e}"


def _execute_read_xlsx(args: dict) -> str:
    try:
        result = _markitdown.convert(args["file_path"])
        return result.text_content or "XLSX file contains no data."
    except Exception as e:
        return f"Error reading XLSX: {e}"


def _execute_read_text_file(args: dict) -> str:
    try:
        file_path = Path(args["file_path"])
        content = file_path.read_text(encoding="utf-8", errors="replace")
        if len(content) > 100000:
            return content[:100000] + "\n\n... [truncated, file too large]"
        return content
    except Exception as e:
        return f"Error reading file: {e}"


def _execute_list_zip(args: dict) -> str:
    try:
        with zipfile.ZipFile(args["file_path"], "r") as zf:
            names = zf.namelist()
            if not names:
                return "ZIP archive is empty."
            return "\n".join(names)
    except Exception as e:
        return f"Error listing ZIP: {e}"


def _execute_read_zip_file(args: dict) -> str:
    try:
        with zipfile.ZipFile(args["zip_path"], "r") as zf:
            inner_path = args["inner_path"]
            data = zf.read(inner_path)
            try:
                text = data.decode("utf-8")
                if len(text) > 100000:
                    return text[:100000] + "\n\n... [truncated, file too large]"
                return text
            except UnicodeDecodeError:
                return f"[Binary file: {inner_path}, size: {len(data)} bytes]"
    except Exception as e:
        return f"Error reading ZIP file: {e}"


def _execute_read_affine(args: dict) -> str:
    try:
        url = args["url"]
        return fetch_affine_document(url)
    except Exception as e:
        return f"Error reading Affine document: {e}"


TOOL_EXECUTORS = {
    "read_pdf": _execute_read_pdf,
    "read_docx": _execute_read_docx,
    "read_pptx": _execute_read_pptx,
    "read_xlsx": _execute_read_xlsx,
    "read_text_file": _execute_read_text_file,
    "list_zip": _execute_list_zip,
    "read_zip_file": _execute_read_zip_file,
    "read_affine": _execute_read_affine,
}


def execute_tool(name: str, args: dict) -> str:
    executor = TOOL_EXECUTORS.get(name)
    if not executor:
        return f"Unknown tool: {name}"
    return executor(args)
