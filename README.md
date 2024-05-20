# ZCodeCompiler
## 1. Language Specification
You can read about the language in zcode-specification.pdf

The language is a dynamic type, static scope programming language.
## 2.Preresiquite
You need to have:
- Python3 (recomended, you could use Python)
- Install antlr4 for python:
```bash
pip install antlr4-python3-runtime
# or 
pip3 install antlr4-python3-runtime
```
- ANTLR_JAR environment variable:
You can use the ANTLR_JAR I have defined with the antlr jar I included in the ANTLR folder.

## 3. How to run
1. Navigate to the src directory.
2. Init the Lexer and Parser (if not initialized) by:
```bash
python run.py gen
#or
python3 run.py gen
```
3. Write your test:
- For Static type Checking: write in CheckerSuite.py
- For Code Generating: write in CodeGenSuite.py
- Define new function that start with test, and use similar command like the test a wrote.
4. Run it
- For Static type Checking:
```bash
python run.py test CheckerSuite
#or
python3 run.py test CheckerSuite
```
- For Code generating:
```bash
python run.py test CodeGenSuite
#or
python3 run.py test CodeGenSuite
```
