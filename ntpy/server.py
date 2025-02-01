import hashlib
import base64

import struct

import re

import sys
from io import StringIO

import asyncio
import json

class FrontendWriter:
  def __init__(self, writer):
    self.writer = writer
  def send(self, s):
    self.writer.write(text_ws_msg(s))

class PrintStream:
  def __init__(self):
    pass
  def write(self, s):
    for frontend_writer in frontend_writers:
      frontend_writer.send(s) 

frontend_writers = []

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
        sys.stdout = PrintStream()

        exec(code)
        sys.stdout = sys.__stdout__

      except Exception as e:
        sys.stdout = sys.__stdout__

        print(f"Exception {e}")


    pending_sections = []

    if "loop" in tangled:
      code = "\n".join(tangled["loop"])
      try:
        sys.stdout = PrintStream()

        exec(code)
        sys.stdout = sys.__stdout__

      except Exception as e:
        sys.stdout = sys.__stdout__

        print(f"Exception {e}")

    if "loop" not in tangled or "".join(tangled["loop"]) == "":
      await message_received_event.wait()
      message_received_event.clear()

    await asyncio.sleep(0)

async def start_frontend_server(host='localhost', port=8090):
	server = await asyncio.start_server(on_frontend_connect, host, port)
	print(f"Front server started on {port}")
	async with server:
		await server.serve_forever()


async def on_frontend_connect(reader, writer):
	print("Connected to frontend")
	global frontend_writers
	frontend_writer_task = None
	  
	ws_mode = False
	while True:
		if ws_mode:
			readbuffer = []

			while True:
			  data = await reader.read(1)
			  fin = data[0] & 0x80 == 0x80
			  if data[0] & 0xF != 0:
			    opcode = data[0] & 0xF

			  data = await reader.read(1)
			  assert(data[0] & 0x80 == 0x80) # Client message must be masked

			  paylen = data[0] & 0x7F
			  if paylen == 126:
			    data = await reader.read(2)
			    paylen = struct.unpack("!H", data)[0]
			  elif paylen == 127:
			    data = await reader.read(8)
			    paylen = struct.unpack("!Q", data)[0]

			  masking = await reader.read(4)

			  payload = await reader.read(paylen)

			  for i in range(len(payload)):
			    readbuffer.append(payload[i] ^ masking[i%4])


			  if fin:
			    break

			if opcode == 0x1:
			  s = ""
			  for c in readbuffer:
			    s += chr(c)
			  print(s)
			else:
			  print(readbuffer)

		else:
			http_msg = []
			while True:
				try:
					line = await reader.readline()
				except Exception as e:
					http_msg.clear()
					break
				if len(line) == 0:
					http_msg.clear()
					break
				if line == b'\r\n':
					break
				http_msg.append(line[:-2])

			if len(http_msg) == 0:
				break
			first_line = http_msg[0]
			space = first_line.find(b' ')
			if space == -1:
				continue
			method = first_line[:space]
			rest = first_line[space+1:]

			if method == b'GET':
				space = rest.find(b' ')
				if space == -1:
					continue
				route = rest[:space]
				rest = rest[space+1:]

				if route == b'/':
					content = '<!doctype html><html><head><meta=charset=utf-8><title>blah</title></head><body><p>Hello world :)</p></body></html>'.encode('utf-8')
					msg_lines = [
						"HTTP/1.1 200 OK",
						f"Content-Length: {len(content)}",
						"Content-Type: text/html; charset=UTF-8",
					]
					await write_http_message(writer, msg_lines, content)
				elif route == b'/ws':
				  ws_keys = {}
				  for line in http_msg[1:]:
				    line = line.decode()
				    sep = line.find(':')
				    if sep == -1:
				      continue
				    key = line[:sep].strip()
				    val = line[sep+1:].strip()
				    ws_keys[key] = val
				    print(line)

				  assert(ws_keys["Upgrade"] == "websocket")
				  assert(ws_keys["Connection"] == "Upgrade")
				  ws_key = ws_keys["Sec-WebSocket-Key"]
				  assert(ws_keys["Sec-WebSocket-Version"] == "13")

				  hash = hashlib.sha1((ws_key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode())
				  base64hash = base64.b64encode(hash.digest())
				  msg_lines = [
				    "HTTP/1.1 101 Switching Protocols",
				    "Upgrade: websocket",
				    "Connection: Upgrade",
				    f"Sec-WebSocket-Accept: {base64hash.decode()}",
				  ]
				  await write_http_message(writer, msg_lines)
				  print("Websocket handshake done")

				  ws_mode = True

				  if frontend_writer_task is not None and frontend_writer_task in frontend_writers:
				    frontend_writers.remove(frontend_writer_task)

				  frontend_writer_task = FrontendWriter(writer)
				  frontend_writers.append(frontend_writer_task)



			else:
				print(f"Unknown method {method}")


	if frontend_writer_task is not None and frontend_writer_task in frontend_writers:
	  frontend_writers.remove(frontend_writer_task)

	writer.close()
	await writer.wait_closed()

async def write_http_message(writer, lines, body=None):
	for line in lines:
		writer.write((line + '\r\n').encode())
	writer.write(b'\r\n')
	if body is not None:
		writer.write(body)
	await writer.drain()

def text_ws_msg(txt):
  txt = txt.encode('utf-8')
  paylen = len(txt)
  msg = [0x81]
  if paylen <= 125:
    msg.append(paylen)
  elif paylen <= ((1 << 16) - 1):
    msg.append(126)
    for b in struct.pack("!H", paylen):
      msg.append(b)
  else:
    msg.append(127)
    for b in struct.pack("!Q", paylen):
      msg.append(b)

  msg += txt
  return struct.pack(f"{len(msg)}B", *msg)

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
	global message_received_event

	print("Client connected.")
	sections = {}

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

			blacklist = []
			for section_name in sections.keys():
				tangle_rec(section_name, sections, tangled, parent_section, blacklist)

			if name != "loop":
				pending_sections.append(name)

		elif msg["cmd"] == "killLoop":
		  sections.pop("loop", None)
		else:
			status = f"Unknown command {msg["cmd"]}"

		response = json.dumps({"status" : status}) + '\n'
		writer.write(response.encode())
		await writer.drain()

		message_received_event.set()
		await asyncio.sleep(0)

	print("Client disconnected.")
	writer.close()
	await writer.wait_closed()


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

