from setuptools import setup

setup(
    name="linotype",
    version="0.1.0-3",
    description="Automatically format help messages.",
    long_descriptioin="See GitHub page for more details.",
    url="https://github.com/lostatc/linotype",
    author="Garrett Powell",
    author_email="garrett@gpowell.net",
    license="GPLv3",
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Software Development :: Documentation"],
    install_requires=[],
    python_requires=">=3.5",
    tests_require=["pytest"],
    packages=["linotype"])
