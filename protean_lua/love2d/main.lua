-- Generated using ntangle.nvim
local socket = require"socket"

local cached_tangle = {}

local sections = {}

local tangled = {}

local parent = {}

local pending_sections = {}

local server

local client_cos = {}

function parse_json(str)
  local p = 1
  local parse_co = coroutine.create(function()
    local whitespace

    local accept

    local expect

    local json_obj

    local json_str

    local finished

    local nextc

    local json_array

    local json_number

    local json_value
    local peek

    local parse_err

    whitespace = function()
      while p <= #str do
        if not str:sub(p,p):find("%s") then
          break
        end
        p = p + 1
      end
    end

    accept = function(sym)
      if str:sub(p,p + (#sym - 1)) == sym then
        p = p + #sym
        return true
      end
      return false
    end

    expect = function(sym)
      if str:sub(p,p + (#sym - 1)) == sym then
        p = p + #sym
        return true
      end
      parse_err(("expected %s but got %s"):format(p, sym, str:sub(p,p)))
    end

    function nextc()
      local c = str:sub(p,p)
      p = p + 1
      return c
    end

    peek = function()
      return str:sub(p,p)
    end

    function parse_err(msg)
      coroutine.yield(nil, ("(%d): %s"):format(p, msg))
    end

    function finished()
      return p > #str
    end

    json_obj = function()
      expect('{')
      local result = {}

      whitespace()

      if accept('}') then
        return result
      end

      while true do
        local key = json_str()

        whitespace()
        expect(':')

        result[key] = json_value()

        if accept('}') then
          return result
        end

        expect(',')
        whitespace()
      end
    end

    function json_array()
      expect('[')
      whitespace()

      local result = {}
      if accept(']') then
        return result
      end

      while true do
        table.insert(result, json_value())

        if accept(']') then
          return result
        end

        expect(',')
      end

      parse_err("end of input reached but no closing ']'")
    end

    function json_number()
      local l = p
      while l <= #str do
        local n = str:sub(p,l)
        if not tonumber(n) then
          if p == l then
            parse_err("expected number")
          else
            break
          end
        end
        l = l + 1
      end

      p = l
      return tonumber(str:sub(p,l-1))
    end

    function json_str()
      expect('"')

      local parts = {}

      while not finished() do
        if accept('"') then
          return table.concat(parts)
        elseif accept('\\') then
          if accept('"') then
            table.insert(parts, '"')
          elseif accept('\\') then
            table.insert(parts, '\\')
          elseif accept('/') then
            table.insert(parts, '/')
          elseif accept('b') then
            table.insert(parts, '\b')
          elseif accept('f') then
            table.insert(parts, '\f')
          elseif accept('n') then
            table.insert(parts, '\n')
          elseif accept('r') then
            table.insert(parts, '\r')
          elseif accept('t') then
            table.insert(parts, '\t')
          elseif accept('u') then
            parse_err("Unsupported unicode escape character")
          end

        else
          table.insert(parts, nextc())
        end
      end

      parse_err("end of input reached but no closing '\"'")
    end

    function json_value()
      whitespace()

      local c = peek()
      local result
      if c == '"' then
        result = json_str()
      elseif c == '-' or c:find("%d") then
        result = json_number()
      elseif c == '{' then
        result = json_obj()
      elseif c == '[' then
        result = json_array()
      elseif accept('true')  then
        result = true
      elseif accept('false')  then
        result = false
      elseif accept('null')  then
        result = nil
      else
        parse_err("Expected value")
      end
      whitespace()

      return result
    end

    return json_obj()
  end)

  local result, err = coroutine.resume(parse_co)

  if err then
    return err, p

  else
    return result, p
  end
end

function tangle(name, prefix, blacklist)
  prefix = prefix or ""
  blacklist = blacklist or {}

  if blacklist[name] then
    return {}
  end

  blacklist[name] = true

  if tangled[name] then
    return tangled[name]
  end

  if not sections[name] then
    return {}
  end

  local lines = {}
  for _, line in ipairs(sections[name]) do
    if string.match(line, "^%s*;[^;]") then
      local _, _, ref_prefix, ref_name = string.find(line, "^(%s*);(.+)$")
      ref_name = ref_name:match("^%s*(.+)%s*$")
      parent[ref_name] = name


      local ref_lines = tangle(ref_name, prefix .. ref_prefix, blacklist)
      for _, ref_line in ipairs(ref_lines) do
        table.insert(lines, ref_line)
      end


    else
      table.insert(lines, prefix .. line)
    end

  end
  blacklist[name] = nil

  tangled[name] = lines
  return tangled[name]
end

function has_parent(name, candidate)
  if name == candidate then
    return true
  end

  if not parent[name] then
    return false
  end
  return has_parent(parent[name], candidate)
end


local dt

function love.load()
  local port = 8089
  server = socket.bind("127.0.0.1", port)
  print(("Server running on port %d"):format(port))
  server:settimeout(0)

end

function love.update(dt)
  dt = dt
end

function love.draw()
  local client = server:accept()
  if client then
    print("Client connected!")
    client:settimeout(0)
    local client_co = coroutine.create(function(client)
      while true do
        coroutine.yield()
        local data, err = client:receive()
        if data then
          local msgs = {}
          local rest = data
          while #rest > 0 do
            local msg
            msg, p = parse_json(rest)

            if type(msg) == "string" then 
              break 
            end

            rest = rest:sub(p)
            table.insert(msgs, msg)
          end

          local msg = msgs[1]
          if msg["cmd"] == "execute" then
            msg_data = msg['data']
            local name = msg_data['name']
            local lines = msg_data['lines']
            sections[name] = lines

            tangled = {}
            parent = {}

            for name, _ in pairs(sections) do
              tangle(name)
            end

            if msg_data['execute'] then
              if not has_parent(name, "loop") then
                table.insert(pending_sections, name)
              end

            end

            cached_tangle = {}

            client:send([[{"status": "Done"}]] .. "\n")


          elseif msg["cmd"] == "killLoop" then
            sections["loop"] = nil
            tangled["loop"] = nil
            print("Loop killed")

          else
            client:send([[{"status": "Unsupported command ]] .. msg['cmd'] .. [["}]] .. "\n")
          end

        elseif err == "closed" then
          print("Client disconnected.")
          break
        end
      end
    end)

    coroutine.resume(client_co, client)
    table.insert(client_cos, client_co)

  end

  local i = 1
  while i <= #client_cos do
    coroutine.resume(client_cos[i], client)
    if coroutine.status(client_cos[i]) == "dead" then
      table.remove(client_cos, i)
    else
      i = i + 1
    end
  end
  if #pending_sections > 0 then
    for _, name in ipairs(pending_sections) do
      if not cached_tangle[name] then
        local lines = tangled[name]
        local f, err = loadstring(table.concat(lines, "\n"))
        if not f then
          print("Compile error (" .. name .. "): " .. err)
          sections[name] = nil
          tangled[name] = nil
          cached_tangle[name] = nil
        else
          cached_tangle[name] = f
        end

      end

      if cached_tangle[name] then
        local succ,err = pcall(cached_tangle[name])
        if not succ then
          print("Execute error (" .. name .. "): " .. err)
          sections[name] = nil
          tangled[name] = nil
          cached_tangle[name] = nil
        end
      end
    end
    pending_sections = {}
  end

  if tangled['loop'] then
    local name = "loop"
    if not cached_tangle[name] then
      local lines = tangled[name]
      local f, err = loadstring(table.concat(lines, "\n"))
      if not f then
        print("Compile error (" .. name .. "): " .. err)
        sections[name] = nil
        tangled[name] = nil
        cached_tangle[name] = nil
      else
        cached_tangle[name] = f
      end

    end

    if cached_tangle[name] then
      local succ,err = pcall(cached_tangle[name])
      if not succ then
        print("Execute error (" .. name .. "): " .. err)
        sections[name] = nil
        tangled[name] = nil
        cached_tangle[name] = nil
      end
    end
  end

end

