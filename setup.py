from setuptools import setup

setup(
    name="linotype",
    version="0.2.1",
    description="Automatically format help messages.",
    long_description="See GitHub page for more details.",
    url="https://github.com/lostatc/linotype",
    author="Garrett Powell",
    author_email="garrett@gpowell.net",
    license="GPLv3",
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Documentation"],
    install_requires=["sphinx"],
    python_requires=">=3.5",
    tests_require=["pytest"],
    extras_require={
        "Windows support": ["colorama"]},
    packages=["linotype"])
