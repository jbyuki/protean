var previous_task_id = null;
var previous_cell;

var status_animation = null;

var idle_request = null;

var endAnimTime = performance.now();

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
          previous_cell.innerText += msg.data.text;
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

          cell_output.innerText = msg.data.text;

          previous_task_id = task_id;
          previous_cell = cell_output;

          output.appendChild(cell);

        }

        window.scrollTo(0, document.body.scrollHeight);

      }

      else if(msg.cmd == "exception")
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
        cell_output.classList.add("cell-exception");
        cell.appendChild(cell_output);

        var code = "";
        for(let i=0; i<msg.data.lines.length; i++)
        {
          code += `${i+1}  ${msg.data.lines[i]}\n`;
        }

        cell_output.innerText = code + '\n' + msg.data.text;

        output.appendChild(cell);

        window.scrollTo(0, document.body.scrollHeight);

      }

      else if(msg.cmd == "svg_output")
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

        const cell_download = document.createElement("div");
        cell_download.classList.add("cell-download");

        const p = document.createElement("p");
        p.innerText = "Download";
        cell_download.appendChild(p);
        p.onclick = () => {
          const blob = new Blob([svg_content], { type: "image/svg+xml" });
          const url = URL.createObjectURL(blob);
          const a = document.createElement("a");
          document.body.appendChild(a);
          a.style = "display: none";
          a.href = url;
          a.download = `figure_${new Date().toJSON()}.svg`;
          a.click();
          URL.revokeObjectURL(url);
        };

        cell.appendChild(cell_download);

        var svg_content = msg.data.content;
        const first_index = svg_content.indexOf('<svg');
        svg_content = svg_content.slice(first_index);

        cell_output.innerHTML = svg_content;

        output.appendChild(cell);

        window.scrollTo(0, document.body.scrollHeight);

      }

      else if(msg.cmd == "notify")
      {
        if(msg.data.status == "running")
        {
          var section_name = msg.data.section;
          if(section_name.length > 16)
          {
            section_name = section_name.substr(0,16) + "...";
          }

          if(status_animation !== null)
          {
            clearInterval(status_animation);
            status_animation = null;
          }

          if(idle_request !== null)
          {
            clearInterval(idle_request);
            idle_request = null;
          }


          const kernel_status = document.getElementById("kernel-status").firstElementChild;
          kernel_status.textContent = "";

          status_animation = setInterval((kernel_status, section_name) => {
            const curLength = kernel_status.textContent.length;
            if(curLength < section_name.length)
            {
              kernel_status.textContent += section_name[curLength];
            }
            else
            {
              clearInterval(status_animation);
              status_animation = null;
              endAnimTime = performance.now();

            }
          }, 15, kernel_status, section_name);

        }

        else if(msg.data.status == "idle")
        {
          if(idle_request !== null)
          {
            clearInterval(idle_request);
            idle_request = null;
          }


          idle_request = setInterval(() => {
            const nowTime = performance.now();

            if(status_animation === null && nowTime - endAnimTime > 1000)
            {
              const kernel_status = document.getElementById("kernel-status").firstElementChild;
              kernel_status.textContent = "idle";
              clearInterval(idle_request);
              idle_request = null;
            }

          }, 100);

        }

      }

    }

  };

};

