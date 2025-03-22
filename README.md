# NodeTranslator
Translation with node programming.

# Environment
| Name          | Tool                                                |
| ------------- | --------------------------------------------------- |
| **Language**  | Python 3.13                                         |
| **Framework** | [DearPyGUI](https://github.com/hoffstadt/DearPyGui) |

# Usage
## clone
```
git clone https://github.com/taogya/NodeTranslator.git
cd NodeTranslator
```

## create environment
```
python3.13 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
```

## download font
You download "Noto Sans Japanese".
https://fonts.google.com/noto/specimen/Noto+Sans+JP

You copy `NotoSansJP-VariableFont_wght.ttf` to [src](/src)

## launch
```
cd src
python main.py
```
![demo](/resources/demo.mp4)


# Note
Not English input do not show until push enter key.
