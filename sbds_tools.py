#!/usr/bin/env python3

import sys
if len(sys.argv) == 3:
	import eventlet
	import eventlet.wsgi
	eventlet.monkey_patch()

# pylint: disable=wrong-import-position
import mimetypes

from pigwig import PigWig, Response
from pigwig.exceptions import HTTPException

def root(request):
	return Response.render(request, 'index.jinja2', {'no_back_button': True})

def spells_page(request):
	return Response.render(request, 'spells.jinja2', {})

def buffs_page(request):
	return Response.render(request, 'buffs.jinja2', {})

def static(request, path):
	content_type, _ = mimetypes.guess_type(path)
	try:
		with open('static/' + path, 'rb') as f:
			return Response(f.read(), content_type=content_type)
	except FileNotFoundError:
		raise HTTPException(404, '%r not found\n' % path) # pylint: disable=raise-missing-from

routes = [
	('GET', '/', root),
	('GET', '/spells', spells_page),
	('GET', '/buffs', buffs_page),
	('GET', '/static/<path:path>', static),
]

app = PigWig(routes, template_dir='templates')

def main():
	if len(sys.argv) == 3:
		addr = sys.argv[1]
		port = int(sys.argv[2])
		eventlet.wsgi.server(eventlet.listen((addr, port)), app)
	else:
		app.main()

if __name__ == '__main__':
	main()
