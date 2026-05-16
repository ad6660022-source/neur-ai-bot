import re


def strip_markdown(text: str) -> str:
    """Remove markdown formatting symbols so they don't appear as raw ** in Telegram HTML mode."""
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text, flags=re.DOTALL)
    text = re.sub(r'\*(.+?)\*',     r'\1', text, flags=re.DOTALL)
    text = re.sub(r'__(.+?)__',     r'\1', text, flags=re.DOTALL)
    text = re.sub(r'_(.+?)_',       r'\1', text, flags=re.DOTALL)
    text = re.sub(r'^#{1,6}\s+',    '',    text, flags=re.MULTILINE)
    return text
