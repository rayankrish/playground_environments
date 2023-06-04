from setuptools import setup

setup(
   name='playgroundrl_envs',
   version='0.0.1',
   author='Rayan Krishnan',
   packages=['playgroundrl_envs'],
   package_dir={'':'src'},
   scripts=[],
   url='http://pypi.python.org/pypi/playgroundrl_envs/',
   description='The environments hosted on Playground RL',
   # long_description=open('README.txt').read(),
   install_requires=[
        'attrs==22.2.0',
        'cattrs==22.2.0',
   ],
)
