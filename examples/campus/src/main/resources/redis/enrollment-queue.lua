-- 모든 키는 같은 Redis Cluster hash slot {enrollment}을 사용한다.
local action, user, ticket = ARGV[1], ARGV[2], ARGV[3]
local now = tonumber(ARGV[4])
local function remove(id)
  local owner = redis.call('HGET', KEYS[2], id)
  if owner and redis.call('HGET', KEYS[6], owner) == id then redis.call('HDEL', KEYS[6], owner) end
  redis.call('HDEL', KEYS[2], id)
  redis.call('ZREM', KEYS[1], id)
  redis.call('ZREM', KEYS[3], id)
end
for _, id in ipairs(redis.call('ZRANGEBYSCORE', KEYS[3], '-inf', now)) do remove(id) end
if action == 'join' then
  local existing = redis.call('HGET', KEYS[6], user)
  if existing then ticket = existing
  else
    if redis.call('ZCARD', KEYS[3]) >= 500 then return {'full', '0', ''} end
    redis.call('HSET', KEYS[2], ticket, user)
    redis.call('HSET', KEYS[6], user, ticket)
    redis.call('ZADD', KEYS[1], redis.call('INCR', KEYS[5]), ticket)
  end
  redis.call('ZADD', KEYS[3], now + 120000, ticket)
  return {'waiting', '0', ticket}
end
if redis.call('HGET', KEYS[2], ticket) ~= user then return {'expired', '0', ticket} end
local active = redis.call('GET', KEYS[4])
if action == 'cancel' and active == ticket .. ':running' then return {'running', '0', ticket} end
if action == 'release' or action == 'cancel' then
  if active == ticket or active == ticket .. ':running' then redis.call('DEL', KEYS[4]) end
  remove(ticket)
  return {'released', '0', ticket}
end
if action == 'claim' then
  if active ~= ticket then return {'waiting', '0', ticket} end
  redis.call('SET', KEYS[4], ticket .. ':running', 'PX', 60000)
  return {'admitted', '0', ticket}
end
redis.call('ZADD', KEYS[3], now + 120000, ticket)
if active == ticket then return {'admitted', '0', ticket} end
if active == ticket .. ':running' then return {'running', '0', ticket} end
local rank = redis.call('ZRANK', KEYS[1], ticket)
if not rank then remove(ticket); return {'expired', '0', ticket} end
if not active and rank == 0 then
  redis.call('ZREM', KEYS[1], ticket)
  redis.call('SET', KEYS[4], ticket, 'PX', 60000)
  return {'admitted', '0', ticket}
end
return {'waiting', tostring(rank + 1), ticket}
