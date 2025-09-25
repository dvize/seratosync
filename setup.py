"""
Setup configuration for seratosync package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="seratosync",
    version="1.0.0",
    author="Serato Crate Sync",
    description="Mirror folder hierarchy into Serato crates and detect new tracks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: System :: Filesystems",
    ],
    python_requires=">=3.8",
    install_requires=[
        # No external dependencies required for CLI - uses only Python standard library
    ],
    extras_require={
        "gui": [
            "customtkinter>=5.2.0",  # Modern GUI framework
            "pillow>=9.0.0",         # Image support for GUI
        ],
    },
    entry_points={
        "console_scripts": [
            "seratosync=seratosync.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
