import os

from docx_parser import DocxParser, Paragraph, Table


class DocxToMarkdownConverter:
    def __init__(self, docx_file):
        self.docx_file = docx_file
        self.in_code_block = False  # 用于追踪是否在代码块中
        self.code_block_content = ""  # 存储代码块的内容

    def _parse_text_with_hyperlink(self, paragraph):
        """
        如果文本中有超链接，转换为 Markdown 超链接格式
        """
        if paragraph.hyperlink:
            # 转换为 Markdown 超链接格式
            return paragraph.text.replace(paragraph.hyperlink.text, f"[{paragraph.hyperlink.text}]({paragraph.hyperlink.url})")
        return paragraph.text

    def _generate_markdown_from_paragraph(self, parser, paragraph):
        """
        根据段落信息生成相应的 Markdown 格式。
        """
        text = self._parse_text_with_hyperlink(paragraph)  # 获取段落文本并处理文本中的超链接
        style = paragraph.style
        image = paragraph.image
        numbering = paragraph.numbering  # 假设已经在解析时获取了编号信息
        background = style.background  # 获取背景填充信息

        markdown_text = ""

        # 处理加粗、斜体、下划线
        if style.bold:
            text = f"**{text}**"
        if style.italic:
            text = f"*{text}*"
        if style.underline:
            text = f"_{text}_"

        # 检查是否是代码块（背景填充不为空）
        if background and background.get('fill') == 'DBDBDB':  # 可以根据需要修改背景色
            if not self.in_code_block:
                # 如果之前没有在代码块中，开始新的代码块
                self.in_code_block = True
                markdown_text += "```\n"  # 开始代码块

            # 将当前段落的文本添加到代码块内容中
            markdown_text += text
        else:
            if self.in_code_block:
                # 如果之前处于代码块中，结束代码块
                self.in_code_block = False
                markdown_text += "```\n"  # 结束代码块

            # 判断是否是列表项
            if numbering is not None:

                # {'bullet': None, 'ilvl': '0', 'lvl_text': '%1.', 'numId': '1', 'num_format': 'decimal'}

                num_format = numbering.get('num_format')
                ilvl = int(numbering.get('ilvl'))
                lvl_text = numbering.get('lvl_text')

                if num_format == 'bullet':
                    # 无序列表
                    markdown_text += f"- {text}\n"
                elif num_format in ['decimal', 'lowerRoman', 'lowerLetter']:
                    # 有序列表，使用 numId 和 ilvl 生成编号
                    if num_format == 'decimal':
                        # 有序列表的格式：1. 2. 3.
                        markdown_text += f"{lvl_text.replace('%1', str(ilvl + 1))} {text}\n"
                    elif num_format == 'lowerRoman':
                        roman_numerals = ['i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii', 'ix', 'x']
                        roman = roman_numerals[ilvl] if ilvl < len(roman_numerals) else str(ilvl + 1)
                        markdown_text += f"{roman}) {text}\n"
                    elif num_format == 'lowerLetter':
                        letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']
                        letter = letters[ilvl] if ilvl < len(letters) else chr(ord('a') + ilvl)
                        markdown_text += f"{letter}) {text}\n"

            else:
                # 根据标题级别生成 Markdown
                if style.fonts.get("default", None):
                    try:
                        heading_level = int(style.fonts["default"])
                        if 1 <= heading_level <= 6:  # 1-6 级标题有效
                            markdown_text += f"{'#' * heading_level} {text}\n"
                        else:
                            markdown_text += f"{text}\n"
                    except ValueError:
                        markdown_text += f"{text}\n"  # 如果无法解析为数字，默认处理为普通文本
                else:
                    # 普通文本
                    markdown_text += f"{text}\n"

        # 处理图片
        if image:

            image_filename = image['file']

            # 调用方法获取图片的 Base64 编码
            image_base64 = parser.get_image_base64(image['file'])
            if image_base64:

                # 获取图片的文件扩展名
                extension = os.path.splitext(image_filename)[1].lower()

                # 根据文件扩展名设置 MIME 类型
                if extension == '.jpg' or extension == '.jpeg':
                    mime_type = 'image/jpeg'
                elif extension == '.png':
                    mime_type = 'image/png'
                elif extension == '.gif':
                    mime_type = 'image/gif'
                else:
                    mime_type = 'image/png'  # 默认使用 PNG

                # Markdown 格式的图片标签
                markdown_text += f"\n![{image_filename}](data:{mime_type};base64,{image_base64})"

        return markdown_text

    def _generate_markdown_from_table(self, table):
        """
        将 Table 对象转换为 Markdown 格式的表格。
        :param table: Table 对象，包含表格的数据
        :return: Markdown 格式的表格字符串
        """
        markdown_table = []

        # 如果表格没有行，直接返回空字符串
        if not table.rows:
            return ""

        # 表头行
        header_row = table.rows[0]
        markdown_table.append("| " + " | ".join(header_row) + " |")

        # 分隔符行（Markdown 表头和表体的分隔线）
        markdown_table.append("|" + " | ".join(["---"] * len(header_row)) + "|")

        # 表格内容行
        for row in table.rows[1:]:
            markdown_table.append("| " + " | ".join(row) + " |")

        # 返回转换后的 Markdown 表格内容
        return "\n".join(markdown_table)

    def convert(self):
        """
        转换整个 docx 文件的内容为 markdown 格式。
        """
        parser = DocxParser(self.docx_file)
        document = parser.parse()
        markdown_content = ""

        for element in document['elements']:
            if isinstance(element, Paragraph):
                markdown_content += self._generate_markdown_from_paragraph(parser, element) + "\n"
            elif isinstance(element, Table):
                markdown_content += self._generate_markdown_from_table(element) + "\n"

        # 如果文件结尾处仍然有未关闭的代码块，关闭它
        if self.in_code_block:
            markdown_content += "```\n"

        return markdown_content


def docx_to_markdown(docx_file, output=None):
    converter = DocxToMarkdownConverter(docx_file)
    markdown_content = converter.convert()

    # 输出生成的 Markdown 内容
    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        print(f"Markdown 文件已生成：{output}")

    return markdown_content
