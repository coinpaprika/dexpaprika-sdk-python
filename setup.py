from setuptools import setup, find_packages

setup(
    name="dexpaprika-sdk",
    version="0.1.0",
    description="Python SDK for the DexPaprika API",
    author="CoinPaprika",
    author_email="support@coinpaprika.com",
    url="https://github.com/coinpaprika/dexpaprika-sdk-python",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
        "pydantic>=2.0.0",
    ],
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
    ],
) 