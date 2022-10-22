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

	function renderSpell(spellID, data) {
		const section = document.createElement('section');
		const name = translate(data['spellName']);
		section.innerHTML = `<img loading="lazy" src="/static/data/spells/${spellID}.png">` +
				`<h3>${name}:</h3>`;
		section.innerHTML += `<div>base damage: ${data['baseDamage']}</div>`;
		section.innerHTML += `<div>base cooldown: ${data['baseDamage']}</div>`;
		section.innerHTML += `<div>projectiles: ${data['projectileAmount']}</div>`;
		section.innerHTML += `<div>projectile delay: ${data['multiProjectileDelay']}</div>`;

		const levels = document.createElement('div');
		levels.innerHTML = 'levels';
		if (data['levelUpDescriptions'] !== null)
			data['levelUpDescriptions'].forEach((desc, i) => {
				const translated = desc.replaceAll(/[A-Z_]+/g, translate);
				levels.innerHTML += `<div class="levels">${i+1}: ${translated}\n</div>`;
			});
		section.appendChild(levels);

		if (data['spellTags'] !== null)
			section.innerHTML += `<div>tags: ${data['spellTags'].join(', ')}</div>`;
		return section;
	}

	function translate(s) {
		const tr = translations[s];
		if (tr)
			return tr[lang];
		else // translation not found
			return s;
	}

	render();
})();
