# Installing the `qrev` Package

This guide explains how to install the `qrev` package from the GitHub repository:

```text
https://github.com/Sana-hammemi/qrevint
```

The Python package is inside the `qrev` subdirectory of that repository, so the install command must include:

```text
subdirectory=qrev
```

## 1. Open Command Prompt

Open `cmd.exe`, then go to the QRame project folder:

```cmd
cd C:\Users\shammemi\Documents\forge_inrae\qrame-1
```

## 2. Activate the QRame Virtual Environment

Run:

```cmd
C:\Users\shammemi\Documents\forge_inrae\qrame-1\qrame1.27.1\Scripts\activate.bat
```

After activation, the terminal should show:

```cmd
(qrame1.27.1) C:\Users\shammemi\Documents\forge_inrae\qrame-1>
```

## 3. Install `qrev`

Run this exact command:

```cmd
pip install --no-cache-dir "git+https://github.com/Sana-hammemi/qrevint.git@master#egg=qrev&subdirectory=qrev"
```

The quotes are important on Windows.

Without quotes, Windows treats `&subdirectory=qrev` as a separate command, which causes this error:

```text
'subdirectory' is not recognized as an internal or external command
```

## 4. Check That Installation Worked

Run:

```cmd
pip show qrev
```

You should see something like:

```text
Name: qrev
Version: 1.45
Location: C:\Users\shammemi\Documents\forge_inrae\qrame-1\qrame1.27.1\Lib\site-packages
```

You can also test the Python import:

```cmd
python -c "import qrev; print(qrev.__file__)"
```

## 5. Updating or Reinstalling `qrev`

If you change the GitHub repository and want to reinstall the latest version, uninstall the current package first:

```cmd
pip uninstall -y qrev
```

Then reinstall:

```cmd
pip install --no-cache-dir "git+https://github.com/Sana-hammemi/qrevint.git@master#egg=qrev&subdirectory=qrev"
```

You can also force reinstall in one command:

```cmd
pip install --upgrade --force-reinstall --no-cache-dir "git+https://github.com/Sana-hammemi/qrevint.git@master#egg=qrev&subdirectory=qrev"
```

## Common Errors

### Error: inconsistent name

Example:

```text
Requested qrevint has inconsistent name: expected 'qrev', but metadata has 'qrevint'
```

This usually means pip installed from the wrong directory in the repository.

Make sure the command includes:

```text
&subdirectory=qrev
```

Also make sure the whole URL is wrapped in quotes:

```cmd
pip install --no-cache-dir "git+https://github.com/Sana-hammemi/qrevint.git@master#egg=qrev&subdirectory=qrev"
```

### Error: `subdirectory` is not recognized

Example:

```text
'subdirectory' is not recognized as an internal or external command
```

This happens because Windows CMD uses `&` as a command separator.

Fix it by using quotes around the install URL:

```cmd
pip install --no-cache-dir "git+https://github.com/Sana-hammemi/qrevint.git@master#egg=qrev&subdirectory=qrev"
```

### Error: package installs but import fails

Check that `qrev/pyproject.toml` contains a correct setuptools package configuration:

```toml
[project]
name = "qrev"

[tool.setuptools]
packages = ["qrev"]

[tool.setuptools.package-dir]
qrev = "."
```

This tells Python that the current `qrev` directory should be installed as the package named `qrev`.

## Full Install Command Summary

Use this full sequence for a normal installation:

```cmd
cd C:\Users\shammemi\Documents\forge_inrae\qrame-1
C:\Users\shammemi\Documents\forge_inrae\qrame-1\qrame1.27.1\Scripts\activate.bat
pip install --no-cache-dir "git+https://github.com/Sana-hammemi/qrevint.git@master#egg=qrev&subdirectory=qrev"
pip show qrev
```
