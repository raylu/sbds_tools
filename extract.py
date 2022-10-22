#!/usr/bin/env python3

import csv
import json
import os
import re
import shutil

import godot_parser

def main():
	shutil.rmtree('static/data', ignore_errors=True)
	for d in ['static/data', 'static/data/spells']:
		os.mkdir(d)

	langs, translations = prepare_translations()
	with open('static/data/translations.json', 'w') as f:
		json.dump({'languages': list(langs), 'translations': translations}, f, indent='\t')
	with open('static/data/spells.json', 'w') as f:
		json.dump(prepare_spells(), f, indent='\t')

def prepare_translations() -> tuple[set, dict[str, dict[str, str]]]:
	translations = {}
	langs = None
	with open('extracted/SBDS Translations - General Terms.csv', 'r', encoding='utf-8') as f:
		reader = csv.DictReader(f)
		row = next(reader)
		langs = frozenset(lang for lang, s in row.items() if s and lang != 'keys')
		print('languages:', ', '.join(langs))
		translations[row['keys']] = {lang: s for lang, s in row.items() if lang in langs}
		for row in reader:
			if len(row['keys']) == 0:
				continue
			translations[row['keys']] = {lang: s for lang, s in row.items() if lang in langs}
	return langs, translations

def prepare_spells() -> dict:
	spell_paths = {'SPELL': [], 'EVOLVED': [], 'AURA': []}
	path_re = re.compile(r'preload\("res://(.+)"\)')
	with open('extracted/SpellReferenceList.gd', 'r', encoding='ascii') as f:
		for line in f:
			if not line.startswith('\t"'):
				continue
			m = re.match(r'\t"([A-Z]+)_([A-Z_]+)":(.+),', line.rstrip())
			prefix, name, paths = m.groups()
			if prefix in ('SPELL', 'EVOLVED'):
				path = path_re.match(paths).group(1)
				spell_paths[prefix].append(path)
			else:
				assert prefix == 'AURA'
				paths = re.match(r'\[(.+), (.+), "\w+"\]', paths).groups()
				paths = [path_re.match(path).group(1) for path in paths]
				spell_paths[prefix].append(paths)

	spells = {
		'SPELL': {},
		'EVOLVED': {},
	}
	fields = [
		'spellName',
		'baseDamage',
		'baseCooldown',
		'projectileAmount',
		'multiProjectileDelay',
		'levelUpDescriptions',
		'evolveList',
		'spellTags',
	]
	for prefix in ('SPELL', 'EVOLVED'):
		for path in spell_paths[prefix]:
			scene = godot_parser.load('extracted/' + path)

			node = scene.find_node(parent=None)
			spell_id = node['spellID']
			spell = {key: node.get(key) for key in fields}
			assert prefix == 'SPELL' or spell['evolveList'] is None
			spells[prefix][spell_id] = spell

			icon = node.get('newLevelUpIcon', node.get('levelUpIcon'))
			resource = scene.find_ext_resource(id=icon.id)
			if resource.type == 'PackedScene':
				scene = godot_parser.load('extracted/' + resource.path[len('res://'):])
				resource = scene.find_ext_resource(type='Texture')
			assert resource.path.startswith('res://')
			img_path = resource.path[len('res://'):]
			print(spell_id, '→', img_path)
			os.link('extracted/' + img_path, f'static/data/spells/{spell_id}.png')
	
	return spells

if __name__ == '__main__':
	main()
