'use strict';

(async () => {
	async function fetchJSON(path) {
		const res = await fetch(path);
		return await res.json();
	}
	const spellsPromise = fetchJSON('/static/data/spells.json');
	const translationPromise = fetchJSON('/static/data/translations.json');
	const spells = await spellsPromise;
	const {translations} = await translationPromise;

	let lang = 'en';

	const main = document.querySelector('main');
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

	function renderSpell(spellID, data) {
		const section = document.createElement('section');
		const name = translate(data['spellName']);
		section.innerHTML = `<img src="/static/data/spells/${spellID}.png"><h3>${name}:</h3>`;
		for (const [key, value] of Object.entries(data)) {
			if (Array.isArray(value))
				section.innerHTML += `<div>${key}: <pre>${value.join('\n')}</pre></div>`;
			else
				section.innerHTML += `<div>${key}: ${value}</div>`;
		}
		return section;
	}

	function translate(s) {
		const tr = translations[s];
		if (tr)
			return tr[lang];
		else // translation not found
			return s;
	}
})();
