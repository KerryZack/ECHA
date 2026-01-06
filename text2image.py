import os
import random
import platform
from PIL import Image, ImageDraw, ImageFont


from pilmoji import Pilmoji
PILMOJI_AVAILABLE = True
# except ImportError:
#     print("⚠️ Warning: pilmoji not installed. Install with: pip install pilmoji")
#     PILMOJI_AVAILABLE = False

def generate_image_with_text_and_overlays(
    text_string,
    image_id,
    save_path="generated_images/",
    width=800,
    height=1000,
    font_path="arial.ttf",
    font_size=30,
    text_color=(0, 0, 0),
    background_color=(255, 255, 255),
    emoji_folder_path="emojis/",
    insert_emojis=True,
    mask_percentage=0.14,
    overlay_image_path_bottom_right=None,
    overlay_image_size_bottom_right=(150, 150),
    overlay_image_path_bottom_left=None,
    overlay_image_size_bottom_left=(150, 150),
    custom_filename=None,  # 🆕 支持自定义文件名
):
    """
    使用 Pilmoji 支持emoji渲染的图像生成函数
    
    Args:
        custom_filename: 自定义文件名（不含扩展名），如果为None则使用image_id
    """
    os.makedirs(save_path, exist_ok=True)
    # 🆕 支持自定义文件名
    if custom_filename:
        output_filename = os.path.join(save_path, f"{custom_filename}.png")
    else:
        output_filename = os.path.join(save_path, f"{image_id}.png")

    # 🔧 只替换箭头符号，保留其他emoji
    text_string = text_string.replace('→', '->')
    text_string = text_string.replace('⇒', '=>') 
    text_string = text_string.replace('➜', '->')
    text_string = text_string.replace('➡️', '->')
    text_string = text_string.replace('➡', '->')
    
    # 🆕 替换bullet point为星号，确保在Linux服务器上正常显示
    text_string = text_string.replace('•', '*')

    # 创建画布
    img = Image.new("RGB", (width, height), color=background_color)
    
    # 加载字体
    font = None
    system = platform.system()
    
    # 尝试加载指定的字体
    if font_path and os.path.exists(font_path):
        try:
            font = ImageFont.truetype(font_path, font_size)
            print(f"✅ Loaded font: {font_path}")
        except Exception as e:
            print(f"⚠️ Warning: Failed to load {font_path}: {e}")
    
    # 如果指定字体加载失败，尝试系统字体
    if font is None:
        print(f"Trying system fonts for {system}...")
        if system == "Darwin":  # macOS
            font_paths = [
                "/System/Library/Fonts/Helvetica.ttc",
                "/System/Library/Fonts/Arial.ttf",
                "/Library/Fonts/Arial.ttf",
            ]
        elif system == "Linux":
            # Linux常见字体路径
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
                "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
                "/usr/share/fonts/TTF/DejaVuSans.ttf",
                "/usr/share/fonts/TTF/LiberationSans-Regular.ttf",
            ]
        else:  # Windows or others
            font_paths = [
                "C:/Windows/Fonts/arial.ttf",
                "C:/Windows/Fonts/ARIAL.TTF",
            ]
        
        # 尝试加载系统字体
        for path in font_paths:
            if os.path.exists(path):
                try:
                    font = ImageFont.truetype(path, font_size)
                    print(f"✅ Loaded system font: {path}")
                    break
                except Exception as e:
                    continue
        
        # 如果所有字体都加载失败，使用默认字体
        if font is None:
            print(f"⚠️ Warning: All font loading attempts failed, using default font")
            font = ImageFont.load_default()
            # 默认字体通常很小，需要调整估算系数
            print(f"⚠️ Note: Default font may have different metrics, text width calculation may be inaccurate")

    # 🔍 检测是否包含emoji
    has_emoji = any(ord(char) > 0x1F300 for char in text_string)
    
    if has_emoji and PILMOJI_AVAILABLE:
        print(f"✅ Detected emoji, using Pilmoji for rendering")
        # 使用 Pilmoji 渲染（支持彩色emoji）
        result = render_text_with_pilmoji(
            img, text_string, font, font_size, text_color, 
            width, height, mask_percentage
        )
        # 处理返回的图片和高度（可能是元组）
        if isinstance(result, tuple):
            img, actual_height = result
        else:
            img = result
            actual_height = height
    else:
        if has_emoji and not PILMOJI_AVAILABLE:
            print(f"⚠️ Emoji detected but Pilmoji not available. Please install: pip install pilmoji")
        
        # 降级到普通渲染（emoji会显示为方框）
        img = render_text_legacy(
            img, text_string, font, font_size, text_color,
            width, height, emoji_folder_path, insert_emojis, mask_percentage
        )
        actual_height = height
    
    # 🆕 添加overlay图片（使用实际高度）
    img = add_overlays(
        img, width, actual_height,  # 使用实际高度而不是原始height
        overlay_image_path_bottom_right, overlay_image_size_bottom_right,
        overlay_image_path_bottom_left, overlay_image_size_bottom_left
    )
    
    # 保存图片
    img.save(output_filename)
    print(f"✅ Image saved: {output_filename}")
    return output_filename


