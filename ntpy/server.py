import re

import asyncio
import json

def tangle_rec(name, sections, tangled, parent_section, blacklist):
	if name in blacklist:
		return []

	blacklist.append(name)

	if name not in sections:
		return []
	if name in tangled:
		return tangled[name]
	lines = []
	for line in sections[name]:
		if re.match("^\\s*;[^;].*", line):
			ref_name = re.match("^\\s*;([^;].*)", line)[1].strip()
			if ref_name not in parent_section:
				parent_section[ref_name] = []

			if name not in parent_section[ref_name]:
				parent_section[ref_name].append(name)


			ref_lines = tangle_rec(ref_name, sections, tangled, parent_section, blacklist)
			for ref_line in ref_lines:
				lines.append(ref_line)


		else:
			lines.append(line)

	tangled[name] = lines
	blacklist.pop()

	return lines

def get_roots(name, parent_section, blacklist):
	if name not in parent_section:
		return [name]
	blacklist.append(name)

	roots = []
	for parent in parent_section[name]:
		parent_roots = get_roots(parent)
		for root in parent_roots:
			roots.append(root)
	blacklist.pop()

	return roots

async def start_server(host='localhost', port=8089):
	server = await asyncio.start_server(on_connect, host, port)
	print(f"Server started on {port}")
	async with server:
		await server.serve_forever()

async def on_connect(reader, writer):
	sections = {}

	tangled = {}

	parent_section = {}

	running_queue = []

	while True:
		data = await reader.readline()
		if len(data) == 0:
			break
		msg = json.loads(data)
		assert("cmd" in msg)
		assert("data" in msg)
		if msg["cmd"] == "execute":
			data = msg["data"]
			assert("name" in data)
			assert("lines" in data)

			name = data["name"]
			lines = data["lines"]
			sections[name] = lines

			tangled = {}
			parent_section = {}

			blacklist = []
			for name in sections.keys():
				tangle_rec(name, sections, tangled, parent_section, blacklist)

			blacklist = []
			roots = get_roots(name, parent_section, blacklist)

			for root in roots:
				if root not in running_queue:
					running_queue.append(root)


	writer.close()
	await writer.wait_closed()


