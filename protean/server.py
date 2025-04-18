from pathlib import Path

import hashlib
import base64

import struct

import matplotlib

from protean_matplotlib_backend import flush_figures

import io
import matplotlib.pyplot as plt

import darkdetect

import sys
from io import StringIO

import traceback

import re

import asyncio
import json

from sympy import latex

class FrontendWriter:
  def __init__(self, writer):
    self.writer = writer
  def send(self, s):
    self.writer.write(text_ws_msg(s))
  async def drain(self):
    await self.writer.drain()

class PrintStream:
  def __init__(self):
    pass
  def write(self, s):
    global frontend_writers
    conv = Ansi2HTMLConverter()
    s = conv.convert(s, full=False)
    for frontend_writer in frontend_writers:
      frontend_writer.send(msg_output_txt(s)) 

  def flush(self):
    pass

frontend_writers = []

task_id = 0

import time
from ansi2html import Ansi2HTMLConverter

sent_sections = False

loop_last_run = False

sections = {}

tangled = {}

pending_sections = []

async def start_executor():
  global pending_sections
  global tangled

  global message_received_event

  global frontend_writers

  global sent_sections

  global loop_last_run 

  while True:
    for name in pending_sections:
      if name in tangled:
        code = "\n".join(tangled[name])
      else:
        continue

      try:
        sys.stdout = PrintStream()

        exec(code,  globals())
        sys.stdout = sys.__stdout__

        new_figs = flush_figures()

        if len(new_figs) > 0:
          svgs = []
          for fig in new_figs:
            f = io.StringIO()
            plt.tight_layout()
            fig.figure.savefig(f, transparent=True)
            svgs.append(f.getvalue())

          for frontend_writer in frontend_writers:
            for svg in svgs:
              frontend_writer.send(msg_svg_output(svg))
              await frontend_writer.drain()


        for frontend_writer in frontend_writers:
          frontend_writer.send(msg_notify_no_exception()) 
      except Exception as e:
        sys.stdout = sys.__stdout__

        print(f"Exception {e}")
        exc_msg = traceback.format_exc()
        for frontend_writer in frontend_writers:
          frontend_writer.send(msg_exception(exc_msg, tangled[name]))
          await frontend_writer.drain()
        new_figs = flush_figures()



    if sent_sections:
      for frontend_writer in frontend_writers:
        frontend_writer.send(msg_notify_idle()) 
        await frontend_writer.drain()
      sent_sections = False

    pending_sections = []

    if "loop" in tangled:
      name = "loop"
      code = "\n".join(tangled["loop"])
      try:
        if not loop_last_run:
          for frontend_writer in frontend_writers:
            frontend_writer.send(msg_notify_loop_run()) 
          loop_last_run = True

        sys.stdout = PrintStream()

        exec(code,  globals())
        sys.stdout = sys.__stdout__

        new_figs = flush_figures()

      except Exception as e:
        sys.stdout = sys.__stdout__

        print(f"Exception {e}")
        exc_msg = traceback.format_exc()
        for frontend_writer in frontend_writers:
          frontend_writer.send(msg_exception(exc_msg, tangled[name]))
          await frontend_writer.drain()
        del tangled["loop"]
        global sections
        del sections["loop"]
        if loop_last_run:
          for frontend_writer in frontend_writers:
            frontend_writer.send(msg_notify_loop_stop()) 
          loop_last_run = False

        new_figs = flush_figures()


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

			end_con = False
			while True:
			  data = await reader.read(1)
			  if len(data) == 0:
			    end_con = True
			    break

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
			if end_con:
			  break

			if opcode == 0x1:
			  s = ""
			  for c in readbuffer:
			    s += chr(c)

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

				if route == b'/' or route == b'/script.js' or route == b'/styles.css' or route == b'/popup_latex.html':
					filename = route[1:].decode('utf-8')
					if filename == "":
						filename = "index.html"
					path = Path(__file__)
					f = open(path.parent.parent / "frontend" / filename, "r")
					content = f.read().encode('utf-8')

					content_type = ""
					if filename == 'index.html':
						content_type = 'text/html'
					elif filename == 'script.js':
						content_type = 'text/javascript'
					elif filename == 'styles.css':
						content_type = 'text/css'
					else:
						ext = filename.split('.')[1]
						content_type = f'text/{ext}'

					msg_lines = [
						"HTTP/1.1 200 OK",
						f"Content-Length: {len(content)}",
						f"Content-Type: {content_type}; charset=UTF-8",
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
					print(f"Unknown route {route.decode('utf-8')}")

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

def msg_log(text):
  msg = {}
  msg["cmd"] = "log"
  msg["data"] = { "text": text }
  return json.dumps(msg)

def log_debug(*text):
  for frontend_writer in frontend_writers:
    frontend_writer.send(msg_log(" ".join([str(t) for t in text]))) 
def msg_svg_output(svg_content):
  global task_id

  msg = {}
  msg["cmd"] = "svg_output"
  msg["data"] = { "task_id": task_id, "content": svg_content }
  return json.dumps(msg)

def msg_output_txt(txt):
  global task_id

  msg = {}
  msg["cmd"] = "output"
  msg["data"] = { "task_id": task_id, "text": txt }
  return json.dumps(msg)

def msg_exception(txt, lines):
  global task_id

  msg = {}
  msg["cmd"] = "exception"
  msg["data"] = { "task_id": task_id, "text": txt, "lines": lines }
  return json.dumps(msg)

def msg_notify_running(section_name):
  msg = {}
  msg["cmd"] = "notify"
  msg["data"] = { "status": "running", "section": section_name }
  global last_idle
  last_idle = False
  return json.dumps(msg)

def msg_notify_idle():
  msg = {}
  msg["cmd"] = "notify"
  msg["data"] = { "status": "idle" }
  return json.dumps(msg)

def msg_notify_loop_run():
  msg = {}
  msg["cmd"] = "notify"
  msg["data"] = { "status": "loop run" }
  global loop_last_run
  loop_last_run = True
  return json.dumps(msg)

def msg_notify_loop_stop():
  msg = {}
  msg["cmd"] = "notify"
  msg["data"] = { "status": "loop stop" }
  global loop_last_run
  loop_last_run = False
  return json.dumps(msg)

def msg_notify_no_exception():
  msg = {}
  msg["cmd"] = "notify"
  msg["data"] = { "status": "no exception" }
  return json.dumps(msg)

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
	matplotlib.use('module://protean_matplotlib_backend')

	if darkdetect.isDark():
	  params = {"ytick.color" : "w",
	            "xtick.color" : "w",
	            "axes.titlecolor" : "w",
	            "axes.labelcolor" : "w",
	            "axes.edgecolor" : "w"}
	else:
	  params = {}
	plt.rcParams.update(params)
	server = await asyncio.start_server(on_connect, host, port)
	print(f"Server started on {port}")
	async with server:
		await server.serve_forever()

async def on_connect(reader, writer):
	global message_received_event

	print("Client connected.")
	global sent_sections

	global loop_last_run 

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

			for frontend_writer in frontend_writers:
			  frontend_writer.send(msg_notify_running(name)) 
			sent_sections = True

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

			global task_id
			task_id = task_id + 1


		elif msg["cmd"] == "killLoop":
		  sections.pop("loop", None)
		  del tangled["loop"]
		  if loop_last_run:
		    for frontend_writer in frontend_writers:
		      frontend_writer.send(msg_notify_loop_stop()) 
		    loop_last_run = False

		elif msg["cmd"] == "toggleBackend":
		  backend_name = matplotlib.get_backend()
		  if backend_name == "module://protean_matplotlib_backend":
		    matplotlib.rcParams.update(matplotlib.rcParamsDefault)
		    matplotlib.use("qtagg")
		  else:
		    matplotlib.use('module://protean_matplotlib_backend')

		    if darkdetect.isDark():
		      params = {"ytick.color" : "w",
		                "xtick.color" : "w",
		                "axes.titlecolor" : "w",
		                "axes.labelcolor" : "w",
		                "axes.edgecolor" : "w"}
		    else:
		      params = {}
		    plt.rcParams.update(params)
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
  global task_id

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

