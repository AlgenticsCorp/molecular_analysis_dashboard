-- Gateway initialization module (simplified)
-- Sets up basic configuration without external dependencies

local _M = {}

-- Configuration constants
_M.config = {
    jwt_secret = os.getenv("SECRET_KEY") or "change-me-in-production",
    service_registry_ttl = 60, -- seconds
    rate_limit_window = 60, -- seconds
    default_rate_limit = 100, -- requests per minute
}

-- Simple in-memory storage for development
local cache = {}

-- Cache operations
function _M.cache_get(key)
    local entry = cache[key]
    if entry and (not entry.expires or entry.expires > ngx.time()) then
        return entry.value
    end
    cache[key] = nil -- Remove expired entry
    return nil
end

function _M.cache_set(key, value, ttl)
    cache[key] = {
        value = value,
        expires = ttl and (ngx.time() + ttl) or nil
    }
end

function _M.cache_del(key)
    cache[key] = nil
end

-- Log configuration
function _M.log_config()
    ngx.log(ngx.INFO, "Gateway configuration:")
    ngx.log(ngx.INFO, "  Service registry TTL: ", _M.config.service_registry_ttl, "s")
    ngx.log(ngx.INFO, "  Rate limit window: ", _M.config.rate_limit_window, "s")
    ngx.log(ngx.INFO, "  Default rate limit: ", _M.config.default_rate_limit, " req/min")
end

-- Main initialization function
function _M.init()
    _M.log_config()
    ngx.log(ngx.INFO, "Gateway initialization complete - Simple mode")
end

-- Initialize on startup
_M.init()

return _M
