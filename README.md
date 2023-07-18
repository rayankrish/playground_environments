# PlaygroundRL Environments Package

This repository contains the game environments used in the backend
of the PlaygroundRL website. These environments help to facilitate
gameplay by providing relevant game boundaries, rules, and states.
In particular, the repository contains PettingZoo environments,
allowing for multi-agent reinforcement learning research opportunities. 
Instructions to install this package are below. 

## How to Install

1. Increment version number in setup.cfg

2. Use `pip install .` to install the package's dependencies

3. Build the package with 
`python -m build` 
    - You may need to do `pip install build` if `build` is not installed in your computer

4. Then publish with 
`python -m twine upload dist/*`
    - You may need to do 
      `pip install twine` if `twine` is not installed in your computer

## Credits

Created and developed by Rayan Krishnan and Langston Nashold. 

Modified by Chuyi Zhang.

## License

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

