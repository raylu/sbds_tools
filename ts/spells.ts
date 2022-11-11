'use strict';

import {fetchJSON, setupSearch, Translate} from './common.mjs';

interface Spell {
	spellName: string;
	spellLevel: number | null;
	levelUpDescriptions: Array<string>;
	evolveList: Array<string>;
	spellTags: Array<string> | null;
	learnDescription: string | null,
	baseStats: {
		baseDamage: number;
		baseCooldown: number;
		projectileAmount: number;
		multiProjectileDelay: number;
		[key: string]: number;
	}
	levelData: {
		[level: string]: Array<[string, string, number]>;
	}
}
interface Aura {
	titleText: string
	description: string
}
interface SpellsResponse {
	SPELL: {[spellID: string]: Spell}
	EVOLVED: {[spellID: string]: Spell}
	AURA: Array<[Aura, Aura]>
}

(async () => {
	const spellsPromise = fetchJSON('/static/data/spells.json');
	const translationPromise = fetchJSON('/static/data/translations.json');
	const spells: SpellsResponse = await spellsPromise;
	const {languages, translations} = await translationPromise;

	const translator = new Translate(languages, translations,
		document.querySelector('#langs'), () => render(search.value));

	const spellsDiv = document.querySelector('.spells');
	function render(query: string | null) {
		spellsDiv.innerHTML = '';
		if (query !== null)
			query = query.toLowerCase();
		for (const [spellID, data] of Object.entries(spells['SPELL'])) {
			if (query === null || queryMatchSpell(query, data)) {
				spellsDiv.appendChild(renderSpell(spellID, data));

				for (const evolveID of data['evolveList'] ?? []) {
					const evolveData = spells['EVOLVED'][evolveID];
					const section = renderSpell(evolveID, evolveData);
					section.classList.add('evolved');
					spellsDiv.appendChild(section);
				}
			}
		}
		for (const auraPair of spells['AURA']) {
			if (query === null || queryMatchAura(query, auraPair)) {
				const [normalAura, evolvedAura] = auraPair;
				spellsDiv.appendChild(renderAura(normalAura, false));
				spellsDiv.appendChild(renderAura(evolvedAura, true));
			}
		}
	}

	function queryMatchSpell(query: string, data: Spell) {
		if (data['spellName'] !== null) {
			const name = translator.translate(data['spellName']);
			if (name.toLowerCase().indexOf(query) !== -1)
				return true;
			for (const tag of data['spellTags'] ?? [])
				if (tag.toLowerCase() === query)
					return true;
		}
		for (const evolveID of data['evolveList'] ?? []) {
			const evolveData = spells['EVOLVED'][evolveID];
			if (queryMatchSpell(query, evolveData))
				return true;
		}
		return false;
	}

	const numFormat = new Intl.NumberFormat(undefined, {'maximumFractionDigits': 2});
	function renderSpell(spellID: string, data: Spell) {
		const section = document.createElement('section');

		const spellBase = document.createElement('div');
		spellBase.classList.add('spell_base');
		const spellBaseLeft = document.createElement('div');
		spellBaseLeft.classList.add('spell_base_left');
		const name = translator.translate(data['spellName']);
		spellBaseLeft.innerHTML = `<h3>${name}</h3>`;
		if (spellID.indexOf('_SHRINE_') !== -1)
			spellBaseLeft.innerHTML += '<span> (shrine)</span>';
		const learnDesc = data['learnDescription'] ?? '';
		if (learnDesc === 'ILLEGAL_SPELL' || learnDesc.substr(0, 15) === 'Illegal Magic -')
			spellBaseLeft.innerHTML += '<span> (illegal)</span>';
		spellBaseLeft.innerHTML += `<img loading="lazy"
				src="/static/data/spells/${spellID}.png" class="spell_icon">`;
		spellBase.appendChild(spellBaseLeft);
		const stats = document.createElement('div');
		stats.classList.add('stats');
		const baseStats = data['baseStats'];
		stats.innerHTML = `
			<div>base damage: ${baseStats['baseDamage']}</div>
			<div>base cooldown: ${baseStats['baseCooldown']}</div>
			<div>projectiles: ${baseStats['projectileAmount']}</div>
			<div>projectile delay: ${baseStats['multiProjectileDelay']}</div>`;
		if (data['spellTags'] !== null)
			stats.innerHTML += `<div>tags: ${data['spellTags'].join(', ')}</div>`;
		spellBase.appendChild(stats);
		section.appendChild(spellBase);

		renderLevels(section, data);
		return section;
	}

	function renderLevels(section: HTMLElement, data: Spell) {
		section.innerHTML += '<button class="level_toggle">levels</button>';
		const levels = document.createElement('div');
		levels.classList.add('levels');
		const levelDescs = document.createElement('div');
		const minLevel = data['spellLevel'] ?? 1;
		if (data['levelUpDescriptions'] !== null)
			data['levelUpDescriptions'].forEach((desc, i) => {
				if (i+1 >= minLevel) {
					const translated = translator.translateAll(desc);
					levelDescs.innerHTML += `<div>${i+1}: <span class="level_up_desc">${translated}</span></div>`;
				}
			});
		levels.appendChild(levelDescs);
		section.appendChild(levels);

		if (data['levelData'] !== null) {
			const levelTable = document.createElement('table');
			const {levelData, baseStats} = data;
			const varNames: Set<string> = new Set();
			Object.values(levelData).forEach((stmts) => {
				stmts.forEach((stmt) => varNames.add(stmt[0]));
			});
			const vars = {};
			let tr = document.createElement('tr');
			tr.innerHTML = '<td>level</td>';
			for (const varName of varNames) {
				tr.innerHTML += `<td>${varName}</td>`;
				let baseValue = 0;
				if (baseStats[varName])
					baseValue = baseStats[varName];
				vars[varName] = baseValue;
			}
			levelTable.appendChild(tr);

			const maxLevel = Math.max(...Object.keys(levelData).map(Number));
			for (let level = minLevel; level <= maxLevel; level++) {
				const bonus = levelData[level] ?? [];
				for (const [varName, op, num] of bonus) {
					if (op === '+=')
						vars[varName] += num;
					else if (op === '-=')
						vars[varName] -= num;
					else if (op === '*=')
						vars[varName] *= num;
				}

				tr = document.createElement('tr');
				tr.innerHTML = `<td>${level}</td>`;
				for (const varName of varNames)
					tr.innerHTML += `<td>${numFormat.format(vars[varName])}</td>`;
				levelTable.appendChild(tr);
			}
			levels.appendChild(levelTable);
		}
	}
	spellsDiv.addEventListener('click', (event) => {
		if ((event.target as HTMLElement).tagName === 'BUTTON') {
			const levels = (event.target as HTMLButtonElement).parentElement.querySelector('.levels');
			levels.classList.toggle('visible');
		}
	});

	function queryMatchAura(query: string, auraPair: [Aura, Aura]) {
		for (const data of auraPair) {
			const name = translator.translate(data['titleText']);
			if (name.toLowerCase().indexOf(query) !== -1)
				return true;
		}
		return false;
	}

	function renderAura(data: Aura, evolved: boolean) {
		const section = document.createElement('section');
		if (evolved)
			section.classList.add('evolved');
		const name = translator.translate(data['titleText']);
		const description = translator.translateAll(data['description']);
		section.innerHTML = `<div class="spell_base">
				<div class="spell_base_left">
					<h3>${name}</h3>
					<img loading="lazy" src="/static/data/spells/${data['titleText']}.png" class="spell_icon">
				</div>
				<div class="stats">
					<div>${description}</div>
				</div>
			</div>`;
		return section;
	}

	const search = document.querySelector('input#search') as HTMLInputElement;
	setupSearch(search, render);
})();
