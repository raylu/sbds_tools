from ast import Assert
import glob
import os
import os.path

class GameData:
	def __init__(self):
		self.spells: dict[str, str] = self.load_spells()

	def load_spells(self):
		base_dir = 'extracted/Spells'
		for name in os.listdir(base_dir):
			path = os.path.join(base_dir, name)
			if not os.path.isdir(path):
				continue

			tscn = os.path.join(path, f'Spell_{name}.tscn')
			if not os.path.exists(tscn):
				spell_tscns = glob.glob(os.path.join(path, 'Spell_*.tscn'))
				if len(spell_tscns) == 0:
					continue
				elif len(spell_tscns) == 1:
					(tscn,) = spell_tscns
				else:
					assert name == 'MysticBolt'
					tscn = os.path.join(path, 'Spell_GhostBullet.tscn')
			self.read_tscn(tscn)
	
	def read_tscn(self, path):
		print(path)
		in_spell_node = False
		with open(path, 'r', encoding='ascii') as f:
			for line in f:
				if not line:
					continue
				if in_spell_node:
					if line.startswith('['):
						return
					key, val = line.split(' = ', 1)
					print(key, val.rstrip())
				elif line.startswith('[node name="Spell_'):
					in_spell_node = True