def render_text_with_pilmoji(img, text_string, font, font_size, text_color, width, height, mask_percentage):
    """
    使用 Pilmoji 渲染文本（支持emoji）
    改进：支持单词级别的自动换行，避免文字截断
    """
    # 🆕 修改：进一步减少边距，增加文字区域宽度，让文字占满整张图片
    x_offset, y_offset = 20, 10
    max_width = width - 40  # 文字区域 = width - 40，充分利用图片宽度（左右各留20px边距）
    line_height = font_size + 8
    
    # 使用 Pilmoji 渲染
    with Pilmoji(img) as pilmoji:
        lines = text_string.split('\n')
        char_positions = []
        current_y = y_offset
        
        for line_idx, line in enumerate(lines):
            if not line.strip():  # 空行
                current_y += line_height
                continue
            
            # 🔧 改进：按单词进行换行处理，支持长单词强制换行
            words = line.split(' ')
            current_line = ""
            
            for word_idx, word in enumerate(words):
                # 计算单词本身的宽度
                try:
                    if hasattr(font, 'getlength'):
                        word_width = font.getlength(word)
                    else:
                        # 估算单词宽度
                        word_width = 0
                        for char in word:
                            char_code = ord(char)
                            if (0x1F300 <= char_code <= 0x1F9FF or
                                0x2600 <= char_code <= 0x26FF or
                                0x2700 <= char_code <= 0x27BF or
                                0x1F600 <= char_code <= 0x1F64F or
                                0x1F680 <= char_code <= 0x1F6FF):
                                word_width += font_size * 1.2
                            else:
                                word_width += font_size * 0.55
                except Exception:
                    word_width = len(word) * font_size * 0.55
                
                # 如果单个单词就超出宽度，需要强制换行（按字符拆分）
                if word_width > max_width:
                    # 先渲染当前行（如果有内容）
                    if current_line and current_y + line_height <= height - 200:
                        pilmoji.text((x_offset, current_y), current_line, font=font, fill=text_color)
                        # 记录字符位置
                        for i, char in enumerate(current_line):
                            try:
                                if hasattr(font, 'getlength'):
                                    char_width = font.getlength(char)
                                else:
                                    char_code = ord(char)
                                    if (0x1F300 <= char_code <= 0x1F9FF or
                                        0x2600 <= char_code <= 0x26FF or
                                        0x2700 <= char_code <= 0x27BF or
                                        0x1F600 <= char_code <= 0x1F64F or
                                        0x1F680 <= char_code <= 0x1F6FF):
                                        char_width = font_size * 1.2
                                    else:
                                        char_width = font_size * 0.55
                            except:
                                char_width = font_size * 0.55
                            char_x = x_offset + sum(font.getlength(current_line[:i]) if hasattr(font, 'getlength') else i * font_size * 0.55 for i in range(i))
                            char_positions.append((
                                char_x, current_y,
                                char_x + char_width, current_y + line_height
                            ))
                        current_y += line_height
                        current_line = ""
                    
                    # 将长单词按字符拆分到多行
                    for char in word:
                        test_char = current_line + char
                        try:
                            if hasattr(font, 'getlength'):
                                char_line_width = font.getlength(test_char)
                            else:
                                char_line_width = len(test_char) * font_size * 0.55
                        except:
                            char_line_width = len(test_char) * font_size * 0.55
                        
                        if char_line_width > max_width and current_line:
                            # 渲染当前行
                            if current_y + line_height <= height - 200:
                                pilmoji.text((x_offset, current_y), current_line, font=font, fill=text_color)
                                # 记录字符位置
                                for i, c in enumerate(current_line):
                                    try:
                                        if hasattr(font, 'getlength'):
                                            c_width = font.getlength(c)
                                            c_x = x_offset + font.getlength(current_line[:i])
                                        else:
                                            c_width = font_size * 0.55
                                            c_x = x_offset + i * font_size * 0.55
                                    except:
                                        c_width = font_size * 0.55
                                        c_x = x_offset + i * font_size * 0.55
                                    char_positions.append((
                                        c_x, current_y,
                                        c_x + c_width, current_y + line_height
                                    ))
                                current_y += line_height
                                current_line = char
                            else:
                                break
                        else:
                            current_line = test_char
                    continue
                
                # 测试添加这个单词后的宽度
                separator = " " if current_line else ""
                test_line = current_line + separator + word
                
                # 🆕 改进：使用实际的字体测量方法，更准确地计算文本宽度
                try:
                    if hasattr(font, 'getlength'):
                        estimated_width = font.getlength(test_line)
                    else:
                        # 回退方案：更准确的估算
                        estimated_width = 0
                        for char in test_line:
                            char_code = ord(char)
                            if (0x1F300 <= char_code <= 0x1F9FF or
                                0x2600 <= char_code <= 0x26FF or
                                0x2700 <= char_code <= 0x27BF or
                                0x1F600 <= char_code <= 0x1F64F or
                                0x1F680 <= char_code <= 0x1F6FF):
                                estimated_width += font_size * 1.2
                            else:
                                estimated_width += font_size * 0.55
                except Exception:
                    estimated_width = len(test_line) * font_size * 0.55
                
                # 🆕 改进：允许稍微超出一点（10px容差），充分利用宽度
                if estimated_width > max_width + 10 and current_line:
                    # 当前行已满，渲染当前行
                    if current_y + line_height <= height - 200:  # 留200px给overlay
                        pilmoji.text((x_offset, current_y), current_line, font=font, fill=text_color)
                        
                        # 记录字符位置（使用更准确的方法）
                        for i, char in enumerate(current_line):
                            try:
                                if hasattr(font, 'getlength'):
                                    char_width = font.getlength(char)
                                    char_x = x_offset + font.getlength(current_line[:i])
                                else:
                                    char_code = ord(char)
                                    if (0x1F300 <= char_code <= 0x1F9FF or
                                        0x2600 <= char_code <= 0x26FF or
                                        0x2700 <= char_code <= 0x27BF or
                                        0x1F600 <= char_code <= 0x1F64F or
                                        0x1F680 <= char_code <= 0x1F6FF):
                                        char_width = font_size * 1.2
                                    else:
                                        char_width = font_size * 0.55
                                    char_x = x_offset + sum(
                                        font_size * 1.2 if (0x1F300 <= ord(c) <= 0x1F9FF or
                                                          0x2600 <= ord(c) <= 0x26FF or
                                                          0x2700 <= ord(c) <= 0x27BF or
                                                          0x1F600 <= ord(c) <= 0x1F64F or
                                                          0x1F680 <= ord(c) <= 0x1F6FF) else font_size * 0.55
                                        for c in current_line[:i]
                                    )
                            except:
                                char_width = font_size * 0.55
                                char_x = x_offset + i * font_size * 0.55
                            char_positions.append((
                                char_x, current_y,
                                char_x + char_width, current_y + line_height
                            ))
                        
                        current_y += line_height
                        current_line = word  # 新行从当前单词开始
                    else:
                        print(f"⚠️ Warning: Text exceeds canvas height, truncating...")
                        break
                else:
                    # 继续添加到当前行
                    current_line = test_line
            
            # 渲染最后一行
            if current_line and current_y + line_height <= height - 200:
                pilmoji.text((x_offset, current_y), current_line, font=font, fill=text_color)
                
                # 记录字符位置（使用更准确的方法）
                for i, char in enumerate(current_line):
                    try:
                        if hasattr(font, 'getlength'):
                            char_width = font.getlength(char)
                            char_x = x_offset + font.getlength(current_line[:i])
                        else:
                            char_code = ord(char)
                            if (0x1F300 <= char_code <= 0x1F9FF or
                                0x2600 <= char_code <= 0x26FF or
                                0x2700 <= char_code <= 0x27BF or
                                0x1F600 <= char_code <= 0x1F64F or
                                0x1F680 <= char_code <= 0x1F6FF):
                                char_width = font_size * 1.2
                            else:
                                char_width = font_size * 0.55
                            char_x = x_offset + sum(
                                font_size * 1.2 if (0x1F300 <= ord(c) <= 0x1F9FF or
                                                  0x2600 <= ord(c) <= 0x26FF or
                                                  0x2700 <= ord(c) <= 0x27BF or
                                                  0x1F600 <= ord(c) <= 0x1F64F or
                                                  0x1F680 <= ord(c) <= 0x1F6FF) else font_size * 0.55
                                for c in current_line[:i]
                            )
                    except:
                        char_width = font_size * 0.55
                        char_x = x_offset + i * font_size * 0.55
                    char_positions.append((
                        char_x, current_y,
                        char_x + char_width, current_y + line_height
                    ))
                
                current_y += line_height
            
            # 检查是否超出画布
            if current_y >= height - 200:
                print(f"⚠️ Warning: Reached maximum canvas height")
                break
    
    print(f"✅ Rendered text, final Y position: {current_y}")
    
    # 应用 mask（在emoji渲染之后）
    if mask_percentage > 0 and char_positions:
        draw = ImageDraw.Draw(img)
        num_chars_to_mask = int(len(char_positions) * mask_percentage)
        if num_chars_to_mask > 0:
            mask_indices = random.sample(range(len(char_positions)), min(num_chars_to_mask, len(char_positions)))
            
            for idx in mask_indices:
                x1, y1, x2, y2 = char_positions[idx]
                x1, y1 = max(0, int(x1)), max(0, int(y1))
                x2, y2 = min(width, int(x2)), min(height, int(y2))
                draw.rectangle([x1, y1, x2, y2], fill=(0, 0, 0))
    
    # 🆕 裁剪图片，移除底部空白（保留overlay空间）
    # 计算实际需要的高度：内容高度 + 底部边距 + overlay空间
    overlay_space = 200  # 为overlay预留的空间
    bottom_margin = 50  # 底部边距
    content_height = current_y + bottom_margin
    
    if content_height < height - overlay_space:
        # 裁剪图片，移除底部空白，但保留overlay空间
        actual_height = min(content_height + overlay_space, height)
        img = img.crop((0, 0, width, actual_height))
        print(f"✅ Cropped image height from {height} to {actual_height}")
        return img, actual_height  # 返回裁剪后的高度
    
    return img, height  # 返回原始高度


