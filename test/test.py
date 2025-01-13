import os
from docx2markdown.docx_to_markdown_converter import docx_to_markdown

# docx 文件路径
docx = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Android Dex VMP 动态加载加密指令流 .docx')

# markdown 文件输出路径
output = os.path.join(os.path.dirname(os.path.abspath(__file__)), '测试.md')

# 开始转换
docx_to_markdown(docx, output)
