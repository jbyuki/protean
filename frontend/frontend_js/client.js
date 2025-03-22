window.onload = () =>
{
  const socket = new WebSocket("ws://localhost:8091/ws");

  socket.onopen = (event) => {
    console.log('opened ws connection')
  };

  socket.onclose = (event) => {
    console.log('closed ws connection')
  };

  socket.onerror = (event) => {
    console.error(event);
  };

  socket.onmessage = (event) => {
  };
}