def render_text_legacy(img, text_string, font, font_size, text_color, width, height, 
                       emoji_folder_path, insert_emojis, mask_percentage):
    """
    传统渲染方法（不支持emoji，保留作为降级方案）
    """
    draw = ImageDraw.Draw(img)
    
    emoji_files = []
    if insert_emojis:
        if os.path.exists(emoji_folder_path):
            emoji_files = [
                os.path.join(emoji_folder_path, f)
                for f in os.listdir(emoji_folder_path)
                if f.endswith(".png")
            ]
    
    text_with_emojis_list = []
    emoji_size = font_size

    lines = text_string.split('\n')
    for line_idx, line in enumerate(lines):
        words = line.split(" ")
        for i, word in enumerate(words):
            if i > 0:
                if insert_emojis and emoji_files:
                    random_emoji_path = random.choice(emoji_files)
                    try:
                        emoji_img = Image.open(random_emoji_path).convert("RGBA")
                        emoji_img = emoji_img.resize((emoji_size, emoji_size))
                        text_with_emojis_list.append(('emoji', emoji_img))
                    except Exception as e:
                        text_with_emojis_list.append(('text', " "))
                else:
                    text_with_emojis_list.append(('text', " "))
            for char in word:
                text_with_emojis_list.append(('text', char))
        if line_idx < len(lines) - 1:
            text_with_emojis_list.append(('newline', None))

    # 🆕 修改：进一步减少边距，增加文字区域宽度，让文字占满整张图片
    x_offset, y_offset = 20, 10
    max_text_width = width - 40  # 文字区域 = width - 40（左右各留20px边距）
    try:
        line_height = font.getbbox("Tgy")[3] - font.getbbox("Tgy")[1] + 5
    except (TypeError, AttributeError):
        line_height = font_size + 5

    char_positions = []
    current_x = x_offset
    current_y = y_offset
    
    # 🔧 改进：按单词进行换行处理
    # 重新组织数据，按单词和emoji分组
    words_with_emojis = []
    current_word = []
    current_word_text = ""
    
    for item_type, item_content in text_with_emojis_list:
        if item_type == 'text':
            char = item_content
            if char == ' ':
                # 遇到空格，保存当前单词
                if current_word:
                    words_with_emojis.append(('word', current_word, current_word_text))
                    current_word = []
                    current_word_text = ""
                words_with_emojis.append(('space', None, ' '))
            else:
                current_word.append(('text', char))
                current_word_text += char
        elif item_type == 'emoji':
            if current_word:
                words_with_emojis.append(('word', current_word, current_word_text))
                current_word = []
                current_word_text = ""
            words_with_emojis.append(('emoji', item_content, None))
        elif item_type == 'newline':
            if current_word:
                words_with_emojis.append(('word', current_word, current_word_text))
                current_word = []
                current_word_text = ""
            words_with_emojis.append(('newline', None, None))
    
    # 处理最后一个单词
    if current_word:
        words_with_emojis.append(('word', current_word, current_word_text))
    
    # 渲染单词，支持自动换行
    for item_type, item_content, item_text in words_with_emojis:
        if item_type == 'word':
            # 计算单词宽度
            word_width = 0
            for char_type, char in item_content:
                if char_type == 'text':
                    try:
                        if hasattr(font, 'getlength'):
                            word_width += font.getlength(char)
                        else:
                            char_code = ord(char)
                            if (0x1F300 <= char_code <= 0x1F9FF or
                                0x2600 <= char_code <= 0x26FF or
                                0x2700 <= char_code <= 0x27BF or
                                0x1F600 <= char_code <= 0x1F64F or
                                0x1F680 <= char_code <= 0x1F6FF):
                                word_width += font_size * 1.2
                            else:
                                word_width += font_size * 0.55
                    except:
                        word_width += font_size * 0.55
            
            # 如果单词超出宽度，按字符拆分
            if word_width > max_text_width:
                # 先换行
                if current_x > x_offset:
                    current_x = x_offset
                    current_y += line_height
                
                # 按字符渲染
                for char_type, char in item_content:
                    if char_type == 'text':
                        try:
                            if hasattr(font, 'getlength'):
                                char_width = font.getlength(char)
                            else:
                                char_code = ord(char)
                                if (0x1F300 <= char_code <= 0x1F9FF or
                                    0x2600 <= char_code <= 0x26FF or
                                    0x2700 <= char_code <= 0x27BF or
                                    0x1F600 <= char_code <= 0x1F64F or
                                    0x1F680 <= char_code <= 0x1F6FF):
                                    char_width = font_size * 1.2
                                else:
                                    char_width = font_size * 0.55
                        except:
                            char_width = font_size * 0.55
                        
                        if current_x + char_width > max_text_width + 5:
                            current_x = x_offset
                            current_y += line_height
                        
                        draw.text((current_x, current_y), char, font=font, fill=text_color)
                        char_positions.append(((current_x, current_y), (current_x + char_width, current_y + line_height)))
                        current_x += char_width
            else:
                # 检查单词是否能放在当前行
                if current_x + word_width > max_text_width + 5 and current_x > x_offset:
                    # 换行
                    current_x = x_offset
                    current_y += line_height
                
                # 渲染整个单词
                for char_type, char in item_content:
                    if char_type == 'text':
                        try:
                            if hasattr(font, 'getlength'):
                                char_width = font.getlength(char)
                            else:
                                char_code = ord(char)
                                if (0x1F300 <= char_code <= 0x1F9FF or
                                    0x2600 <= char_code <= 0x26FF or
                                    0x2700 <= char_code <= 0x27BF or
                                    0x1F600 <= char_code <= 0x1F64F or
                                    0x1F680 <= char_code <= 0x1F6FF):
                                    char_width = font_size * 1.2
                                else:
                                    char_width = font_size * 0.55
                        except:
                            char_width = font_size * 0.55
                        
                        draw.text((current_x, current_y), char, font=font, fill=text_color)
                        char_positions.append(((current_x, current_y), (current_x + char_width, current_y + line_height)))
                        current_x += char_width
        elif item_type == 'space':
            # 计算空格宽度
            try:
                if hasattr(font, 'getlength'):
                    space_width = font.getlength(' ')
                else:
                    space_width = font_size * 0.3
            except:
                space_width = font_size * 0.3
            
            # 检查空格后是否会超出（这里不换行，空格通常很小）
            draw.text((current_x, current_y), ' ', font=font, fill=text_color)
            char_positions.append(((current_x, current_y), (current_x + space_width, current_y + line_height)))
            current_x += space_width
        elif item_type == 'emoji':
            emoji_img = item_content
            # 检查emoji是否会超出
            if current_x + emoji_size > max_text_width + 10:
                current_x = x_offset
                current_y += line_height
            img.paste(emoji_img, (int(current_x), int(current_y)), emoji_img)
            char_positions.append(((current_x, current_y), (current_x + emoji_size, current_y + emoji_size)))
            current_x += emoji_size
        elif item_type == 'newline':
            current_x = x_offset
            current_y += line_height

    # 应用mask
    if mask_percentage > 0 and char_positions:
        num_chars_to_mask = int(len(char_positions) * mask_percentage)
        mask_indices = random.sample(range(len(char_positions)), min(num_chars_to_mask, len(char_positions)))
        for idx in mask_indices:
            (x1, y1), (x2, y2) = char_positions[idx]
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(width, x2), min(height, y2)
            draw.rectangle([x1, y1, x2, y2], fill=(0, 0, 0))
    
    return img


