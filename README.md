## setup

1. download https://github.com/bruvzg/gdsdecomp/releases and extract it
1. assuming you extracted to `gdre_tools/`, `gdre_tools/gdre_tools.x86_64 --headless --output-dir=extracted
   --recover='/mnt/.../Steam/steamapps/common/Spellbook Demonslayers Prologue/Spellbook Demonslayers.pck'`
1. download https://docs.google.com/spreadsheets/d/1SrbtXMnRbRUK77WYrmwisTh33dnmSnwtXv7brwAL8Gk
   as CSVs to `extracted/`
1. `pip3 install -r requirements.txt -r requirements_extract.txt`
1. `./extract.py`
1. `npm install -g typescript`
1. `npx tsc`
1. `./sbds_tools.py`

## development

1. `npm install @typescript-eslint/eslint-plugin @typescript-eslint/parser eslint typescript`
1. `npx tsc --watch`

* `npx eslint ts`
