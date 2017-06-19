from setuptools import setup

setup(
    name="linotype",
    version="0.1",
    description="Automatically format help messages.",
    url="https://github.com/lostatc/linotype",
    author="Garrett Powell",
    author_email="garrett@gpowell.net",
    license="GPLv3",
    install_requires=["Sphinx"],
    python_requires=">=3.5",
    packages=["linotype"])