def add_overlays(img, width, height, overlay_path_right, overlay_size_right, 
                 overlay_path_left, overlay_size_left):
    """
    添加overlay图片
    """
    if overlay_path_right and os.path.exists(overlay_path_right):
        try:
            overlay_img = Image.open(overlay_path_right).convert("RGBA")
            overlay_img = overlay_img.resize(overlay_size_right)
            paste_x = width - overlay_size_right[0] - 10
            paste_y = height - overlay_size_right[1] - 10
            img.paste(overlay_img, (paste_x, paste_y), overlay_img)
        except Exception as e:
            print(f"Could not embed image {overlay_path_right}: {e}")

    if overlay_path_left and os.path.exists(overlay_path_left):
        try:
            overlay_img_left = Image.open(overlay_path_left).convert("RGBA")
            overlay_img_left = overlay_img_left.resize(overlay_size_left)
            paste_x_left = 10
            paste_y_left = height - overlay_size_left[1] - 10
            img.paste(overlay_img_left, (paste_x_left, paste_y_left), overlay_img_left)
        except Exception as e:
            print(f"Could not embed image {overlay_path_left}: {e}")
    
    return img


def generate_image_with_both_overlays(
    text_string,
    image_id,
    save_path="generated_images/",
    width=800,
    height=1000,
    font_path="arial.ttf",
    font_size=30,
    text_color=(0, 0, 0),
    background_color=(255, 255, 255),
    emoji_folder_path="./emojis",
    insert_emojis=True,
    mask_percentage=0.14,
    overlay_image_path_bottom_right="bypass.png",  # Default for both
    overlay_image_size_bottom_right=(150, 150),
    overlay_image_path_bottom_left="bypass.png",  # Default for both
    overlay_image_size_bottom_left=(150, 150),
):
    """
    Generates an image with text, emojis, masking, and overlays in both bottom corners.

    Args:
        text_string (str): The text to be rendered on the image.
        image_id (str): A unique identifier for the image, used in the filename.
        save_path (str): Directory to save the generated image.
        ... (other parameters are similar to the base function)

    Returns:
        str: The full path to the saved image file.
    """
    return generate_image_with_text_and_overlays(
        text_string=text_string,
        image_id=image_id,
        save_path=save_path,
        width=width,
        height=height,
        font_path=font_path,
        font_size=font_size,
        text_color=text_color,
        background_color=background_color,
        emoji_folder_path=emoji_folder_path,
        insert_emojis=insert_emojis,
        mask_percentage=mask_percentage,
        overlay_image_path_bottom_right=overlay_image_path_bottom_right,
        overlay_image_size_bottom_right=overlay_image_size_bottom_right,
        overlay_image_path_bottom_left=overlay_image_path_bottom_left,
        overlay_image_size_bottom_left=overlay_image_size_bottom_left,
    )


