-- Request ID generation and propagation module
-- Implements X-Request-ID header handling as per API_GATEWAY.md

local _M = {}

-- Generate a unique request ID
function _M.generate_request_id()
    -- Check if request ID already exists
    local existing_id = ngx.var.http_x_request_id
    if existing_id and existing_id ~= "" then
        return existing_id
    end

    -- Generate new request ID using timestamp and random component
    local time_part = tostring(ngx.now() * 1000):gsub("%.", "")
    local random_part = string.format("%06x", math.random(0, 0xffffff))
    local request_id = "req_" .. time_part .. "_" .. random_part

    return request_id
end

-- Set request ID in headers for downstream services
function _M.set_request_id(request_id)
    -- Set header for upstream services
    ngx.req.set_header("X-Request-ID", request_id)

    -- Set header for client response
    ngx.header["X-Request-ID"] = request_id

    -- Store in Nginx variable for logging
    ngx.var.request_id = request_id
end

-- Main function to generate and propagate request ID
function _M.generate()
    local request_id = _M.generate_request_id()
    _M.set_request_id(request_id)

    -- Log request start
    ngx.log(ngx.INFO, "Request started: ", request_id,
           " ", ngx.var.request_method, " ", ngx.var.uri)

    return request_id
end

return _M
