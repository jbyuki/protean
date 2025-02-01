const socket = new WebSocket("ws://localhost:8090/ws");
socket.onopen = (event) => {
  socket.send("Hello sever!");
};
socket.onmessage = (event) => {
  console.log(event.data);
};

window.onload = () => {
  const div = document.getElementById("output");
  for(var i=0; i<100; ++i)
  {
    const para = document.createElement("p");
    para.textContent = "hello world";
    div.appendChild(para);
  }

  const filemenu = document.getElementById("file_menu");
  filemenu.onmousedown = () => {

  };
};
