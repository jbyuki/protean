var socket;

var sections = {};

var tangled = {};

var parent = {};

var pending_sections = [];

var execute_loop = false;

var sleeping = true;

var readfile_cb = {};

var readfile;

function tangle(name, prefix="", blacklist=[])
{
  if(blacklist.indexOf(name) != -1)
  {
    return [];
  }

  blacklist.push(name);

  if(name in tangled)
  {
    return tangled[name];
  }

  if(!(name in sections))
  {
    return [];
  }

  const lines = [];
  for(const line of sections[name])
  {
    if(/^\s*;[^;].*/.test(line))
    {
      const matches = line.match(/(\s*);([^;].*)/);
      const ref_prefix = matches[1];
      const ref_name = matches[2].trim();

      parent[ref_name] = name;

      const ref_lines = tangle(ref_name, prefix + ref_prefix, blacklist);
      if(ref_lines.length > 0)
      {
        for(const ref_line of ref_lines)
        {
          lines.push(prefix + ref_prefix + ref_line);
        }
      }

    }

    else
    {
      lines.push(prefix + line);
    }

  }
  blacklist.pop();

  tangled[name] = lines;
  return tangled[name];
}

function get_root(name)
{
  if(!(name in parent))
  {
    return name;
  }
  return get_root(parent[name]);
}

function execute()
{
  for(const name of pending_sections)
  {
    const code = tangled[name].join('\n');

    try
    {
      eval(`(async () => { ${code} })()`);
    }
    catch(err)
    {
      console.error(err);
    }

  }


  pending_sections = [];

  if(execute_loop && ("loop" in tangled))
  {
    const name = "loop";
    const code = tangled[name].join('\n');

    try
    {
      eval(`(async () => { ${code} })()`);
    }
    catch(err)
    {
      console.error(err);
      execute_loop = false;
    }

  }

  if(execute_loop && ("loop" in tangled))
  {
    requestAnimationFrame(execute);
  }

  else
  {
    sleeping = true;
  }

}

async function importfile(filename)
{
  const content = await readfile(filename);
  console.assert(content !== null);
  try 
  {
    eval(content);
  }
  catch(err)
  {
    console.error(err);
  }
}
function readfile(filename)
{
  const ws_msg = {
    cmd: 'fileRead',
    path: filename
  };

  const promise = new Promise((resolve) => {
    readfile_cb[filename] = (content) => {
      resolve(content);
    };
  });

  socket.send(JSON.stringify(ws_msg));
  return promise;
}

window.onload = () =>
{
  socket = new WebSocket("ws://localhost:8091/ws");

  socket.onopen = (event) => {
  };

  socket.onclose = (event) => {
    console.log('closed ws connection')
  };

  socket.onerror = (event) => {
    console.error(event);
  };

  socket.onmessage = (event) => {
    const msg = JSON.parse(event.data);

    if(msg['cmd'] == 'execute')
    {
      const data = msg['data'];
      const name = data['name'];
      const lines = data['lines'];

      sections[name] = lines

      tangled = {};
      parent = {};

      for(const name in sections)
      {
        tangle(name);
      }

      if(data['execute'])
      {
        const root = get_root(name);
        if(root != "loop")
        {
          pending_sections.push(name);
        }

        else
        {
          execute_loop = true;
        }
        if(sleeping)
        {
          sleeping = false;
          requestAnimationFrame(execute);
        }

      }
    }

    else if(msg['cmd'] == 'killLoop')
    {
      console.log('loop killed');
      execute_loop = false;
    }
    else if(msg['cmd'] == 'fileRead')
    {
      for(const fn in readfile_cb)
      {
        if(fn == msg['path'])
        {
          readfile_cb[fn](msg['content']);
          break;
        }
      }
    }
  };

}

