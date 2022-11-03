'use strict';

async function fetchJSON(path) {
	const res = await fetch(path);
	return await res.json();
}

class Translate {
	lang = 'en';
	constructor(languages, translations, langs, clickCB) {
		this.translations = translations;
		this.clickCB = clickCB;

		for (const langCode of languages) {
			const div = document.createElement('div');
			div.innerText = div.dataset['lang'] = langCode;
			if (langCode === this.lang)
				div.classList.add('selected');
			langs.appendChild(div);
		}

		langs.addEventListener('click', this.onClick.bind(this));
	}

	onClick(event) {
		const newLang = event.target.dataset['lang'];
		if (newLang) {
			langs.querySelectorAll('div').forEach((div) => div.classList.remove('selected'));
			event.target.classList.add('selected');
			this.lang = newLang;
			this.clickCB();
		}
	}

	translate(s) {
		const tr = this.translations[s];
		if (tr)
			return tr[this.lang];
		else // translation not found
			return s;
	}

	translateAll(s) {
		return s.replaceAll(/[A-Z_]+/g, this.translate.bind(this));
	}
}

export { fetchJSON, Translate };
