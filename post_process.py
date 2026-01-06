import json
import re


def process_json(text):
    # 尝试解析文本是否为有效的JSON
    try:
        json_data = json.loads(text)
        # 如果是JSON格式，返回原始文本
        return text
    except json.JSONDecodeError:
        # 如果不是JSON格式，删除 {} 以外的内容
        start_index = text.find('{')
        end_index = text.rfind('}')
        if start_index != -1 and end_index != -1:
            return text[start_index:end_index + 1]
        else:
            # 如果没有找到 {} 包裹的内容，返回空字符串
            print(text)
            return ""


def extract_content_from_html(html_text):
    """
    从HTML文本中提取原始内容，保留基本的结构信息（如列表项换行）
    
    Args:
        html_text (str): 包含HTML标签的文本
        
    Returns:
        str: 提取出的纯文本内容
    """
    if not html_text:
        return ""

    # 1. 移除可能的 markdown 代码块标记 (```html ... ```)
    html_text = re.sub(r'```html\s*|\s*```', '', html_text, flags=re.IGNORECASE)
    
    # 2. 将一些块级标签替换为换行符，以保持可读性
    # 将 </div>, </p>, </li>, </h1>...</h6>, </header>, </section>, </article> 替换为换行
    block_tags = ['div', 'p', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'header', 'section', 'article', 'br']
    for tag in block_tags:
        if tag == 'br':
             html_text = re.sub(r'<br\s*/?>', '\n', html_text, flags=re.IGNORECASE)
        else:
            html_text = re.sub(f'</{tag}>', '\n', html_text, flags=re.IGNORECASE)

    # 3. 移除所有剩余的 HTML 标签
    text = re.sub(r'<[^>]+>', '', html_text)
    
    # 4. 处理 HTML 实体 (简单的处理)
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&amp;', '&')
    
    # 5. 清理多余的空白字符
    # 将连续的换行符替换为单个换行符，但保留段落感（如果是多个换行可能是有意的）
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join([line for line in lines if line]) # 移除空行
    
    return text.strip()
