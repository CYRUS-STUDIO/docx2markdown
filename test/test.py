import os
from docx2markdown.docx_to_markdown_converter import docx_to_markdown

# docx 文件路径
docx = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'FART 自动化脱壳框架简介与脱壳点的选择.docx')

# markdown 文件输出路径
output = os.path.join(os.path.dirname(os.path.abspath(__file__)), '测试.md')

# 开始转换
docx_to_markdown(docx, output)
