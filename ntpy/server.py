import re

import asyncio
import json

tangled = {}

pending_sections = []

async def start_executor():
  global pending_sections
  global tangled

  while True:
    for name in pending_sections:
      if name in tangled:
        code = "\n".join(tangled[name])
      else:
        continue

      exec(code)


    pending_sections = []

    if "loop" in tangled:
      code = "\n".join(tangled["loop"])
      exec(code)
    await asyncio.sleep(0)

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

async def start_server(host='localhost', port=8089):
	server = await asyncio.start_server(on_connect, host, port)
	print(f"Server started on {port}")
	async with server:
		await server.serve_forever()

async def on_connect(reader, writer):
	sections = {}

	global tangled

	parent_section = {}

	global pending_sections

	while True:
		data = await reader.readline()
		if len(data) == 0:
			break
		msg = json.loads(data)
		status = "Done"
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
			for section_name in sections.keys():
				tangle_rec(section_name, sections, tangled, parent_section, blacklist)

			if name != "loop":
				pending_sections.append(name)

		else:
			status = f"Unknown command {msg["cmd"]}"

		response = json.dumps({"status" : status}) + '\n'
		writer.write(response.encode())
		await writer.drain()

		await asyncio.sleep(0)

	writer.close()
	await writer.wait_closed()


if __name__ == "__main__":
	async def main():
		executor_task = asyncio.create_task(start_executor())
		server_task = asyncio.create_task(start_server())
		try:
			await server_task
		except asyncio.CancelledError:
			pass
	asyncio.run(main())

