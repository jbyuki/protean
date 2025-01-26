const socket = new WebSocket("ws://localhost:8090/ws");
socket.onopen = (event) => {
  socket.send("Hello sever!");
};
