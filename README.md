# SMD Converter
GUI application to convert smd files to [Igor Pro](https://www.wavemetrics.com/) files (Igor binary wave)

## Requirements
- [ibwpy](https://github.com/MiLL4U/ibwpy) (library to Read/Write Igor binary waves)

## Installation
### Install with pip
1. download wheel package from https://github.com/MiLL4U/smd-converter/tree/main/wheel_package

2. Install SMD Converter with pip
```bash
$ python -m pip install smdconverter-x.y.z-py3-none-any.whl
```
<span style="color: #FFAAAA">(replace x.y.z with the version of SMD Converter which you downloaded)</span>

### Install with git clone
1. Clone this repository

```bash
$ git clone https://github.com/MiLL4U/smd-converter.git
```

2. Go into the repository

```bash
$ cd smd-converter
```

3. Install SMD Converter with setup.py

```bash
$ python setup.py install
```

## Usage
Launch GUI application with:
```bash
$ python -m smdconverter
```
