### Introduction
A toy backend for a file-sharing website (**DiaDoc**) based on django 3.0.

<br>

### Installation

All the dependencies are listed in `req.txt`.
You can activate a virtual python environment `YOUR_VENV_NAME` and then use `pip` to install them:

```sh
source activate `YOUR_VENV_NAME`
pip install -r req.txt
```

You also need to add `YOUR_VENV_NAME` into your environment variables, and the key is `DJ_CONDA_ENV`.
Otherwise, shell scripts will use `dj` as the name of virtual environment by default.

<br>

### Tutorial

##### rebuild database:
```sh
sh ./drop.sh
```

##### run server:
```sh
sh ./run.sh
```

##### debug in the shell:
```sh
sh ./run.sh sh
```

##### directories & files:
- logs: `logging`
- frontend: `Dia/frontend`
- django setting file: `Dia/settings.py`
