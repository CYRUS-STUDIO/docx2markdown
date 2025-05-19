import os
from docx2markdown.docx_to_markdown_converter import docx_to_markdown

# docx 文件路径
docx = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'FART 主动调用组件设计和源码分析.docx')

# markdown 文件输出路径
output = os.path.join(os.path.dirname(os.path.abspath(__file__)), '测试.md')

# 开始转换
docx_to_markdown(docx, output)
