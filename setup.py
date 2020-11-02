import setuptools

with open('README.md') as fh:
    long_description = fh.read()

setuptools.setup(
    name="bugfixminer",
    version="0.0.1",
    author="Lincoln Rocha, Diego Freitas, Gabriel Freire, Pedro Ernesto, Davi Segundo, Eduardo Alcantra",
    description="Mine bug reports using Jira and Git",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gabrielfvale/engsoft-bugfixminer",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    entry_points={
        'console_scripts': [
            'bugfixminer=bugfixminer:main'
        ]
    },
    python_requires='>=3.7',
)
