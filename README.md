
For Atari environments, will need to run the following:
`AutoROM --accept-license`

Increment version number in setup.cfg

Build with 
`python -m build` 

(might need to do )
`pip install build`

Then publish with 
`python -m twine upload dist/*`

Might need to do 
`pip install twine`

