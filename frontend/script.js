var previous_task_id = null;
var previous_cell;

var status_animation = null;

var idle_request = null;

var endAnimTime = performance.now();

var loop_running = false;

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
          previous_cell.innerHTML += msg.data.text;
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

          cell_output.innerHTML = msg.data.text;

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

        cell_output.innerHTML = code + '\n' + msg.data.text;

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
          const max_section_name_length = 32;
          if(section_name.length > max_section_name_length )
          {
            section_name = section_name.substr(0,max_section_name_length) + "...";
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
          kernel_status.style.color = "#888";

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
              if(loop_running)
              {
                kernel_status.textContent = "loop";
                kernel_status.style.color = "#888";
              }
              else
              {
                kernel_status.textContent = "idle";
                kernel_status.style.color = "#444";
              }

              clearInterval(idle_request);
              idle_request = null;
            }

          }, 100);

        }

        else if(msg.data.status == "loop run")
        {
          const kernel_status = document.getElementById("kernel-status").firstElementChild;
          loop_running = true;
          kernel_status.textContent = "loop";
          kernel_status.style.color = "#888";
        }

        else if(msg.data.status == "loop stop")
        {
          const kernel_status = document.getElementById("kernel-status").firstElementChild;
          loop_running = false;
          kernel_status.textContent = "idle";
          kernel_status.style.color = "#444";
        }

        else if(msg.data.status == "no exception")
        {
          var exception_cells = document.querySelectorAll(".cell-exception");
          for(var i=0; i<exception_cells.length; i++)
          {
            const div_exception = exception_cells[i].parentElement;
            div_exception.remove();
          }
        }

      }

      else if(msg.cmd == "log")
      {
        console.log("SERVER: " + msg.data.text);
      }

    }

  };

};

