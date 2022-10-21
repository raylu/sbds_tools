'use strict';

(async () => {
	const res = await fetch('/static/data/spells.json');
	const spells = await res.json();

	const main = document.querySelector('main');
	for (const [name, data] of Object.entries(spells['SPELL'])) {
		const section = document.createElement('section');
		section.innerHTML = `${name}:`;
		for (const [key, value] of Object.entries(data)) {
			if (Array.isArray(value))
				section.innerHTML += `<div>${key}: <pre>${value.join('\n')}</pre></div>`;
			else
				section.innerHTML += `<div>${key}: ${value}</div>`;
		}
		main.appendChild(section);
	}
})();