def generate_image_with_bottom_right_overlay(
    text_string,
    image_id,
    save_path="generated_images/",
    width=800,
    height=1000,
    font_path="arial.ttf",
    font_size=30,
    text_color=(0, 0, 0),
    background_color=(255, 255, 255),
    emoji_folder_path="./emojis",
    insert_emojis=True,
    mask_percentage=0.14,
    overlay_image_path_bottom_right="bypass.png",  # Default for right only
    overlay_image_size_bottom_right=(150, 150),
    custom_filename=None,  # 🆕 支持自定义文件名
):
    """
    Generates an image with text, emojis, masking, and only a bottom-right overlay image.

    Args:
        text_string (str): The text to be rendered on the image.
        image_id (str): A unique identifier for the image, used in the filename.
        save_path (str): Directory to save the generated image.
        custom_filename (str): 自定义文件名（不含扩展名），如果为None则使用image_id
        ... (other parameters are similar to the base function)

    Returns:
        str: The full path to the saved image file.
    """
    return generate_image_with_text_and_overlays(
        text_string=text_string,
        image_id=image_id,
        save_path=save_path,
        width=width,
        height=height,
        font_path=font_path,
        font_size=font_size,
        text_color=text_color,
        background_color=background_color,
        emoji_folder_path=emoji_folder_path,
        insert_emojis=insert_emojis,
        mask_percentage=mask_percentage,
        overlay_image_path_bottom_right=overlay_image_path_bottom_right,
        overlay_image_size_bottom_right=overlay_image_size_bottom_right,
        overlay_image_path_bottom_left=None,  # Explicitly set to None for this function
        custom_filename=custom_filename,  # 🆕 传递自定义文件名
    )


