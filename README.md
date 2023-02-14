# bachelor-oppgave-nina

### Requirements
- [npm](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm)
- [commitlint (not husky)](https://commitlint.js.org/#/./guides-local-setup?id=guides-local-setup)
- [poetry](https://python-poetry.org/docs/#installing-with-the-official-installer)




`poetry config virtualenvs.in-project true --local` **if** you want the virtual environment to be created in .venv at the root of the project

`poetry install` to install project dependencies

`pre-commit install` to install pre-commit hooks.

`pre-commit install --hook-type commit-msg` to install commitlint hook.


See the commitlint config:
https://github.com/conventional-changelog/commitlint/tree/master/%40commitlint/config-conventional
