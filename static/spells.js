'use strict';

(async () => {
	async function fetchJSON(path) {
		const res = await fetch(path);
		return await res.json();
	}
	const spellsPromise = fetchJSON('/static/data/spells.json');
	const translationPromise = fetchJSON('/static/data/translations.json');
	const spells = await spellsPromise;
	const {languages, translations} = await translationPromise;

	const langs = document.querySelector('#langs');
	let lang = 'en';
	for (const langCode of languages) {
		const div = document.createElement('div');
		div.innerText = div.dataset['lang'] = langCode;
		if (langCode === lang)
			div.classList.add('selected');
		langs.appendChild(div);
	}
	langs.addEventListener('click', (event) => {
		const newLang = event.target.dataset['lang'];
		if (newLang) {
			langs.querySelectorAll('div').forEach((div) => div.classList.remove('selected'));
			event.target.classList.add('selected');
			lang = newLang;
			render();
		}
	});

	const main = document.querySelector('main');
	function render() {
		main.innerHTML = '';
		for (const [spellID, data] of Object.entries(spells['SPELL'])) {
			main.appendChild(renderSpell(spellID, data));

			for (const evolveName of data['evolveList'] || []) {
				let evolveData;
				if (evolveName == 'SPELL_INDRA_SIGIL')
					evolveData = spells['SPELL'][evolveName];
				else
					evolveData = spells['EVOLVED'][evolveName];
				const section = renderSpell(evolveName, evolveData);
				section.classList.add('evolved');
				main.appendChild(section);
			}
		}
	}

	const numFormat = new Intl.NumberFormat(undefined, {'maximumFractionDigits': 2});
	function renderSpell(spellID, data) {
		const section = document.createElement('section');

		const spellBase = document.createElement('div');
		spellBase.classList.add('spell_base');
		const name = translate(data['spellName']);
		spellBase.innerHTML = `<div>
				<img loading="lazy" src="/static/data/spells/${spellID}.png">
				<h3>${name}</h3>
			</div>`;
		const stats = document.createElement('div');
		stats.classList.add('stats');
		stats.innerHTML = `
			<div>base damage: ${data['baseDamage']}</div>
			<div>base cooldown: ${data['baseCooldown']}</div>
			<div>projectiles: ${data['projectileAmount']}</div>
			<div>projectile delay: ${data['multiProjectileDelay']}</div>`;
		if (data['spellTags'] !== null)
			stats.innerHTML += `<div>tags: ${data['spellTags'].join(', ')}</div>`;
		spellBase.appendChild(stats);
		section.appendChild(spellBase);

		renderLevels(section, data);
		return section;
	}

	function renderLevels(section, data) {
		section.innerHTML += '<button class="level_toggle">levels</button>';
		const levels = document.createElement('div');
		levels.classList.add('levels');
		const levelDescs = document.createElement('div');
		const minLevel = data['spellLevel'] ?? 1;
		if (data['levelUpDescriptions'] !== null)
			data['levelUpDescriptions'].forEach((desc, i) => {
				if (i+1 >= minLevel) {
					const translated = desc.replaceAll(/[A-Z_]+/g, translate);
					levelDescs.innerHTML += `<div>${i+1}: ${translated}\n</div>`;
				}
			});
		levels.appendChild(levelDescs);
		section.appendChild(levels);

		if (data['levelData'] !== null) {
			const levelTable = document.createElement('table');
			const {levelData} = data;
			const varNames = new Set();
			Object.values(levelData).forEach((stmts) => {
				stmts.forEach((stmt) => varNames.add(stmt[0]));
			});
			const vars = {};
			let tr = document.createElement('tr');
			tr.innerHTML = '<td>level</td>';
			for (const varName of varNames) {
				tr.innerHTML += `<td>${varName}</td>`;
				let baseValue = 0;
				if (data[varName])
					baseValue = data[varName];
				vars[varName] = baseValue;
			}
			levelTable.appendChild(tr);

			const maxLevel = Math.max(...Object.keys(levelData));
			for (let level = minLevel; level <= maxLevel; level++) {
				const bonus = levelData[level] ?? [];
				for (const [varName, op, num] of bonus) {
					if (op === '+=')
						vars[varName] += num;
					else if (op === '-=')
						vars[varName] -= num;
				}

				tr = document.createElement('tr');
				tr.innerHTML = `<td>${level}</td>`
				for (const varName of varNames)
					tr.innerHTML += `<td>${numFormat.format(vars[varName])}</td>`;
				levelTable.appendChild(tr);
			}
			levels.appendChild(levelTable);
		}
	}
	main.addEventListener('click', (event) => {
		if (event.target.tagName === 'BUTTON') {
			const levels = event.target.parentElement.querySelector('.levels');
			levels.classList.toggle('visible');
		}
	});

	function translate(s) {
		const tr = translations[s];
		if (tr)
			return tr[lang];
		else // translation not found
			return s;
	}

	render();
})();
