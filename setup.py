from setuptools import setup, find_packages

setup(
    name='docx2markdown',  # 包的名称
    version='0.1.0',  # 包的版本
    packages=find_packages(),  # 自动发现包
    install_requires=[  # 列出依赖包
    ],
    description='convert docx to markdown',  # 简短描述
    long_description=open('README.md', encoding='utf-8').read(),  # 长描述，通常从 README.md 获取
    long_description_content_type='text/markdown',  # 描述格式
    author='Cyrus Lin',
    author_email='linchaolong.dev@gmail.com',
    url='https://github.com/CYRUS-STUDIO/docx2markdown',  # 项目的主页或仓库链接
    classifiers=[  # 分类标签（可选）
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',  # Python 版本要求
)
