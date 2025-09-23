-- Service discovery and registry module
-- Manages dynamic service registration for task services and load balancing

local cjson = require "cjson"
local http = require "resty.http"
local init = require "gateway.init"

local _M = {}

-- Register a service instance
function _M.register_service(service_info)
    local red, err = init.get_redis()
    if not red then
        return false, "Redis connection failed: " .. (err or "unknown")
    end

    -- Validate service info
    if not service_info.name or not service_info.host or not service_info.port then
        return false, "Missing required service information (name, host, port)"
    end

    -- Create service key
    local service_key = "service:" .. service_info.name .. ":" .. service_info.host .. ":" .. service_info.port

    -- Prepare service data
    local service_data = {
        name = service_info.name,
        host = service_info.host,
        port = service_info.port,
        health_check = service_info.health_check or "/health",
        last_seen = ngx.time(),
        status = "healthy",
        metadata = service_info.metadata or {}
    }

    -- Store service information
    local ok, err = red:hmset(service_key,
        "name", service_data.name,
        "host", service_data.host,
        "port", service_data.port,
        "health_check", service_data.health_check,
        "last_seen", service_data.last_seen,
        "status", service_data.status,
        "metadata", cjson.encode(service_data.metadata)
    )

    if not ok then
        init.close_redis(red)
        return false, "Failed to store service data: " .. (err or "unknown")
    end

    -- Set TTL for automatic cleanup
    red:expire(service_key, init.config.service_registry_ttl)

    -- Add to service list
    local list_key = "services:" .. service_info.name
    red:sadd(list_key, service_key)
    red:expire(list_key, init.config.service_registry_ttl)

    init.close_redis(red)

    ngx.log(ngx.INFO, "Service registered: ", service_key)
    return true
end

-- Discover services by name
function _M.discover_services(service_name)
    local red, err = init.get_redis()
    if not red then
        return {}, "Redis connection failed: " .. (err or "unknown")
    end

    -- Get service list
    local list_key = "services:" .. service_name
    local service_keys, err = red:smembers(list_key)

    if not service_keys then
        init.close_redis(red)
        return {}, "Failed to get service list: " .. (err or "unknown")
    end

    local services = {}

    -- Get details for each service
    for _, service_key in ipairs(service_keys) do
        local service_data, err = red:hgetall(service_key)
        if service_data and #service_data > 0 then
            -- Convert Redis array to hash
            local service = {}
            for i = 1, #service_data, 2 do
                service[service_data[i]] = service_data[i + 1]
            end

            -- Parse metadata JSON
            if service.metadata then
                local ok, metadata = pcall(cjson.decode, service.metadata)
                if ok then
                    service.metadata = metadata
                end
            end

            table.insert(services, service)
        end
    end

    init.close_redis(red)
    return services
end

-- Health check a service instance
function _M.health_check_service(service)
    local httpc = http.new()
    httpc:set_timeout(5000) -- 5 seconds

    local health_url = "http://" .. service.host .. ":" .. service.port .. service.health_check

    local res, err = httpc:request_uri(health_url, {
        method = "GET",
        headers = {
            ["User-Agent"] = "Gateway-Health-Check/1.0"
        }
    })

    if not res then
        return false, "Health check failed: " .. (err or "unknown")
    end

    if res.status >= 200 and res.status < 300 then
        return true, "healthy"
    else
        return false, "unhealthy: HTTP " .. res.status
    end
end

-- Update service health status
function _M.update_service_health(service_key, is_healthy)
    local red, err = init.get_redis()
    if not red then
        return false, "Redis connection failed: " .. (err or "unknown")
    end

    local status = is_healthy and "healthy" or "unhealthy"
    local ok, err = red:hset(service_key, "status", status)

    if not ok then
        init.close_redis(red)
        return false, "Failed to update health status: " .. (err or "unknown")
    end

    init.close_redis(red)
    return true
end

-- Get healthy services for load balancing
function _M.get_healthy_services(service_name)
    local services, err = _M.discover_services(service_name)
    if not services or #services == 0 then
        return {}, err
    end

    local healthy_services = {}
    for _, service in ipairs(services) do
        if service.status == "healthy" then
            table.insert(healthy_services, service)
        end
    end

    return healthy_services
end

-- Select service using round-robin load balancing
function _M.select_service(services)
    if not services or #services == 0 then
        return nil, "No services available"
    end

    -- Simple round-robin using request time
    local index = (ngx.time() % #services) + 1
    return services[index]
end

-- Handle service registry HTTP requests
function _M.handle_registry_request()
    local method = ngx.var.request_method

    if method == "POST" then
        -- Register service
        ngx.req.read_body()
        local body = ngx.req.get_body_data()

        if not body then
            ngx.status = 400
            ngx.say(cjson.encode({error = "Missing request body"}))
            return
        end

        local ok, service_info = pcall(cjson.decode, body)
        if not ok then
            ngx.status = 400
            ngx.say(cjson.encode({error = "Invalid JSON"}))
            return
        end

        local success, err = _M.register_service(service_info)
        if success then
            ngx.status = 201
            ngx.say(cjson.encode({message = "Service registered successfully"}))
        else
            ngx.status = 500
            ngx.say(cjson.encode({error = err}))
        end

    elseif method == "GET" then
        -- Discover services
        local service_name = ngx.var.arg_name
        if not service_name then
            ngx.status = 400
            ngx.say(cjson.encode({error = "Missing service name parameter"}))
            return
        end

        local services, err = _M.discover_services(service_name)
        if services then
            ngx.status = 200
            ngx.say(cjson.encode({services = services}))
        else
            ngx.status = 500
            ngx.say(cjson.encode({error = err}))
        end

    else
        ngx.status = 405
        ngx.say(cjson.encode({error = "Method not allowed"}))
    end
end

-- Cleanup expired services (called periodically)
function _M.cleanup_expired_services()
    local red, err = init.get_redis()
    if not red then
        ngx.log(ngx.ERR, "Redis connection failed for cleanup: ", err)
        return
    end

    -- This would be implemented as a background job
    -- For now, rely on Redis TTL for cleanup

    init.close_redis(red)
end

return _M
