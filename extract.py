#!/usr/bin/env python3

import json
import os
import re

import godot_parser

def main():
	try:
		os.mkdir('static/data')
	except FileExistsError:
		pass

	with open('static/data/spells.json', 'w') as f:
		json.dump(load_spells(), f, indent='\t')

def load_spells() -> dict:
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
				spell_paths[prefix].append((name, path))
			else:
				assert prefix == 'AURA'
				paths = re.match(r'\[(.+), (.+), "\w+"\]', paths).groups()
				paths = [path_re.match(path).group(1) for path in paths]
				spell_paths[prefix].append((name, paths))

	spells = {
		'SPELL': {},
		'EVOLVED': {},
	}
	fields = [
		'baseDamage',
		'baseCooldown',
		'projectileAmount',
		'levelUpDescriptions',
		'evolveList',
		'spellTags',
	]
	for prefix in ('SPELL', 'EVOLVED'):
		for name, path in spell_paths[prefix]:
			scene = godot_parser.load('extracted/' + path)
			(root,) = (node for node in scene.get_nodes() if not node.parent)
			spell = {key: root.get(key) for key in fields}
			assert prefix == 'SPELL' or spell['evolveList'] is None
			spells[prefix][name] = spell
	
	return spells

if __name__ == '__main__':
	main()
