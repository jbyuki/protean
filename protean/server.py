import re

import asyncio
import json

from sympy import latex

sections = {}

tangled = {}

pending_sections = []

async def start_executor():
  global pending_sections
  global tangled

  global message_received_event

  while True:
    for name in pending_sections:
      if name in tangled:
        code = "\n".join(tangled[name])
      else:
        continue

      try:
        exec(code,  globals())
      except Exception as e:
        print(f"Exception {e}")


    pending_sections = []

    if "loop" in tangled:
      name = "loop"
      code = "\n".join(tangled["loop"])
      try:
        exec(code,  globals())
      except Exception as e:
        print(f"Exception {e}")
        del tangled["loop"]
        global sections
        del sections["loop"]

    if "loop" not in tangled or "".join(tangled["loop"]) == "":
      await message_received_event.wait()
      message_received_event.clear()

    await asyncio.sleep(0)

def tangle_rec(name, sections, tangled, parent_section, blacklist, prefix):
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
			match = re.match("^(\\s*);([^;].*)", line)
			new_prefix = match[1]
			ref_name = match[2].strip()
			if ref_name not in parent_section:
				parent_section[ref_name] = []

			if name not in parent_section[ref_name]:
				parent_section[ref_name].append(name)


			ref_lines = tangle_rec(ref_name, sections, tangled, parent_section, blacklist, prefix+new_prefix)
			if len(ref_lines) > 0:
				for ref_line in ref_lines:
					lines.append(prefix + new_prefix + ref_line)
			else:
				lines.append(prefix + new_prefix + "pass")


		else:
			lines.append(line)

	log_debug(name, lines)
	tangled[name] = lines
	blacklist.pop()

	return lines

async def start_server(host='localhost', port=8089):
	server = await asyncio.start_server(on_connect, host, port)
	print(f"Server started on {port}")
	async with server:
		await server.serve_forever()

async def on_connect(reader, writer):
	global message_received_event

	print("Client connected.")
	global sections

	global tangled

	parent_section = {}

	global pending_sections

	while True:
		try:
			data = await reader.readline()
		except:
			break
		print(data)
		if len(data) == 0:
			break
		msg = json.loads(data)
		status = "Done"
		assert("cmd" in msg)

		if msg["cmd"] == "execute":
			assert("data" in msg)
			data = msg["data"]
			assert("name" in data)
			assert("lines" in data)

			name = data["name"]
			lines = data["lines"]
			sections[name] = lines

			tangled = {}
			parent_section = {}


			for section_name in sections.keys():
				blacklist = []
				tangle_rec(section_name, sections, tangled, parent_section, blacklist, "")

			if data["execute"]:
				has_loop_parent = False
				open = [name]
				closed = set()
				closed.add(name)
				while len(open) > 0:
					current = open.pop()
					if current == "loop":
						has_loop_parent = True
						break
					
					if current in parent_section:
						for parent in parent_section[current]:
							if parent not in closed:
								open.append(parent)
								closed.add(current)
				if not has_loop_parent:
					pending_sections.append(name)


		elif msg["cmd"] == "killLoop":
		  sections.pop("loop", None)
		  del tangled["loop"]
		elif msg["cmd"] == "toggleBackend":
		  backend_name = matplotlib.get_backend()
		  if backend_name == "module://protean_matplotlib_backend":
		    matplotlib.rcParams.update(matplotlib.rcParamsDefault)
		    matplotlib.use("qtagg")
		  else:
		  log_debug(f"new backend {matplotlib.get_backend()}")
		else:
			status = f"Unknown command {msg['cmd']}"

		response = json.dumps({"status" : status}) + '\n'
		writer.write(response.encode())
		await writer.drain()

		message_received_event.set()

		await asyncio.sleep(0)

	print("Client disconnected.")
	writer.close()
	await writer.wait_closed()

def msg_latex_output(latex_code):
  msg = {}
  msg["cmd"] = "latex_output"
  msg["data"] = { "task_id": task_id, "content": latex_code }
  return json.dumps(msg)

def disp(exp):
  latex_code = latex(exp)
  global frontend_writers
  for frontend_writer in frontend_writers:
    frontend_writer.send(msg_latex_output(latex_code))

if __name__ == "__main__":
	async def main():
		global message_received_event
		message_received_event = asyncio.Event()

		executor_task = asyncio.create_task(start_executor())
		server_task = asyncio.create_task(start_server())
		frontend_server_task = asyncio.create_task(start_frontend_server())
		try:
			await server_task
		except asyncio.CancelledError:
			pass
	asyncio.run(main())

