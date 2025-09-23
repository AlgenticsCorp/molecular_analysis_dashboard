-- Rate limiting module using token bucket algorithm
-- Implements configurable rate limiting with Redis backend

local cjson = require "cjson"
local init = require "gateway.init"

local _M = {}

-- Get rate limit key for a request
function _M.get_rate_limit_key(identifier, window_type)
    window_type = window_type or "default"
    return "rate_limit:" .. window_type .. ":" .. identifier
end

-- Apply rate limit using token bucket algorithm
function _M.apply_rate_limit(identifier, limit, window, burst)
    limit = limit or init.config.default_rate_limit
    window = window or init.config.rate_limit_window
    burst = burst or (limit / 2)

    -- Try local cache first for better performance
    local cache = ngx.shared.rate_limit_cache
    local cache_key = _M.get_rate_limit_key(identifier, "cache")

    local current_count, flags = cache:get(cache_key)
    local now = ngx.time()

    if not current_count then
        -- Initialize counter
        current_count = 1
        cache:set(cache_key, current_count, window)
    else
        -- Increment counter
        current_count = cache:incr(cache_key, 1)
        if not current_count then
            -- Counter expired, reset
            current_count = 1
            cache:set(cache_key, current_count, window)
        end
    end

    -- Check if limit exceeded
    if current_count > (limit + burst) then
        return false, current_count, limit
    end

    return true, current_count, limit
end

-- Apply rate limit with Redis backend (more accurate but slower)
function _M.apply_redis_rate_limit(identifier, limit, window, burst)
    local red, err = init.get_redis()
    if not red then
        ngx.log(ngx.WARN, "Redis unavailable for rate limiting, allowing request: ", err)
        return true, 0, limit
    end

    local key = _M.get_rate_limit_key(identifier, "redis")
    local now = ngx.time()

    -- Use Redis pipeline for atomic operations
    red:init_pipeline()
    red:incr(key)
    red:expire(key, window)
    local results, err = red:commit_pipeline()

    init.close_redis(red)

    if not results then
        ngx.log(ngx.ERR, "Rate limit Redis error: ", err)
        return true, 0, limit -- Allow on Redis error
    end

    local current_count = results[1]

    -- Check if limit exceeded
    if current_count > (limit + (burst or 0)) then
        return false, current_count, limit
    end

    return true, current_count, limit
end

-- Get rate limit identifier from request
function _M.get_identifier()
    -- Try to use authenticated user first
    local user_id = ngx.var.http_x_user_id
    if user_id and user_id ~= "" and user_id ~= "anonymous" then
        return "user:" .. user_id
    end

    -- Fall back to IP address
    return "ip:" .. ngx.var.remote_addr
end

-- Set rate limit headers
function _M.set_rate_limit_headers(current, limit, window)
    ngx.header["X-RateLimit-Limit"] = tostring(limit)
    ngx.header["X-RateLimit-Remaining"] = tostring(math.max(0, limit - current))
    ngx.header["X-RateLimit-Reset"] = tostring(ngx.time() + window)
end

-- Handle rate limit exceeded
function _M.rate_limit_exceeded(current, limit)
    ngx.status = 429
    ngx.header.content_type = "application/json"
    ngx.header["Retry-After"] = tostring(init.config.rate_limit_window)

    _M.set_rate_limit_headers(current, limit, init.config.rate_limit_window)

    ngx.say(cjson.encode({
        error = "Rate limit exceeded",
        message = "Too many requests",
        limit = limit,
        current = current,
        retry_after = init.config.rate_limit_window
    }))

    ngx.exit(429)
end

-- Main rate limiting function
function _M.check_rate_limit(limit, window, burst, use_redis)
    local identifier = _M.get_identifier()

    local allowed, current, actual_limit
    if use_redis then
        allowed, current, actual_limit = _M.apply_redis_rate_limit(identifier, limit, window, burst)
    else
        allowed, current, actual_limit = _M.apply_rate_limit(identifier, limit, window, burst)
    end

    -- Set rate limit headers
    _M.set_rate_limit_headers(current, actual_limit, window or init.config.rate_limit_window)

    if not allowed then
        ngx.log(ngx.WARN, "Rate limit exceeded for ", identifier,
               ": ", current, "/", actual_limit)
        _M.rate_limit_exceeded(current, actual_limit)
    end

    -- Log rate limit info for monitoring
    ngx.log(ngx.INFO, "Rate limit check for ", identifier,
           ": ", current, "/", actual_limit)
end

return _M
