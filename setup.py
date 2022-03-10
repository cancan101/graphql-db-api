from setuptools import find_packages, setup

# -----------------------------------------------------------------------------

DESCRIPTION = "Python DB-API and SQLAlchemy interface for GraphQL APIs."

setup(
    name="sqlalchemy-graphqlapi",
    version="0.0.1.dev0",
    description=DESCRIPTION,
    long_description=DESCRIPTION,
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
        "shillelagh >= 1.0.6",
        "sqlalchemy >= 1.3.0",
        "requests >= 2.20.0",
        "typing-extensions",
    ),
    license="MIT",
    classifiers=[
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 2 - Pre-Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
    # $ setup.py publish support.
    cmdclass={
        # 'upload': UploadCommand,
    },
)
