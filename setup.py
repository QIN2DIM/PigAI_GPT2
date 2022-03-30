from os import path as os_path

from setuptools import setup, find_packages

import pigai

this_directory = os_path.abspath(os_path.dirname(__file__))
setup(
    name="pigai-gpt2",
    version=pigai.__version__,
    keywords=["pigai", "gpt2"],
    packages=find_packages(include=["pigai", "LICENSE", "pigai.*"]),
    url="https://github.com/QIN2DIM/PigAI_GPT2",
    license="GNU General Public License v3.0",
    author="QIN2DIM",
    author_email="qinse.top@foxmail.com",
    description="批改网写作助手，根据配置自动生成并提交英语作文。",
    long_description=open(
        os_path.join(this_directory, "README.md"), encoding="utf8"
    ).read(),
    long_description_content_type="text/markdown",
    install_requires=[
        "pyyaml~=6.0",
        "selenium~=4.1.0",
        "loguru~=0.6.0",
        "requests~=2.27.1",
        "webdriver_manager>=3.5.2",
    ],
    python_requires=">=3.7",
    classifiers=[
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
    ],
)
