from setuptools import setup, find_packages

setup(
    packages=find_packages(exclude=["data", "data.*", "alembic", "alembic.*", "tests", "tests.*"]),
)
