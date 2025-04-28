import re
from setuptools import setup, find_packages

# Read version from __init__.py
with open("dexpaprika_sdk/__init__.py", "r") as f:
    version_match = re.search(r'__version__ = "(.*?)"', f.read())
    version = version_match.group(1) if version_match else "0.0.0"

setup(
    name="dexpaprika-sdk",
    version=version,
    description="Python SDK for the DexPaprika API",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="CoinPaprika",
    author_email="support@coinpaprika.com",
    url="https://github.com/coinpaprika/dexpaprika-sdk-python",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
        "pydantic>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.0.0",
            "twine>=4.0.0",
            "build>=0.10.0",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development",
        "Typing :: Typed",
    ],
    keywords=["dexpaprika", "crypto", "blockchain", "defi", "api", "sdk"],
) 