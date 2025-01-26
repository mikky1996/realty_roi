from setuptools import setup, find_packages


setup(
    name="realty_roi",
    version="0.0.1",
    author="Mikhail Novichkov",
    author_email="nmi51253@gmail.co",
    description="Profitability estimator",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.7",
)
