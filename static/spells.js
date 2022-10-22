'use strict';

(async () => {
	const res = await fetch('/static/data/spells.json');
	const spells = await res.json();

	const main = document.querySelector('main');
	for (const [name, data] of Object.entries(spells['SPELL'])) {
		main.appendChild(renderSpell(name, data));

		for (let evolveName of data['evolveList'] || []) {
			let evolveData;
			if (evolveName == 'SPELL_INDRA_SIGIL') {
				evolveName = 'INDRA_SIGIL';
				evolveData = spells['SPELL'][evolveName];
			} else {
				evolveName = evolveName.substr('EVOLVED_'.length);
				evolveData = spells['EVOLVED'][evolveName];
			}
			const section = renderSpell(evolveName, evolveData);
			section.classList.add('evolved');
			main.appendChild(section);
		}
	}

	function renderSpell(name, data) {
		const section = document.createElement('section');
		section.innerHTML = `<img src="/static/data/spells/${name}.png"><h3>${name}:</h3>`;
		for (const [key, value] of Object.entries(data)) {
			if (Array.isArray(value))
				section.innerHTML += `<div>${key}: <pre>${value.join('\n')}</pre></div>`;
			else
				section.innerHTML += `<div>${key}: ${value}</div>`;
		}
		return section;
	}
})();
