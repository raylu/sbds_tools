#!/usr/bin/env python3

import collections
import csv
import json
import os
import re
import shutil
import typing

import gdtoolkit.parser # .gd/script parser
import godot_parser # .tscn/scene parser
import lark.lexer
import lark.tree

def main():
	shutil.rmtree('static/data', ignore_errors=True)
	for d in ['static/data', 'static/data/spells', 'static/data/buffs']:
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
	with open('static/data/buffs.json', 'w') as f:
		json.dump(prepare_buffs(), f, indent='\t')

def prepare_translations() -> tuple[set, dict[str, dict[str, str]]]:
	translations = {}
	langs = None
	with open('extracted/.assets/translations.csv', 'r', encoding='utf-8') as f:
		reader = csv.DictReader(f)
		row = next(reader)
		langs = frozenset(lang for lang, s in row.items() if s and lang != 'key')
		print('languages:', ', '.join(langs))
		translations[row['yi_US']] = {lang: s for lang, s in row.items() if lang in langs}
		for row in reader:
			if len(row['yi_US']) == 0:
				continue
			translations[row['yi_US']] = {lang: s for lang, s in row.items() if lang in langs}
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
				if prefix == 'SPELL' and name == 'INDRA_SIGIL':
					prefix = 'EVOLVED'
				spell_paths[prefix].append(path)
			else:
				assert prefix == 'AURA'
				if name == 'DEATHBOUND':
					continue
				paths = re.match(r'\[(.+), (.+), "\w+"\]', paths).groups()
				paths = [path_re.match(path).group(1) for path in paths]
				spell_paths[prefix].append(paths)

	spells = {
		'SPELL': {},
		'EVOLVED': {},
		'AURA': [],
	}
	fields = [
		'spellName',
		'spellLevel',
		'levelUpDescriptions',
		'evolveList',
		'spellTags',
		'learnDescription',
	]
	base_stat_fields = [
		'baseDamage',
		'baseCooldown',
		'projectileAmount',
		'multiProjectileDelay',
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

			base_stats = {key: node.get(key) for key in base_stat_fields}
			if base_stats['baseCooldown'] is None:
				base_stats['baseCooldown'] = 1.0
			spell['baseStats'] = base_stats

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
				level_data, extra_base_stats = parse_level_data('extracted/' + resource.path[len('res://'):])
				base_stats.update(extra_base_stats)
			spell['levelData'] = level_data

			spells[prefix][spell_id] = spell
	
	fields = [
		'titleText',
		'description',
	]
	for paths in spell_paths['AURA']:
		# always 2 paths; second is evolution
		aura_pair = []
		for path in paths:
			scene = godot_parser.load('extracted/' + path)
			node = scene.find_node(parent=None)
			aura = {key: node.get(key) for key in fields}
			aura_id = node['titleText']

			icon = node.get('sprite')
			if icon is not None:
				resource = scene.find_ext_resource(id=icon.id)
			else:
				resource = scene.find_ext_resource(id=node['iconOnlySprite'].id)
				icon_scene = godot_parser.load('extracted/' + resource.path[len('res://'):])
				resource = icon_scene.find_ext_resource(type='Texture')
			assert resource.path.startswith('res://')
			img_path = resource.path[len('res://'):]
			print(aura_id, '→', img_path)
			os.link('extracted/' + img_path, f'static/data/spells/{aura_id}.png')

			aura_pair.append(aura)
		spells['AURA'].append(aura_pair)

	return spells

def parse_level_data(path: str) -> tuple[dict[int, list], dict[str, float]]:
	with open(path, 'r', encoding='ascii') as f:
		tree = gdtoolkit.parser.parser.parse(f.read())

	base_stats = {k: v for k, v in iter_base_stats(tree)}

	apply_level_bonus = gd_find_func(tree, 'apply_level_bonus')
	level_data = collections.defaultdict(list)
	for level, stmts in iter_match_branches(apply_level_bonus, 'level'):
		for stmt in stmts:
			level_data[level].extend(level_bonuses(stmt))

	if 1 in level_data:
		assert len(level_data[1]) == 0
		del level_data[1]
	return level_data, base_stats

def iter_base_stats(tree: lark.tree.Tree):
	for stmt in tree.children:
		if stmt.data != 'class_var_stmt':
			continue
		(var_assigned,) = stmt.children
		assert var_assigned.data == 'var_assigned'
		left, right, = var_assigned.children
		assert right.data == 'expr'
		(value,) = right.children
		if isinstance(value, lark.lexer.Token) and value.type == 'NUMBER':
			yield left, float(value.value)

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
	if op == '=':
		return
	assert op in ('+=', '-=', '*='), 'unhandled op %r' % op
	num = float(assnmnt_expr.children[2].value)
	if isinstance(assnmnt_expr.children[0], lark.lexer.Token):
		yield assnmnt_expr.children[0].value, op, num
	elif isinstance(assnmnt_expr.children[0], lark.tree.Tree):
		getattr_expr = assnmnt_expr.children[0]
		assert getattr_expr.data == 'getattr'
		yield getattr_expr.children[2].value, op, num
	else:
		raise AssertionError

def prepare_buffs():
	with open('extracted/CosmicShrine.gd', 'r', encoding='ascii') as f:
		tree = gdtoolkit.parser.parser.parse(f.read())
	set_shrine = gd_find_func(tree, 'set_shrine')

	buff_pairs = []
	for shrine_index, stmts in iter_match_branches(set_shrine, 'shrineIndex'):
		player_buff, monster_buff = parse_buff(stmts)
		buff_id = player_buff['shrineText']
		texture = player_buff.pop('buffIcon.texture')
		assert texture.startswith('res://'), texture
		img_path = texture[len('res://'):]
		os.link('extracted/' + img_path, f'static/data/buffs/{buff_id}.png')
		buff_pairs.append((player_buff, monster_buff))
	return buff_pairs

def parse_buff(stmts: list[lark.tree.Tree]) -> tuple[dict[str, typing.Any], dict[str, typing.Any]]:
	player_buff: dict[str, typing.Any] = {}
	monster_buff: dict[str, typing.Any] = {}
	for stmt in stmts:
		if stmt.data == 'if_stmt':
			(if_branch,) = stmt.children
			assert if_branch.data == 'if_branch'
			assert if_branch.children[0].children[0] == 'affectsEnemyInstead'
			for enemy_stmt in if_branch.children[1:]:
				parsed = parse_buff_stmt(enemy_stmt)
				if parsed is None:
					continue
				left, right = parsed
				monster_buff[left] = right
		else:
			parsed = parse_buff_stmt(stmt)
			if parsed is None:
				continue
			left, right = parsed
			player_buff[left] = right

	return player_buff, monster_buff

def parse_buff_stmt(stmt: lark.tree.Tree) -> typing.Union[None, tuple[str, typing.Any]]:
	if stmt.data != 'expr_stmt':
		return

	(expr,) = stmt.children
	assert expr.data == 'expr'
	(assnmnt_expr,) = expr.children
	if assnmnt_expr.data in ['standalone_call', 'getattr_call']:
		return
	assert assnmnt_expr.data == 'assnmnt_expr'
	left_tree, op, right_tree = assnmnt_expr.children
	if op != '=':
		return

	if isinstance(left_tree, lark.tree.Tree) and left_tree.data == 'getattr':
		obj, dot, attr = left_tree.children
		assert dot == '.'
		left = f'{obj}.{attr}'
	else:
		assert isinstance(left_tree, lark.lexer.Token)
		left = str(left_tree)
	
	if isinstance(right_tree, lark.lexer.Token):
		right = right_tree
		if right.type == 'NUMBER':
			right = float(right)
	elif right_tree.data == 'mdr_expr': # TODO
		modifier, times, effectiveness = right_tree.children
		assert times == '*'
		assert effectiveness in ('playerbuff', 'enemybuff') or (
				effectiveness.data == 'standalone_call' and effectiveness.children[2] == 'playerbuff')
		if isinstance(modifier, lark.lexer.Token):
			assert modifier.type == 'NUMBER'
			right = float(modifier.value)
		else:
			assert isinstance(modifier, lark.tree.Tree)
			assert modifier.data == 'getattr'
			right = ''.join(modifier.children)
	elif right_tree.data == 'standalone_call':
		# assnmnt_expr: buffIcon.texture = preload("res://UI/Icons/Icon_HasteBuff.png")
		assert right_tree.children[0] == 'preload'
		string = right_tree.children[2]
		assert string.data == 'string'
		right = string.children[0].strip('"')
	elif right_tree.data == 'getattr_call':
		# assnmnt_expr: spell = RunInformation.playerInfo.learn_spell("SPELL_SHRINE_LIGHTNING", true)
		assert left == 'spell'
		return
	else:
		right: lark.lexer.Token
		(right,) = right_tree.children
		right = right.strip('"')
	
	if left == 'shrineText.text':
		left = 'shrineText'
	return left, right

def gd_find_func(tree: lark.tree.Tree, name: str) -> lark.tree.Tree:
	(func,) = tree.find_pred(lambda t: t.data == 'func_def' and t.children[0].children[0].value == name)
	return func

def iter_match_branches(tree: lark.tree.Tree,
		match_expr: str) -> typing.Generator[tuple[int, list[lark.tree.Tree]], None, None]:
	(match_tree,) = tree.find_data('match_stmt')
	assert match_tree.children[0].children[0].value == match_expr

	for branch in match_tree.children[1:]:
		branch: lark.tree.Tree
		assert branch.data == 'match_branch'
		pattern, *stmts = branch.children
		assert pattern.data == 'pattern'
		yield int(pattern.children[0].value), stmts

if __name__ == '__main__':
	main()
