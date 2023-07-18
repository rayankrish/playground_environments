# PlaygroundRL Environments Package

This repository contains the game environments used in the backend
of the PlaygroundRL website. These environments help to facilitate
gameplay by providing relevant game boundaries, rules, and states.
Instructions to install this package are below. 

## How to Install

1. Increment version number in setup.cfg

2. Build with 
`python -m build` 
- You may need to do
    `pip install build`

3. Then publish with 
`python -m twine upload dist/*`
- You may need to do 
    `pip install twine`