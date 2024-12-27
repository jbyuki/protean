import asyncio
import json

async def start_client(host = "localhost", port=8089):
	reader, writer = await asyncio.open_connection(host, port)

	# message = json.dumps({"cmd" : "execute", "data" : {'name': "main loop", 'lines': [ "import ntpy", "while True:", "\t; print hello", "\tntpy.sleep()" ]}}) + '\n'
	# writer.write(message.encode())
	# await writer.drain()

	message = json.dumps({"cmd" : "execute", "data" : {'name': "print hello", 'lines': [ "print('hello')" ]}}) + '\n'
	writer.write(message.encode())
	await writer.drain()

	message = json.dumps({"cmd" : "execute", "data" : {'name': "main", 'lines': [ "; print hello" ]}}) + '\n'
	writer.write(message.encode())
	await writer.drain()

	message = json.dumps({"cmd" : "execute", "data" : {'name': "print hello", 'lines': [ "print('hi')" ]}}) + '\n'
	writer.write(message.encode())
	await writer.drain()

	writer.close()
	await writer.wait_closed()
	print("Client closed")

