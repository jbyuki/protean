const net = require('node:net');

const ws = require("ws");

const http = require('node:http');

const fs = require('fs');
const path = require('path');

var ws_clients = [];


const server = net.createServer((c) => {
  console.log('client connected');
  c.on('data', (data) => {
    const msg = JSON.parse(data.toString());

    for(var i=0; i<ws_clients.length; i++)
    {
      ws_clients[i].send(data.toString());
    }

    c.write(JSON.stringify({"status": "Done"}) + "\n");

  });
  c.on('end', () => {
    console.log('client disconnected');
    c.end();
  });

  c.on('error',function(err){
    throw err;
  });

  c.on('close',function(error){
    console.log('client closed');
  });
}, {  });

server.on('error', (err) => {
  throw err;
});

const wss = new ws.WebSocketServer({port: 8091});

wss.on('connection', (ws) => {
  console.log('websocket client connected');
  ws_clients.push(ws);

  ws.on('error', console.error);
  ws.on('message', (data) => {
    const ws_msg = JSON.parse(data);
    console.log(ws_msg);
    if(ws_msg['cmd'] == 'fileRead')
    {
      const filename = ws_msg['path'];
      fs.readFile(filename, 'utf8', (err, content) => {
        if(!err && content)
        {
          ws.send(JSON.stringify({
            cmd: 'fileRead',
            path: filename,
            content: content,
          }));

        }
        else
        {
          ws.send(JSON.stringify({
            cmd: 'fileRead',
            path: filename,
            content: null,
          }));
        }
      });
    }


  });
  ws.on('close', () => {
    console.log('websocket client disconnected');
    const idx = ws_clients.indexOf(ws);
    if(idx != -1)
    {
      ws_clients.splice(idx, 1);
    }

  });
});

const port = 8089;
server.listen(port, () => {
  console.log(`Server listening on port ${port}`);
});

const frontend_server = http.createServer((req, res) => {
  var content = "";
  var content_type = "";
  var url = req.url;
  if(url == '/')
  {
    url = '/index.html';
  }

  const filepath = path.join(path.dirname(path.dirname(__filename)), 'frontend', 'frontend_js', url);
  console.log(url);
  const ext = path.extname(filepath);

  fs.readFile(filepath, 'utf8', (err, data) => {
    if(!err && data)
    {
      var content_type = 'text/plain';
      if(ext == '.html')
      {
        content_type = 'text/html';
      }
      else if(ext == '.js')
      {
        content_type = 'text/javascript';
      }
      else if(ext == '.css')
      {
        content_type = 'text/css';
      }
      res.writeHead(200, { 
        'Content-Type': content_type,
        'Access-Control-Allow-Origin': 'http://localhost:8090',
        'Access-Control-Allow-Methods': 'GET,PUT,POST,DELETE'
      });

      res.end(data);

    }
  });

});

const frontend_port = 8090;
frontend_server.listen(frontend_port, () => {
  console.log(`Frontend Server listening on port ${frontend_port}`);
});


