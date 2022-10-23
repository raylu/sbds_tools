#!/usr/bin/env python3

import collections
import csv
import json
import os
import re
import shutil

import gdtoolkit.parser # .gd/script parser
import godot_parser # .tscn/scene parser
import lark.lexer
import lark.tree

def main():
	shutil.rmtree('static/data', ignore_errors=True)
	for d in ['static/data', 'static/data/spells']:
		os.mkdir(d)

	assets = [
		('UI/Font/Japanese-Noto Sans/NotoSansJP-Regular.otf', 'NotoSansJP-Regular.otf'),
	]
	for src, dst in assets:
		print(src, '→', dst)
		os.link('extracted/' + src, 'static/data/' + dst)

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
		'spellLevel',
		'baseDamage',
		'baseCooldown',
		'projectileAmount',
		'multiProjectileDelay',
		'levelUpDescriptions',
		'evolveList',
		'spellTags',
	]
	unparseable_level_data = [
		'SPELL_SHRINE_COLDFRONT',
		'SPELL_SPIRIT_SHIELD',
		'SPELL_STORM_THRONE',
		'SPELL_SHIELD_STORM',
		'SPELL_TORNADO',
		'SPELL_DARK_THRONE',
		'SPELL_MELTDOWN',
		'EVOLVED_GUN_GUARDIANS',
	]
	for prefix in ('SPELL', 'EVOLVED'):
		for path in spell_paths[prefix]:
			scene = godot_parser.load('extracted/' + path)

			node = scene.find_node(parent=None)
			spell_id = node['spellID']
			spell = {key: node.get(key) for key in fields}
			assert prefix == 'SPELL' or spell['evolveList'] is None
			if spell['baseCooldown'] is None:
				spell['baseCooldown'] = 1.0

			icon = node.get('newLevelUpIcon', node.get('levelUpIcon'))
			resource = scene.find_ext_resource(id=icon.id)
			if resource.type == 'PackedScene':
				icon_scene = godot_parser.load('extracted/' + resource.path[len('res://'):])
				resource = icon_scene.find_ext_resource(type='Texture')
			assert resource.path.startswith('res://')
			img_path = resource.path[len('res://'):]
			print(spell_id, '→', img_path)
			os.link('extracted/' + img_path, f'static/data/spells/{spell_id}.png')

			script = node['script']
			resource = scene.find_ext_resource(id=script.id)
			assert resource.path.startswith('res://')
			level_data = None
			if spell_id not in unparseable_level_data:
				level_data = parse_level_data('extracted/' + resource.path[len('res://'):])
			spell['levelData'] = level_data

			spells[prefix][spell_id] = spell
	
	return spells

def parse_level_data(path: str) -> dict[int, tuple]:
	with open(path, 'r', encoding='ascii') as f:
		tree = gdtoolkit.parser.parser.parse(f.read())
	apply_level_bonus: lark.tree.Tree
	(apply_level_bonus,) = tree.find_pred(
			lambda t: t.data == 'func_def' and t.children[0].children[0].value == 'apply_level_bonus')
	match_tree: lark.tree.Tree
	(match_tree,) = apply_level_bonus.find_data('match_stmt')
	assert match_tree.children[0].children[0].value == 'level'

	level_data = collections.defaultdict(list)
	for branch in match_tree.children[1:]:
		branch: lark.tree.Tree
		assert branch.data == 'match_branch'
		pattern, *stmts = branch.children
		assert pattern.data == 'pattern'
		level = int(pattern.children[0].value)
		for stmt in stmts:
			level_data[level].extend(level_bonuses(stmt))

	if 1 in level_data:
		assert len(level_data[1]) == 0
		del level_data[1]
	return level_data

def level_bonuses(stmt: lark.tree.Tree):
	if stmt.data == 'for_stmt':
		# recurse
		for sub_stmt in stmt.find_data('expr_stmt'):
			yield from level_bonuses(sub_stmt)
		return

	# base case
	if stmt.data == 'pass_stmt':
		return
	assert stmt.data == 'expr_stmt', stmt.pretty()
	assnmnt_expr = stmt.children[0].children[0]
	if assnmnt_expr.data in ('getattr_call', 'standalone_call'):
		return
	assert assnmnt_expr.data == 'assnmnt_expr', stmt.pretty()

	op = assnmnt_expr.children[1].value
	assert op in ('+=', '-=')
	num = float(assnmnt_expr.children[2].value)
	if isinstance(assnmnt_expr.children[0], lark.lexer.Token):
		yield assnmnt_expr.children[0].value, op, num
	elif isinstance(assnmnt_expr.children[0], lark.tree.Tree):
		getattr_expr = assnmnt_expr.children[0]
		assert getattr_expr.data == 'getattr'
		yield getattr_expr.children[2].value, op, num
	else:
		raise AssertionError

if __name__ == '__main__':
	main()
