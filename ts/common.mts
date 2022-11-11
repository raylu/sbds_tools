'use strict';

async function fetchJSON(path: string) {
	const res = await fetch(path);
	return await res.json();
}

function setupSearch(input: HTMLInputElement, render: (q: string | null) => void) {
	let searchTimeout = null;
	input.addEventListener('input', (event) => {
		if (searchTimeout !== null)
			clearTimeout(searchTimeout);
		const query = input.value;
		searchTimeout = setTimeout(() => render(query), 200);
	});

	render(null);
}

class Translate {
	lang: string;
	translations: object;
	langs: Element;
	clickCB: () => void;
	constructor(languages: Array<string>, translations: object, langs: Element, clickCB: () => void) {
		this.translations = translations;
		this.clickCB = clickCB;

		const url = new URL(window.location as unknown as string);
		this.lang = url.searchParams.get('lang') ?? 'en';

		const langNames = {
			'en': 'English',
			'bg_BG': 'български',
			'ja': '日本語',
			'ru': 'Русский',
			'yi_US': 'keys',
			'zh_Hans_CN': '简体中文',
			'zh_Hant_TW': '繁體中文',
		};
		for (const langCode of languages.sort()) {
			const div = document.createElement('div');
			div.innerText = langNames[langCode] ?? langCode;
			div.dataset['lang'] = langCode;
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

			const url = new URL(window.location as unknown as string);
			url.searchParams.set('lang', newLang);
			history.pushState({}, '', url);

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

export { fetchJSON, setupSearch, Translate };
