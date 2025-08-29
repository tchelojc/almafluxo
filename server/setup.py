from setuptools import setup, find_packages

setup(
    name="flux_on",
    version="1.0",
    packages=find_packages(),
    install_requires=[
        'streamlit',
        'PyQt6',
        'numpy',
        'pandas'
    ],
    entry_points={
        'console_scripts': [
            'fluxon=seletor:main',
        ],
    },
    package_data={
        'project': ['*.py'],
        'day_trade': ['*.py'],
    },
    python_requires='>=3.8',
)