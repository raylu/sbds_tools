## setup

1. download `GDRE_tools-standalone` from https://github.com/bruvzg/gdsdecomp/issues/88#issuecomment-1289829017 and extract it
1. assuming you extracted to `gdre_tools/`, `gdre_tools/gdre_tools.x86_64 --headless --output-dir=extracted
   --recover='/mnt/.../Steam/steamapps/common/Spellbook Demonslayers/Spellbook Demonslayers.pck'`
1. `pip3 install -r requirements.txt -r requirements_extract.txt`
1. `./extract.py`
1. `npm install -g typescript`
1. `npx tsc`
1. `./sbds_tools.py`

## development

1. `npm install @typescript-eslint/eslint-plugin @typescript-eslint/parser eslint typescript`
1. `npx tsc --watch`

* `npx eslint ts`
