# bachelor-oppgave-nina

### Requirements
- [npm](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm)
- [poetry](https://python-poetry.org/docs/#insntalling-with-the-official-installer)


I recommend adding poetry to your PATH.
Add `%APPDATA%\Python\Scripts` on windows.

`poetry config virtualenvs.in-project true --local` **if** you want the virtual environment to be created in .venv at the root of the project

`poetry install` to install project dependencies

`pre-commit install` to install pre-commit hooks.

`pre-commit install --hook-type commit-msg` to install commitlint hook.


See the commitlint config:
https://github.com/conventional-changelog/commitlint/tree/master/%40commitlint/config-conventional
