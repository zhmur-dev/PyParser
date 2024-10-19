# PyParser

A command line utility to handle up-to-date official Python documentation in the most convenient way.

```
positional arguments:
  {whats-new,latest-versions,download,pep}
                        PyParser operation mode

options:
  -h, --help            show this help message and exit
  -c, --clear-cache     clear cache
  -o {pretty,file}, --output {pretty,file}
                        additional output options
```

* **whats-new**: generate a list of URLs, headers and authors of articles on what's new in each Python version available at the moment.

* **latest-versions**: generate a list of URLs, versions and statuses for all Python versions available at the moment.
* **download**: download an archive with documentation for latest Python version in PDF.  Downloaded archive will be saved in "downloads" folder.
* **pep**: get a short summary of current statuses for all published PEP documents.

If output is set to "file", the results will be stored as csv files in "results" directory (for all modes except "download").

---

To install PyParser locally do the following:

```bash
# Clone PyParser from GitHub
git clone git@github.com:zhmur-dev/PyParser.git

# Create and activate virtual environment
# MacOS / Linux:
python3 -m venv venv
source venv/bin/activate
# Windows:
python -m venv venv
source venv/Scripts/activate

# Upgrade package manager and install requirements
pip install --upgrade pip
pip install -r requirements.txt

# Run the utility in requested mode, e.g. "help"
python3 src/main.py -h
```

---

Author: Alexander [zhmur-dev](https://github.com/zhmur-dev) Zhmurkov

Developed with Python3.12 and BeautifulSoup4