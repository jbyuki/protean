const net = require('node:net');

var execute_scheduled = false;

var sections = {};

var tangled = {};

var parent_section = {};

var pending_sections = [];

function executor()
{
  execute_scheduled = true;

  for(const name of pending_sections)
  {
    var code;
    if(name in tangled)
    {
      code = tangled[name].join("\n");
    }
    else
    {
      continue;
    }

    try
    {
      eval(code);
    }
    catch(error)
    {
      console.log(error);
    }

  }

  pending_sections = [];

  var code_loop = "";
  if("loop" in tangled)
  {
    const name = "loop";
    code_loop = tangled["loop"].join("\n");
    try
    {
      eval(code_loop);
    }
    catch(error)
    {
      console.log(error);
    }
  }

  if(code_loop.length > 0)
  {
    execute_scheduled = true;
    setTimeout(executor, 0);
  }
}

function tangle_rec(name, sections, tangled, parent_section, blacklist, prefix)
{
  if(blacklist.indexOf(name) != -1)
  {
    return [];
  }

  blacklist.push(name);

  if(!(name in sections))
  {
    return [];
  }

  if(name in tangled)
  {
    return tangled[name];
  }

  var lines = [];
  for(var line of sections[name])
  {
    if(/\s*;[^;].*/.test(line))
    {
      const matches = /(\s*);([^;].*)/;
      const new_prefix = matches[1];
      const ref_name = matches[2].trim();
      if(!(ref_name in parent_section))
      {
        parent_section[ref_name] = [];
      }

      if(!(name in parent_section[ref_name]))
      {
        parent_section[ref_name].push(name);
      }


      const ref_lines = tangle_rec(ref_name, sections, tangled, parent_section, blacklist, prefix + new_prefix);
      if(ref_lines.length > 0)
      {
        for(const ref_line of ref_lines)
        {
          lines.push(prefix + new_prefix + ref_line);
        }
      }

    }

    else
    {
      lines.push(line);
    }

  }

  tangled[name] = lines;
  blacklist.pop();

  return lines;
}


const server = net.createServer((c) => {
  console.log('client connected');
  c.on('data', (data) => {
    const msg = JSON.parse(data.toString());

    const status = "Done";
    if(msg['cmd'] == "execute")
    {
    	const msg_data = msg["data"];

    	const name = msg_data['name'];
    	const lines = msg_data["lines"];
    	sections[name] = lines;

    	tangled = {};
    	parent_section = {};


    	for(const section_name in sections)
    	{
    	  blacklist = [];
    	  tangle_rec(section_name, sections, tangled, parent_section, blacklist, "");
    	}

    	if(msg_data['execute'])
    	{
    	  var has_loop_parent = false;
    	  var open = [name];
    	  var closed = new Set([]);
    	  closed.add(name);
    	  while(open.length > 0)
    	  {
    	    var current = open.pop();
    	    if(current == "loop")
    	    {
    	      has_loop_parent = true;
    	      break;
    	    }

    	    if(current in parent_section)
    	    {
    	      for(const parent in parent_section[current])
    	      {
    	        if(!closed.has(parent))
    	        {
    	          open.push(parent);
    	          closed.add(current);
    	        }
    	      }
    	    }
    	  }
    	  if(!has_loop_parent)
    	  {
    	    pending_sections.push(name);
    	  }
    	}

    }

    c.write(JSON.stringify({"status": status}) + "\n");
    if(!execute_scheduled)
    {
      execute_scheduled = true;
      setTimeout(executor, 0);
    }

  });
  c.on('end', () => {
    console.log('client disconnected');
  });
});

server.on('error', (err) => {
  throw err;
});

const port = 8089;
server.listen(port, () => {
  console.log(`Server listening on port ${port}`);
});


