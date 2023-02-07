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


See the commitlint config:
https://github.com/conventional-changelog/commitlint/tree/master/%40commitlint/config-conventional


`pre-commit install` to install pre-commit hooks.
`pre-commit install --hook-type commit-msg` to install commitlint hook.
