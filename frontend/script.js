var previous_task_id = null;
var previous_cell;

window.onload = () =>
{
  const status = document.getElementById("connection-status");
  const p = status.firstElementChild;
  p.textContent = "disconnected";
  p.style.color = "#444";
  const kernel_status = document.getElementById("kernel-status");
  kernel_status.style.display = "none";


  const socket = new WebSocket("ws://localhost:8090/ws");

  socket.onopen = (event) => {
    const status = document.getElementById("connection-status");
    const p = status.firstElementChild;
    p.textContent = "connected";
    p.style.color = "#444";
    const kernel_status = document.getElementById("kernel-status");
    kernel_status.style.display = "block";


  };

  socket.onclose = (event) => {
    const status = document.getElementById("connection-status");
    const p = status.firstElementChild;
    p.textContent = "disconnected";
    p.style.color = "#444";
    const kernel_status = document.getElementById("kernel-status");
    kernel_status.style.display = "none";


  };

  socket.onclose = (event) => {
    const status = document.getElementById("connection-status");
    const p = status.firstElementChild;
    p.textContent = "error";
    p.style.color = "#b66";
    console.log(event);
    const kernel_status = document.getElementById("kernel-status");
    kernel_status.style.display = "none";


  };

  socket.onmessage = (event) => {
    console.log(event);
    if(typeof event.data == "string")
    {
      const msg = JSON.parse(event.data);

      if(msg.cmd == "output")
      {
        const task_id = msg.data.task_id;

        if(task_id === previous_task_id)
        {
          previous_cell.textContent += msg.data.text;
        }

        else
        {
          const output = document.getElementById("output");

          const today = new Date();
          const time_iso = today.toLocaleString();

          const cell = document.createElement("div");
          cell.classList.add("cell");

          const cell_date = document.createElement("div");
          cell_date.classList.add("cell-date");
          cell_date.textContent = time_iso
          cell.appendChild(cell_date);

          const cell_output = document.createElement("div");
          cell_output.classList.add("cell-output");
          cell.appendChild(cell_output);

          cell_output.textContent = msg.data.text;

          previous_task_id = task_id;
          previous_cell = cell_output;

          output.appendChild(cell);
        }

      }

    }

  };

};

