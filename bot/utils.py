import re
from html import escape as html_escape


def markdown_to_html(text: str) -> str:
    """Convert AI markdown to Telegram HTML: code blocks, inline code, **bold**."""
    parts = []
    last_end = 0

    for match in re.finditer(r'```(?:\w*)\n?(.*?)```', text, flags=re.DOTALL):
        before = text[last_end:match.start()]
        parts.append(_convert_inline(before))
        code = match.group(1).strip()
        parts.append(f'<pre><code>{html_escape(code)}</code></pre>')
        last_end = match.end()

    parts.append(_convert_inline(text[last_end:]))
    return ''.join(parts)


def _convert_inline(text: str) -> str:
    parts = []
    last_end = 0

    for match in re.finditer(r'`([^`\n]+)`', text):
        before = text[last_end:match.start()]
        parts.append(_format_plain(before))
        parts.append(f'<code>{html_escape(match.group(1))}</code>')
        last_end = match.end()

    parts.append(_format_plain(text[last_end:]))
    return ''.join(parts)


def _format_plain(text: str) -> str:
    text = html_escape(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text, flags=re.DOTALL)
    text = re.sub(r'\*(.+?)\*',     r'\1',          text, flags=re.DOTALL)
    text = re.sub(r'__(.+?)__',     r'\1',          text, flags=re.DOTALL)
    text = re.sub(r'_(.+?)_',       r'\1',          text, flags=re.DOTALL)
    text = re.sub(r'^#{1,6}\s+',    '',             text, flags=re.MULTILINE)
    return text
