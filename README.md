# Query Project
A fork of the ESLWriter project to enhance result presentation by visualization.

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
Modify `eslwriter/views.py`, where is marked by `# TODO: ---- add r['m'] to vis_data ----`.
Modify `eslwriter/templates/eslwriter/sentence_result.html` to show visualization of vis_data
