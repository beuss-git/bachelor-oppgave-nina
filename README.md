# bachelor-oppgave-nina

[![CI][ci-badge]][ci]

[ci-badge]: https://github.com/beuss-git/bachelor-oppgave-nina/actions/workflows/code-quality.yml/badge.svg
[ci]: https://github.com/beuss-git/bachelor-oppgave-nina/actions/workflows/code-quality.yml

### Requirements
- [commitlint (not husky)](https://commitlint.js.org/#/./guides-local-setup?id=guides-local-setup)
- [poetry](https://python-poetry.org/docs/#installing-with-the-official-installer)


I recommend adding poetry to your PATH.
Add `%APPDATA%\Python\Scripts` on windows.

`poetry config virtualenvs.in-project true --local` **if** you want the virtual environment to be created in .venv at the root of the project

`poetry install` to install project dependencies

`poetry run poe torch-cuda` to install torch with cuda.

`pre-commit install` to install pre-commit hooks.

`pre-commit install --hook-type commit-msg` to install commitlint hook.


See the commitlint config:
https://github.com/conventional-changelog/commitlint/tree/master/%40commitlint/config-conventional

## Run using Docker

```
docker compose up --build
```


## VDI Testing
Download the zip file from [here](https://nextcloud.beuss.me/s/2DsJsF56mPBx579) and extract it to `app/vdi_perf_test`
Now simply run `python -m app.vdi_perf_test`.

After that everything we need should be in the log file located at `app/log`


**NB!**
There is an issue where some threads might crash due to out of memory exceptions happening in them and we haven't really added a way to handle them yet.
I made a quick and dirty patch to the frame grabber to somewhat handle it, but that is in no way reliable.

The main working loop of the test should handle it somewhat well and just skip the model.

There is however an issue with with freeing up VRAM because it never seems to totally free up all the memory, so the latter models will have less VRAM to work with so we can't test larger batch sizes on those.

If it always crashes before getting to the larger models, please uncomment line 58 in `app/vdi_perf_test/__main__.py` so we get data for those too.
You could also try to limit the max batch sizes.
