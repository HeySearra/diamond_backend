### Introduction
A toy backend for a file-sharing website (**DiaDoc**) based on django 3.0.

<br>

### Installation

All the dependencies are listed in `req.txt`.
You can run `install.sh` to install them.

**PLEASE NOTE THIS**: You need to add a virtual python environment's name `YOUR_VENV_NAME` into your environment variables, and its key is `DJ_CONDA_ENV`.
Otherwise, all the shell scripts will use `dj` as the name of virtual environment by default.

<br>

### Tutorial

##### install dependencies:
```sh
sh ./install.sh
```

##### rebuild database:
```sh
sh ./drop.sh
```

##### run server:
```sh
sh ./build.sh
```

##### debug in the shell:
```sh
sh ./build.sh sh
```

##### directories & files:
- logs: `Dia/logging`
- frontend: `Dia/frontend`
- django setting file: `Dia/settings.py`
