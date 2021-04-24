from setuptools import setup


setup(
    name='cldfbench_saphon',
    py_modules=['cldfbench_saphon'],
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'cldfbench.dataset': [
            'saphon=cldfbench_saphon:Dataset',
        ]
    },
    install_requires=[
        'cldfbench',
    ],
    extras_require={
        'test': [
            'pytest-cldf',
        ],
    },
)
