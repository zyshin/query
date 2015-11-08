# Query Project
A fork of the ESLWriter project to enhance query interface.

## Setup
* Install dependencies
```shell
pip install -r requirements_x64.txt
```
* Install NLTK corpora
In python shell:
```python
import nltk
nltk.download()
```
Download **WordNet** (`wordnet`) and **Punkt Tokenizer Models** (`punkt`).
* Runserver
```shell
python manage_debug.py runserver
```

## Next Step
Modify `eslwriter/views.py`, where is marked by `# TODO: ---- add your code here ----`.
