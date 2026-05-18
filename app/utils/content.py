"""
Content utils - 内容处理工具
"""
import re


def _merge_style(html: str, tag: str, extra_style: str) -> str:
    """给标签合并 style：不覆盖已有属性，仅补充缺失的样式"""
    pattern = re.compile(rf'<{tag}\b([^>]*?)(/?)>', re.IGNORECASE)

    def _replacer(m: re.Match) -> str:
        attrs = m.group(1).strip()
        self_closing = m.group(2) or ""

        # 提取已有 style
        style_match = re.search(r'style="([^"]*)"', attrs)
        if style_match:
            existing = style_match.group(1)
            merged = existing.rstrip(";")
            for prop in extra_style.rstrip(";").split(";"):
                prop = prop.strip()
                key = prop.split(":")[0].strip()
                if key and not re.search(rf'(?:^|;)\s*{re.escape(key)}\s*:', merged):
                    merged += ";" + prop
            merged += ";"
            # 替换原有 style 属性值
            attrs = attrs[:style_match.start(1)] + merged + attrs[style_match.end(1):]
        else:
            # 没有 style，直接追加
            attrs = f'{attrs} style="{extra_style}"'.strip()

        if self_closing:
            return f"<{tag} {attrs} />"
        return f"<{tag} {attrs}>"

    return pattern.sub(_replacer, html)


def enhance_content_html(html: str) -> str:
    """为富文本内容添加移动端友好的内联样式，适配微信 rich-text 渲染"""
    if not html:
        return html

    # 只补充间距/行高类样式，不覆盖已有的颜色/字号
    html = _merge_style(html, "p", "line-height:1.8;margin-bottom:20px;letter-spacing:0.5px;")
    html = _merge_style(html, "h1", "line-height:1.5;margin:28px 0 12px;")
    html = _merge_style(html, "h2", "line-height:1.5;margin:24px 0 10px;")
    html = _merge_style(html, "h3", "line-height:1.5;margin:20px 0 8px;")
    html = _merge_style(html, "ul", "padding-left:20px;margin-bottom:20px;line-height:1.8;")
    html = _merge_style(html, "ol", "padding-left:20px;margin-bottom:20px;line-height:1.8;")
    html = _merge_style(html, "li", "margin-bottom:6px;")
    html = _merge_style(html, "img", "max-width:100%;height:auto;display:block;margin:20px auto;border-radius:4px;")
    html = _merge_style(html, "blockquote", "border-left:3px solid #07C160;padding:10px 16px;margin:20px 0;background:#f7fcf9;border-radius:0 4px 4px 0;")
    html = _merge_style(html, "table", "width:100%;border-collapse:collapse;margin:20px 0;")
    html = _merge_style(html, "th", "border:1px solid #e0e0e0;padding:10px 12px;background:#f7f7f7;text-align:left;")
    html = _merge_style(html, "td", "border:1px solid #e0e0e0;padding:8px 12px;")
    html = _merge_style(html, "a", "color:#07C160;text-decoration:none;")
    html = _merge_style(html, "hr", "border:none;border-top:1px solid #eee;margin:28px 0;")

    # 移除简陋的 "(返回顶部)"
    html = html.replace("（返回顶部）", "")
    html = html.replace("(返回顶部)", "")

    return html
