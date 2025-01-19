import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ntpy'))
import server
import threading
import random
import test_client

import asyncio

async def main():
	executor_task = asyncio.create_task(server.start_executor())
	server_task = asyncio.create_task(server.start_server())
	asyncio.create_task(test_client.start_client())
	await asyncio.sleep(1)
	executor_task.cancel()
	server_task.cancel()
	try:
		await server_task
	except asyncio.CancelledError:
		pass


asyncio.run(main())

print("hello")

