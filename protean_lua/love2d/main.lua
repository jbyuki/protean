-- Generated using ntangle.nvim
local socket = require"socket"

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

          for _, msg in ipairs(msgs) do
            if msg["cmd"] == "execute" then
            end
          end
        elseif err == "closed" then
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
end

