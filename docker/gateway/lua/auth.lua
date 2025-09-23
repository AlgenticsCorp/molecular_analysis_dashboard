-- Simple authentication module for development
-- Does basic token validation without external JWT libraries

local init = require "gateway.init"

local _M = {}

-- Extract token from Authorization header
function _M.extract_token()
    local auth_header = ngx.var.http_authorization
    if not auth_header then
        return nil, "Authorization header missing"
    end

    -- Extract Bearer token
    local token = auth_header:match("Bearer%s+(.+)")
    if not token then
        return nil, "Invalid authorization format - Bearer token required"
    end

    return token
end

-- Simple token validation (for development)
function _M.validate_token(token)
    -- For development, accept a simple token or the configured secret
    if token == "dev-token" or token == init.config.jwt_secret then
        return {
            user_id = "dev-user",
            org_id = "dev-org",
            email = "dev@example.com",
            roles = {"user", "admin"},
            exp = ngx.time() + 3600 -- Valid for 1 hour
        }
    end

    return nil, "Invalid token"
end

-- Set user context headers for downstream services
function _M.set_user_context(payload)
    if payload.user_id then
        ngx.req.set_header("X-User-ID", payload.user_id)
    end

    if payload.org_id then
        ngx.req.set_header("X-Org-ID", payload.org_id)
    end

    if payload.roles then
        local roles_str = type(payload.roles) == "table"
            and table.concat(payload.roles, ",")
            or tostring(payload.roles)
        ngx.req.set_header("X-User-Roles", roles_str)
    end

    -- Set authentication timestamp
    ngx.req.set_header("X-Auth-Time", tostring(ngx.time()))
end

-- Return authentication error response
function _M.auth_error(message, status_code)
    status_code = status_code or 401

    ngx.status = status_code
    ngx.header.content_type = "application/json"
    ngx.say('{"error":"Authentication failed","message":"' .. message .. '","timestamp":' .. ngx.time() .. '}')
    ngx.exit(status_code)
end

-- Main token validation function
function _M.validate_jwt()
    -- Extract token
    local token, err = _M.extract_token()
    if not token then
        _M.auth_error(err)
        return
    end

    -- Validate token
    local payload, err = _M.validate_token(token)
    if not payload then
        _M.auth_error(err)
        return
    end

    -- Set user context
    _M.set_user_context(payload)

    -- Log successful authentication
    ngx.log(ngx.INFO, "Token validation successful for user: ",
           payload.user_id or "unknown",
           " org: ", payload.org_id or "unknown")
end

-- Validate storage access (more permissive)
function _M.validate_storage_access()
    -- Check if authentication header is present
    local auth_header = ngx.var.http_authorization
    if not auth_header then
        -- Allow unauthenticated access for public storage
        ngx.req.set_header("X-User-ID", "anonymous")
        ngx.req.set_header("X-Org-ID", "public")
        return
    end

    -- If authentication is present, try to validate it
    local token, err = _M.extract_token()
    if token then
        local payload, err = _M.validate_token(token)
        if payload then
            _M.set_user_context(payload)
        else
            -- Log warning but don't block access
            ngx.log(ngx.WARN, "Invalid token for storage access: ", err)
            ngx.req.set_header("X-User-ID", "anonymous")
            ngx.req.set_header("X-Org-ID", "public")
        end
    end
end

return _M
