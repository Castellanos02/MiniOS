from setuptools import setup, find_packages

setup(
    name="neuromorphic_assistant",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.20.0",
        "lava-nc>=0.5.0",
    ],
    python_requires=">=3.8",
    description="Neuromorphic assistant using Lava SNNs",
    author="Your Name",
)
