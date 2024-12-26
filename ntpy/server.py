import asyncio
import json

async def start_server(host='localhost', port=8089):
	server = await asyncio.start_server(handle_echo, host, port)
	print(f"Server started on {port}")
	async with server:
		await server.serve_forever()

async def handle_echo(reader, writer):
	data = await reader.read(100)
	obj = json.loads(data)
	print(f"Received: {obj}")
	writer.close()
	await writer.wait_closed()

