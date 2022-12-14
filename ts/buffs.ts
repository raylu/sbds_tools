'use strict';

import {fetchJSON, setupSearch, Translate} from './common.mjs';

interface Buff {
	shrineText: string;
	notificationText: string;
	[key: string]: string | number;
}

(async () => {
	const buffsPromise = fetchJSON('/static/data/buffs.json');
	const translationPromise = fetchJSON('/static/data/translations.json');
	const buffs: Array<Array<Buff>> = await buffsPromise;
	const {languages, translations} = await translationPromise;

	const translator = new Translate(languages, translations,
		document.querySelector('#langs'), () => render(search.value));

	const range = document.createRange();
	const buffsDiv = document.querySelector('.buffs');
	function render(query: string | null) {
		buffsDiv.innerHTML = '';
		if (query !== null)
			query = query.toLowerCase();
		for (const buffPair of buffs) {
			if (query === null || queryMatchBuff(query, buffPair)) {
				const [shrine, enemy] = buffPair;
				buffsDiv.appendChild(renderBuff(shrine['shrineText'], shrine, false));
				if (enemy['shrineText'])
					buffsDiv.appendChild(renderBuff(shrine['shrineText'], enemy, true));
			}
		}
	}

	const numFormat = new Intl.NumberFormat(undefined, {'maximumFractionDigits': 2});
	function renderBuff(playerBuffId: string, data: Buff, isEnemy: boolean) {
		const section = document.createElement('section');
		if (isEnemy)
			section.classList.add('enemy');
		const name = translator.translate(data['shrineText']);
		section.innerHTML = `<div class="buff_left">
				<h3>${name}</h3>
				<img loading="lazy" src="/static/data/buffs/${playerBuffId}.png" class="buff_icon">
			</div>`;
		const buffRight = range.createContextualFragment(
			'<div class="buff_right"></div>').firstChild as HTMLDivElement;
		if (data['notificationText']) {
			const description = translator.translateAll(data['notificationText']);
			buffRight.innerHTML += `<div class="buff_desc">${description}</div>`;
		}
		for (let [key, value] of Object.entries(data)) {
			const split = key.split('.');
			if (split.length < 2 || (split[0] != 'buffZone' &&
				split[0].toLowerCase().substring(0, 'enemybuffzone'.length) != 'enemybuffzone'))
				continue;
			if (typeof(value) == 'number')
				value = numFormat.format(value);
			buffRight.innerHTML += `<div>${split[1]}: ${value}</div>`;
		}
		section.appendChild(buffRight);
		return section;
	}

	function queryMatchBuff(query: string, buffPair: Buff[]) {
		for (const data of buffPair) {
			if (!data['shrineText'])
				continue;
			const name = translator.translate(data['shrineText']);
			if (name.toLowerCase().indexOf(query) !== -1)
				return true;
		}
		return false;
	}

	const search = document.querySelector('input#search') as HTMLInputElement;
	setupSearch(search, render);
})();
