# -*- coding: utf-8 -*-
"""
WebResearcher - An Iterative Deep-Research Agent
"""
import os
import re
from setuptools import setup, find_packages

# Read version from __init__.py
def get_version():
    init_file = os.path.join(os.path.dirname(__file__), 'webresearcher', '__init__.py')
    with open(init_file, 'r', encoding='utf-8') as f:
        content = f.read()
        match = re.search(r"__version__\s*=\s*['\"]([^'\"]+)['\"]", content)
        if match:
            return match.group(1)
    return '0.1.0'

# Read long description from README
def get_long_description():
    readme_file = os.path.join(os.path.dirname(__file__), 'README.md')
    with open(readme_file, 'r', encoding='utf-8') as f:
        return f.read()

# Read requirements
def get_requirements():
    req_file = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    with open(req_file, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='webresearcher',
    version=get_version(),
    author='XuMing',
    author_email='xuming624@qq.com',
    description='An Iterative Deep-Research Agent with unbounded reasoning capability',
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    url='https://github.com/shibing624/WebResearcher',
    project_urls={
        'Bug Reports': 'https://github.com/shibing624/WebResearcher/issues',
        'Source': 'https://github.com/shibing624/WebResearcher',
        'Documentation': 'https://github.com/shibing624/WebResearcher#readme',
    },
    packages=find_packages(exclude=['tests', 'tests.*', 'examples', 'examples.*', 'docs', 'docs.*']),
    package_data={
        'webresearcher': ['*.txt', '*.md'],
    },
    install_requires=get_requirements(),
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='research agent ai llm iterative-research deep-research web-research',
    entry_points={
        'console_scripts': [
            'webresearcher=webresearcher.cli:main',
        ],
    },
    license='Apache License 2.0',
    zip_safe=False,
)

