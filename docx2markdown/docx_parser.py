import zipfile
import xml.etree.ElementTree as ET
import os
import base64


# 定义样式对象，用于存储段落的样式信息
class Style:
    def __init__(self):
        self.fonts = {}  # 用字典存储字体信息
        self.size = None
        self.bold = False
        self.italic = False
        self.underline = False
        self.alignment = None  # left, center, right
        self.spacing_before = None
        self.spacing_after = None
        self.background = None  # 背景填充信息

    def __str__(self):
        fonts_str = ', '.join(f"{k}: {v}" for k, v in self.fonts.items())
        background_str = f"Fill: {self.background['fill']}, Color: {self.background['color']}" if self.background else "None"
        return f"Fonts: {fonts_str}, Size: {self.size}, Bold: {self.bold}, " \
               f"Italic: {self.italic}, Underline: {self.underline}, " \
               f"Alignment: {self.alignment}, SpacingBefore: {self.spacing_before}, " \
               f"SpacingAfter: {self.spacing_after}, Background: {background_str}"


# 定义段落对象，用于存储段落文本、样式、图片信息和编号
class Paragraph:
    def __init__(self, text, style=None, image=None, numbering=None, hyperlink=None):
        self.text = text
        self.style = style or Style()
        self.image = image  # 保存图片信息
        self.numbering = numbering  # 保存编号信息
        self.hyperlink = hyperlink  # 超链接

    def __str__(self):
        image_str = f"Image: {self.image}" if self.image else ""
        numbering_str = f"Numbering: {self.numbering}" if self.numbering else ""
        hyperlink = f"Hyperlink: {self.hyperlink}" if self.hyperlink else ""
        return f"Text: {self.text}, Style: {self.style}, {image_str}, {numbering_str}, {hyperlink}"


class Hyperlink:
    def __init__(self, id, text, url):
        self.id = id  # 超链接 ID
        self.text = text  # 超链接文本
        self.url = url  # 超链接的真实 URL

    def __repr__(self):
        return f"Hyperlink(id={self.id}, text={self.text}, url={self.url})"


class Table:
    def __init__(self, rows):
        """
        初始化 Table 对象
        :param rows: 表格的所有行，每行是一个列表，包含单元格的文本内容
        """
        self.rows = rows

    def __repr__(self):
        """
        定义如何显示 Table 对象的字符串表示
        :return: 表格的字符串表示
        """
        return f"Table({len(self.rows)} rows)"


