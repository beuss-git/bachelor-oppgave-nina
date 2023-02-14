# bachelor-oppgave-nina

## Requirements
Install CUDA 11.7:
https://developer.nvidia.com/cuda-11-7-0-download-archive

Install cuDNN v8.6.0 for CUDA 11.x:
https://developer.nvidia.com/rdp/cudnn-archive

Install python requirements:
`pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cu117`

Install ffmpeg:
https://www.ffmpeg.org/

- [npm](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm)
- [commitlint (not husky)](https://commitlint.js.org/#/./guides-local-setup?id=guides-local-setup)
- [poetry](https://python-poetry.org/docs/#installing-with-the-official-installer)



`poetry install` to install project dependencies

`poetry config virtualenvs.in-project true --local` **if** you want the virtual environment to be created in .venv at the root of the project

`poetry install` to install project dependencies

`pre-commit install` to install pre-commit hooks.

`pre-commit install --hook-type commit-msg` to install commitlint hook.


See the commitlint config:
https://github.com/conventional-changelog/commitlint/tree/master/%40commitlint/config-conventional