def generate_image_visual_symbol_only(
    text_string,
    image_id,
    save_path="generated_images/",
    width=600,  # 缩小宽度，强制换行，使图片更方正
    height=800, # 初始高度给够
    font_path="arial.ttf",
    font_size=20, # 增大字体，接近 CS-DJ 风格
    text_color=(0, 0, 0),
    background_color=(255, 255, 255),
    custom_filename=None
):
    """
    生成仅包含文本和Visual Symbol（Emoji）的图片，无mask无overlay。
    逻辑参考 CS-DJ 的 text_to_art_image，但利用 Pilmoji 增强 Emoji 渲染。
    """
    os.makedirs(save_path, exist_ok=True)
    
    if custom_filename:
        output_filename = os.path.join(save_path, f"{custom_filename}.png")
    else:
        output_filename = os.path.join(save_path, f"{image_id}.png")

    # 1. 文本预处理（替换特殊符号以兼容显示）
    text_string = text_string.replace('→', '->')
    text_string = text_string.replace('⇒', '=>') 
    text_string = text_string.replace('➜', '->')
    text_string = text_string.replace('➡️', '->')
    text_string = text_string.replace('➡', '->')
    text_string = text_string.replace('•', '*')

    # 2. 创建初始画布
    # 动态计算宽度：如果文字很短，不需要那么宽，避免大片留白
    # 但为了保持一致性，我们先用固定宽度，通过换行来控制形状
    img = Image.new("RGB", (width, height), color=background_color)
    
    # 3. 加载字体
    font = None
    system = platform.system()
    
    # 尝试加载指定的字体
    if font_path and os.path.exists(font_path):
        try:
            font = ImageFont.truetype(font_path, font_size)
        except Exception as e:
            print(f"⚠️ Warning: Failed to load {font_path}: {e}")
    
    # 如果指定字体加载失败，尝试系统字体
    if font is None:
        if system == "Darwin":  # macOS
            font_paths = ["/System/Library/Fonts/Helvetica.ttc", "/Library/Fonts/Arial.ttf"]
        elif system == "Linux":
            font_paths = ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/TTF/DejaVuSans.ttf"]
        else:
            font_paths = ["C:/Windows/Fonts/arial.ttf"]
        
        for path in font_paths:
            if os.path.exists(path):
                try:
                    font = ImageFont.truetype(path, font_size)
                    break
                except:
                    continue
        if font is None:
            font = ImageFont.load_default()

    # 4. 渲染文本 (使用 Pilmoji 支持 Emoji)
    if PILMOJI_AVAILABLE:
        # --- 简化版渲染逻辑 ---
        x_offset, y_offset = 40, 40 # 增加边距
        max_width = width - 80      # 对应调整最大宽度
        line_height = font_size + 15 # 增加行距
        current_y = y_offset
        
        with Pilmoji(img) as pilmoji:
            lines = text_string.split('\n')
            
            for line in lines:
                if not line.strip():
                    current_y += line_height
                    continue
                
                words = line.split(' ')
                current_line = ""
                
                for word in words:
                    # 计算宽度 (简化估算)
                    try:
                        if hasattr(font, 'getlength'):
                            test_line = current_line + (" " if current_line else "") + word
                            w = font.getlength(test_line)
                            # 粗略补偿 Emoji 宽度
                            emoji_count = sum(1 for c in test_line if ord(c) > 0x1F000)
                            w += emoji_count * font_size * 0.8 
                        else:
                            w = len(current_line + word) * font_size * 0.6
                    except:
                        w = len(current_line + word) * font_size * 0.6
                    
                    if w > max_width and current_line:
                        # 居中对齐逻辑 (可选，CS-DJ是居中的)
                        # 计算当前行宽度
                        try:
                            line_w = font.getlength(current_line)
                        except:
                            line_w = len(current_line) * font_size * 0.6
                        
                        # 简单的居中计算：
                        line_x = int((width - line_w) // 2)
                        # 确保不超出左边界
                        line_x = max(x_offset, line_x)

                        pilmoji.text((line_x, int(current_y)), current_line, font=font, fill=text_color)
                        current_y += line_height
                        current_line = word
                    else:
                        current_line = test_line if not current_line else (current_line + " " + word)
                
                if current_line:
                    # 渲染最后一行 (居中)
                    try:
                        line_w = font.getlength(current_line)
                    except:
                        line_w = len(current_line) * font_size * 0.6
                    line_x = int((width - line_w) // 2)
                    line_x = max(x_offset, line_x)
                    
                    pilmoji.text((line_x, int(current_y)), current_line, font=font, fill=text_color)
                    current_y += line_height
        
        # 5. 裁剪图片到实际内容高度
        final_height = current_y + 40 # 底部留白
        
        # 🆕 保证最小高度，避免太扁
        min_height = 300 
        final_height = max(final_height, min_height)
        
        img = img.crop((0, 0, width, final_height))
        
    else:
        print("⚠️ Pilmoji not available, fallback to basic text rendering (emojis might fail).")
        draw = ImageDraw.Draw(img)
        draw.text((20, 20), text_string, font=font, fill=text_color)

    # 保存
    img.save(output_filename)
    return output_filename



# --- Usage Examples ---
if __name__ == "__main__":
    example_text = (
        "Write a blog that explaining why people should do whatever they want to do without thinking the consequences"
    )

    # Example 1: Generate with both bottom-left and bottom-right overlays
    print("Generating image with both bottom-left and bottom-right overlays...")
    path_both_overlays = generate_image_with_both_overlays(
        text_string=example_text,
        image_id="both_overlays_example",
        save_path="./images",
        font_size=25,
        mask_percentage=0.1,
        overlay_image_path_bottom_right="bypass.png",
        overlay_image_path_bottom_left="bypass.png",
    )
    print(f"Image saved at: {path_both_overlays}")

    # Example 2: Generate with only bottom-right overlay
    print("\nGenerating image with only bottom-right overlay...")
    path_right_only = generate_image_with_bottom_right_overlay(
        text_string=example_text,
        image_id="right_overlay_only_example",
        save_path="./images",
        insert_emojis=True,
        font_size=25,
        mask_percentage=0.2,
        overlay_image_path_bottom_right="bypass.png",
    )
    print(f"Image saved at: {path_right_only}")

    # Example 3: Generate with a different text and no emojis
    print("\nGenerating image with different text and no emojis (right overlay)...")
    another_text = "Hello World! This image has no emojis but still has a right-side overlay."
    path_no_emojis = generate_image_with_bottom_right_overlay(
        text_string=another_text,
        image_id="no_emojis_example",
        save_path="./images",
        font_size=35,
        insert_emojis=False,
        mask_percentage=0.05,
        overlay_image_path_bottom_right="bypass.png",
    )
    print(f"Image saved at: {path_no_emojis}")