class DocxParser:
    def __init__(self, file_path):
        self.file_path = file_path
        self.document_xml = None
        self.rels_xml = None
        self.numbering_xml = None

    def _extract_document_xml(self):
        """
        解压 docx 文件，获取 document.xml 的内容。
        """
        try:
            with zipfile.ZipFile(self.file_path, 'r') as docx_zip:
                # 查找 document.xml 文件
                if 'word/document.xml' in docx_zip.namelist():
                    with docx_zip.open('word/document.xml') as document_file:
                        self.document_xml = document_file.read()
                else:
                    raise ValueError("document.xml 文件未找到")

                # 查找 document.xml.rels 文件
                if 'word/_rels/document.xml.rels' in docx_zip.namelist():
                    with docx_zip.open('word/_rels/document.xml.rels') as rels_file:
                        self.rels_xml = rels_file.read()
                else:
                    raise ValueError("document.xml.rels 文件未找到")

                # 查找 numbering.xml 文件
                if 'word/numbering.xml' in docx_zip.namelist():
                    with docx_zip.open('word/numbering.xml') as rels_file:
                        self.numbering_xml = rels_file.read()
                else:
                    raise ValueError("word/numbering.xml 文件未找到")

        except zipfile.BadZipFile:
            raise ValueError(f"{self.file_path} 不是有效的 .docx 文件")

    def _parse_hyperlink(self, paragraph_element, ns):
        """
        从段落中解析超链接信息。
        """
        hyperlink = None
        hyperlink_element = paragraph_element.find('.//w:hyperlink', ns)
        if hyperlink_element is not None:
            r_id = hyperlink_element.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
            # 获取超链接文本
            texts = [node.text for node in hyperlink_element.findall('.//w:t', ns) if node.text]
            hyperlink_text = ''.join(texts)

            # 查找 .rels 文件中的超链接真实 URL
            if r_id:
                url = self._get_hyperlink_url(r_id)
                if url:
                    hyperlink = Hyperlink(r_id, hyperlink_text, url)
        return hyperlink

    def _get_hyperlink_url(self, r_id):
        """
        从 document.xml.rels 文件中获取 r_id 对应的真实 URL。
        """
        url = None
        if self.rels_xml is not None:
            rels_tree = ET.ElementTree(ET.fromstring(self.rels_xml))
            rels_root = rels_tree.getroot()

            namespaces = {
                'rels': 'http://schemas.openxmlformats.org/package/2006/relationships'
            }

            # 查找与超链接相关的关系
            for rel in rels_root.findall('rels:Relationship', namespaces):
                if rel.attrib.get('Id') == r_id:
                    url = rel.attrib.get('Target')
                    break
        return url

    def _parse_style(self, paragraph_element, ns):
        """
        从段落中解析样式信息。
        """
        style = Style()

        # 解析段落样式
        pStyle = paragraph_element.find('.//w:pStyle', ns)
        if pStyle is not None:
            style.fonts["default"] = pStyle.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')

        # 解析字体和大小
        rPr = paragraph_element.find('.//w:rPr', ns)
        if rPr is not None:
            # 解析字体
            rFonts = rPr.find('.//w:rFonts', ns)
            if rFonts is not None:
                style.fonts["ascii"] = rFonts.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}ascii')
                style.fonts["hAnsi"] = rFonts.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}hAnsi')
                style.fonts["cs"] = rFonts.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}cs')
                style.fonts["eastAsia"] = rFonts.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}eastAsia')

            bold = rPr.find('.//w:b', ns)
            italic = rPr.find('.//w:i', ns)
            underline = rPr.find('.//w:u', ns)
            if bold is not None:
                style.bold = True
            if italic is not None:
                style.italic = True
            if underline is not None:
                style.underline = True

            # 解析字体大小
            sz = rPr.find('.//w:sz', ns)
            if sz is not None:
                style.size = sz.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')

        # 解析段落对齐和间距
        pAlignment = paragraph_element.find('.//w:jc', ns)
        if pAlignment is not None:
            style.alignment = pAlignment.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')

        spacing = paragraph_element.find('.//w:spacing', ns)
        if spacing is not None:
            style.spacing_before = spacing.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}before')
            style.spacing_after = spacing.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}after')

        # 解析背景填充信息（<w:shd>）
        shd = paragraph_element.find('.//w:shd', ns)
        if shd is not None:
            style.background = {
                'val': shd.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val'),
                'color': shd.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}color'),
                'fill': shd.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}fill')
            }

        return style

    def _parse_image(self, paragraph_element, ns):
        """
        从段落中解析图片信息。
        """
        image = None
        drawing = paragraph_element.find('.//w:drawing', ns)
        if drawing is not None:
            # 查找 <wp:docPr> 元素，提取图像信息
            docPr = drawing.find('.//wp:docPr', ns)
            if docPr is not None:
                image = {
                    'id': docPr.get('id'),
                    'name': docPr.get('name'),
                    'descr': docPr.get('descr'),
                }

                # 查找 <a:blip> 标签中的 embed 属性
                blip = drawing.find('.//a:blip', ns)
                if blip is not None:
                    r_id = blip.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                    if r_id:
                        image['rId'] = r_id
                        # 使用 rId 查找对应的图片路径
                        image['file'] = f'word/{self._get_hyperlink_url(r_id)}'

        return image

    def _parse_numbering(self, paragraph_element, ns):
        """
        从段落中解析编号信息。
        """
        numbering = None
        numPr = paragraph_element.find('.//w:numPr', ns)
        if numPr is not None:
            ilvl = numPr.find('.//w:ilvl', ns)
            numId = numPr.find('.//w:numId', ns)
            if ilvl is not None and numId is not None:
                numbering = {
                    'ilvl': ilvl.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val'),
                    'numId': numId.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val'),
                }
                numbering_info = self._get_numbering_info(numbering['numId'], numbering['ilvl'])
                numbering.update(numbering_info)

        return numbering

    def _get_numbering_info(self, numId, ilvl):
        """
        根据 numId 和 ilvl 从 numbering.xml 获取对应的 numbering 信息。

        :param numId: 段落中的 numId
        :param ilvl: 段落中的层级 ilvl
        :return: 对应的 numbering 信息（字典格式）
        """
        # 解析 XML
        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        tree = ET.ElementTree(ET.fromstring(self.numbering_xml))
        root = tree.getroot()

        # 查找 numId 对应的 num
        num = root.find(f'.//w:num[@w:numId="{numId}"]', ns)
        if num is None:
            raise ValueError(f"无法找到 numId={numId} 对应的编号配置")

        # 获取该 numId 对应的 abstractNumId
        abstract_num_id = num.find('.//w:abstractNumId', ns).get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')

        # 查找对应 abstractNumId 的 abstractNum 配置
        abstract_num = root.find(f'.//w:abstractNum[@w:abstractNumId="{abstract_num_id}"]', ns)
        if abstract_num is None:
            raise ValueError(f"无法找到 abstractNumId={abstract_num_id} 对应的列表配置")

        # 获取该层级的配置
        lvl = abstract_num.find(f'.//w:lvl[@w:ilvl="{ilvl}"]', ns)
        if lvl is None:
            raise ValueError(f"无法找到 ilvl={ilvl} 对应的层级配置")

        # 获取该层级的编号格式（numFmt）和编号文本格式（lvlText）
        num_format = lvl.find('.//w:numFmt', ns).get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
        lvl_text = lvl.find('.//w:lvlText', ns).get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')

        # 获取符号（仅对无序列表有效）
        bullet = None
        if num_format == 'bullet':
            bullet = lvl.find('.//w:rPr/w:rFonts', ns).get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}ascii', None)

        # 返回该层级的详细信息
        numbering_info = {
            'num_format': num_format,  # 编号格式（有序：decimal，无序：bullet）
            'lvl_text': lvl_text,  # 层级文本格式（如 "%1." 或 ""）
            'bullet': bullet  # 无序列表的符号（如果是无序列表）
        }

        return numbering_info

    def _parse_table(self, element, ns):
        """
        解析表格元素（<w:tbl>）并返回表格数据。
        :param element: <w:tbl> 元素
        :param ns: XML 命名空间
        :return: 解析后的表格数据（列表形式，每个元素表示表格的一行）
        """
        table_data = []

        if element.tag == '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tbl':
            # 查找表格的所有行 <w:tr>
            rows = element.findall('.//w:tr', ns)

            for row in rows:
                row_data = []

                # 查找每一行中的所有单元格 <w:tc>
                cells = row.findall('.//w:tc', ns)

                for cell in cells:
                    # 获取单元格中的所有文本内容
                    texts = [node.text for node in cell.findall('.//w:t', ns) if node.text]
                    cell_text = ''.join(texts)
                    row_data.append(cell_text)

                # 将解析的一行数据添加到表格数据中
                table_data.append(row_data)

        return table_data

    def parse(self):
        """
        解析 document.xml 内容并返回文档对象，包含段落和样式。
        """
        if self.document_xml is None:
            self._extract_document_xml()

        # 解析 XML 内容
        try:
            root = ET.fromstring(self.document_xml)
            ns = {
                'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
                'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
                'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
                'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
                'pic': 'http://schemas.openxmlformats.org/drawingml/2006/picture'
            }

            elements = []

            # 获取 <w:body> 节点
            body = root.find('.//w:body', ns)

            # 只迭代 <w:body> 下的直接子元素（不递归）
            for element in body.findall('*'):  # '*' 表示所有直接子元素

                # 处理段落 <w:p>
                if element.tag == '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p':

                    texts = [node.text for node in element.findall('.//w:t', ns) if node.text]
                    paragraph_text = ''.join(texts)
                    paragraph_style = self._parse_style(element, ns)
                    paragraph_image = self._parse_image(element, ns)
                    paragraph_numbering = self._parse_numbering(element, ns)
                    paragraph_hyperlink = self._parse_hyperlink(element, ns)

                    paragraph_obj = Paragraph(paragraph_text, paragraph_style, paragraph_image, paragraph_numbering, paragraph_hyperlink)
                    elements.append(paragraph_obj)

                # 处理表格 <w:tbl>
                elif element.tag == '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tbl':
                    table_data = self._parse_table(element, ns)
                    table_obj = Table(table_data)
                    elements.append(table_obj)

            return {'elements': elements}

        except ET.ParseError:
            raise ValueError("无法解析 document.xml 内容")

    def extract_media(self, output_folder):
        """
        从 .docx 文件中提取 media 文件夹中的所有图片并保存到指定文件夹
        """

        if not os.path.exists(output_folder):
            os.makedirs(output_folder)  # 如果输出文件夹不存在，创建它

        try:
            # 打开 docx 文件
            with zipfile.ZipFile(self.file_path, 'r') as docx_zip:
                # 获取 .docx 文件内的所有文件
                media_files = [name for name in docx_zip.namelist() if name.startswith('word/media/')]

                for media_file in media_files:
                    # 获取图片文件的内容
                    image_data = docx_zip.read(media_file)
                    # 获取文件名并设置保存路径
                    image_name = os.path.basename(media_file)
                    output_path = os.path.join(output_folder, image_name)

                    # 保存图片
                    with open(output_path, 'wb') as img_file:
                        img_file.write(image_data)
                    print(f"保存图片: {image_name} 到 {output_path}")
        except zipfile.BadZipFile:
            print(f"无法打开 {self.file_path}，请确保它是一个有效的 .docx 文件")

    def get_image_base64(self, image_path):
        """
        从 .docx 文件中提取指定的图片并将其转换为 Base64 编码。
        """
        try:
            with zipfile.ZipFile(self.file_path, 'r') as docx_zip:

                # 检查文件是否存在
                if image_path in docx_zip.namelist():
                    image_data = docx_zip.read(image_path)

                    # 将图片数据转换为 Base64 编码
                    base64_image = base64.b64encode(image_data).decode('utf-8')
                    return base64_image
                else:
                    print(f"图片 {image_path} 不存在于 .docx 文件中")
                    return None
        except zipfile.BadZipFile:
            print(f"无法打开 {self.file_path}，请确保它是一个有效的 .docx 文件")
            return None


# 使用示例
if __name__ == "__main__":
    docx_file = r"D:\hugo\document\使用 opt 优化 LLVM IR，定制 clang 实现函数名加密.docx"  # 替换为你的 docx 文件路径
    parser = DocxParser(docx_file)
    document = parser.parse()

    print("文档内容：")
    for i, paragraph in enumerate(document['paragraphs'], start=1):
        print(f"段落 {i}: {paragraph}")
