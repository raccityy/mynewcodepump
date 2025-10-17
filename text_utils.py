def html_escape(text: str) -> str:
    """Escape special HTML characters for safe Telegram HTML parse mode."""
    if text is None:
        return ""
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
    )


def code_wrap(text: str) -> str:
    """Wrap the given text in <code> tags after escaping for HTML."""
    return f"<code>{html_escape(text)}</code>"


