from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="cpulimiter",
    version="1.0.2",
    author="Ahmed Ashraf",
    author_email="your-email@example.com",
    description="A simple, lightweight Python library for Windows to limit the CPU usage of any running process",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Ahmed-Ashraf-dv/CPULimiter",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Systems Administration",
    ],
    python_requires=">=3.7",
    install_requires=[
        "psutil>=5.8.0",
        "pygetwindow>=0.0.9",
        "pywin32>=227",
    ],
    keywords="cpu limiter throttle process windows performance",
)

