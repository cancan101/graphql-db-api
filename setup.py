import os
import sys
from pathlib import Path
from shutil import rmtree
from typing import List, Tuple

from setuptools import Command, find_packages, setup

# -----------------------------------------------------------------------------

DESCRIPTION = "Python DB-API and SQLAlchemy interface for GraphQL APIs."
VERSION = "0.0.1.dev5"

# -----------------------------------------------------------------------------

# read the contents of your README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()
long_description_content_type = "text/markdown; charset=UTF-8; variant=GFM"

dist_directory = (this_directory / "dist").absolute()

# -----------------------------------------------------------------------------


class BaseCommand(Command):
    user_options: List[Tuple[str, str, str]] = []

    @staticmethod
    def status(s: str) -> None:
        """Prints things in bold."""
        print("\033[1m{0}\033[0m".format(s))  # noqa: T201

    def system(self, command: str) -> None:
        os.system(command)  # noqa: S605

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass


class BuildCommand(BaseCommand):
    """Support setup.py building."""

    description = "Build the package."

    def run(self):
        try:
            self.status("Removing previous builds…")
            rmtree(dist_directory)
        except OSError:
            pass

        self.status("Building Source and Wheel (universal) distribution…")
        self.system("{0} -m build --sdist --wheel .".format(sys.executable))

        self.status("Checking wheel contents…")
        self.system("check-wheel-contents dist/*.whl")

        self.status("Running twine check…")
        self.system("{0} -m twine check dist/*".format(sys.executable))


class UploadTestCommand(BaseCommand):
    """Support uploading to test PyPI."""

    description = "Upload the package to the test PyPI."

    def run(self):
        self.status("Uploading the package to PyPi via Twine…")
        self.system(
            "twine upload --repository-url https://test.pypi.org/legacy/ dist/*"
        )


class UploadCommand(BaseCommand):
    """Support uploading to PyPI."""

    description = "Upload the package to PyPI."

    def run(self):
        self.status("Uploading the package to PyPi via Twine…")
        self.system("twine upload dist/*")

        self.status("Pushing git tags…")
        self.system("git tag v{0}".format(VERSION))
        self.system("git push --tags")


# -----------------------------------------------------------------------------

setup(
    name="sqlalchemy-graphqlapi",
    version=VERSION,
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type=long_description_content_type,
    author="Alex Rothberg",
    author_email="agrothberg@gmail.com",
    url="https://github.com/cancan101/graphql-db-api",
    packages=find_packages(exclude=("tests",)),
    entry_points={
        "sqlalchemy.dialects": [
            "graphql = graphqldb.dialect:APSWGraphQLDialect",
        ],
        "shillelagh.adapter": [
            "graphql = graphqldb.adapter:GraphQLAdapter",
        ],
    },
    install_requires=(
        "shillelagh >= 1.2.0",
        "requests >= 2.31.0",
    ),
    license="MIT",
    classifiers=[
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 2 - Pre-Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
    # $ setup.py publish support.
    cmdclass={
        "buildit": BuildCommand,
        "uploadtest": UploadTestCommand,
        "upload": UploadCommand,
    },
)
