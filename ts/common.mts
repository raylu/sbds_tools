'use strict';

async function fetchJSON(path) {
	const res = await fetch(path);
	return await res.json();
}

class Translate {
	lang = 'en';
	translations: object;
	langs: Element;
	clickCB: () => void;
	constructor(languages: Array<string>, translations: object, langs: Element, clickCB: () => void) {
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
		this.langs = langs;
	}

	onClick(event: Event) {
		const target = event.target as HTMLDivElement;
		const newLang = target.dataset['lang'];
		if (newLang) {
			this.langs.querySelectorAll('div').forEach((div) => div.classList.remove('selected'));
			target.classList.add('selected');
			this.lang = newLang;
			this.clickCB();
		}
	}

	translate(s: string) {
		const tr = this.translations[s];
		if (tr)
			return tr[this.lang];
		else // translation not found
			return s;
	}

	translateAll(s: string) {
		return s.replaceAll(/[A-Z_]+/g, this.translate.bind(this));
	}
}

export { fetchJSON, Translate };
