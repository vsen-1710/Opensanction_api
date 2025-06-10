from setuptools import setup, find_packages

setup(
    name="opensancton",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "flask",
        "flask-cors",
        "requests",
        "redis",
        "neo4j",
        "python-dotenv",
        "fuzzywuzzy",
        "python-Levenshtein"  # Optional but recommended for better performance
    ],
    python_requires=">=3.9",
) 