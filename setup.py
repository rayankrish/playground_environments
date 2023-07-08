from setuptools import setup, find_packages

setup(
    name="playgroundrl_envs",
    version="0.0.7",
    author="Rayan Krishnan",
    # TODO: figure out systematic way to do this
    packages=[
        "playgroundrl_envs",
        "playgroundrl_envs.games",
        "playgroundrl_envs.games.go",
        "playgroundrl_envs.games.go.engine",
        "playgroundrl_envs.games.codenames",
        "playgroundrl_envs.games.catan",
    ],
    package_dir={"": "src"},
    package_data={"": ["*.txt"]},
    include_package_data=True,
    scripts=[],
    url="http://pypi.python.org/pypi/playgroundrl_envs/",
    description="The environments hosted on Playground RL",
    # long_description=open('README.txt').read(),
    install_requires=[
        "attrs==22.2.0",
        "AutoROM==0.6.1",
        "catanatron==3.2.1",
        "cattrs==22.2.0",
        "chess==1.9.4",
        "gymnasium==0.28.1",
        "numpy==1.24.2",
        "pettingzoo==1.23.1",
        "Pillow==9.5.0",
        "pygame==2.4.0",
        "scikit-learn==1.2.2",
        "scipy==1.10.1",
        "texasholdem==0.9.0",
    ],
)
