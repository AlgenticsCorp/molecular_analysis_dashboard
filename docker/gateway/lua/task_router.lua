-- Task routing module for dynamic task service orchestration
-- Prepares for Stage 4: Dynamic Task Execution integration

local cjson = require "cjson"
local service_discovery = require "gateway.service_discovery"

local _M = {}

-- Extract task type from request URI
function _M.extract_task_type()
    local uri = ngx.var.uri

    -- Pattern: /tasks/{task_type}/{action} or /api/v1/tasks/{task_id}/execute
    local task_type = uri:match("/tasks/([^/]+)")
    if task_type then
        return task_type
    end

    -- For task execution requests, we might need to look up task type by ID
    local task_id = uri:match("/api/v1/tasks/([^/]+)/execute")
    if task_id then
        -- This would require a database lookup in real implementation
        -- For now, return a generic type
        return "generic-task"
    end

    return nil
end

-- Get task service configuration
function _M.get_task_service_config(task_type)
    -- This would eventually come from database (Stage 4)
    -- For now, provide static configuration
    local task_configs = {
        ["molecular-docking"] = {
            service_name = "docking-service",
            timeout = 300, -- 5 minutes
            max_retries = 2
        },
        ["molecule-analysis"] = {
            service_name = "analysis-service",
            timeout = 120, -- 2 minutes
            max_retries = 1
        },
        ["generic-task"] = {
            service_name = "task-service",
            timeout = 180, -- 3 minutes
            max_retries = 2
        }
    }

    return task_configs[task_type] or task_configs["generic-task"]
end

-- Route request to appropriate task service
function _M.route_request()
    local task_type = _M.extract_task_type()
    if not task_type then
        ngx.log(ngx.WARN, "Could not extract task type from URI: ", ngx.var.uri)
        return -- Fall back to default routing
    end

    local config = _M.get_task_service_config(task_type)
    local services = service_discovery.get_healthy_services(config.service_name)

    if #services == 0 then
        ngx.log(ngx.WARN, "No healthy services found for task type: ", task_type)
        -- Fall back to API service for task management
        return
    end

    -- Select service instance
    local selected_service = service_discovery.select_service(services)
    if not selected_service then
        ngx.log(ngx.ERR, "Failed to select service for task type: ", task_type)
        return
    end

    -- Set upstream for proxy_pass
    local upstream_url = "http://" .. selected_service.host .. ":" .. selected_service.port
    ngx.var.task_service_upstream = upstream_url

    -- Set task-specific headers
    ngx.req.set_header("X-Task-Type", task_type)
    ngx.req.set_header("X-Task-Service", selected_service.name)
    ngx.req.set_header("X-Selected-Instance", selected_service.host .. ":" .. selected_service.port)

    -- Set timeout based on task configuration
    ngx.var.proxy_read_timeout = tostring(config.timeout) .. "s"
    ngx.var.proxy_send_timeout = tostring(config.timeout) .. "s"

    ngx.log(ngx.INFO, "Routing task ", task_type, " to service: ", upstream_url)

    -- Dynamically proxy to selected service
    ngx.exec("/internal/task_proxy")
end

-- Handle task service proxy (internal location)
function _M.handle_task_proxy()
    local upstream_url = ngx.var.task_service_upstream
    if not upstream_url then
        ngx.status = 500
        ngx.say(cjson.encode({error = "No task service selected"}))
        return
    end

    -- This would be handled by an internal location in nginx.conf
    -- location /internal/task_proxy {
    --     internal;
    --     proxy_pass $task_service_upstream$request_uri;
    --     include proxy_headers.conf;
    -- }
end

-- Validate task execution request
function _M.validate_task_request()
    local method = ngx.var.request_method

    -- Only allow specific methods for task operations
    if method ~= "GET" and method ~= "POST" and method ~= "PUT" and method ~= "DELETE" then
        ngx.status = 405
        ngx.say(cjson.encode({error = "Method not allowed for task operations"}))
        ngx.exit(405)
    end

    -- Validate content type for POST/PUT requests
    if method == "POST" or method == "PUT" then
        local content_type = ngx.var.content_type
        if content_type and not content_type:match("application/json") then
            ngx.status = 415
            ngx.say(cjson.encode({error = "Content-Type must be application/json"}))
            ngx.exit(415)
        end
    end
end

-- Log task request for monitoring
function _M.log_task_request(task_type, service_info)
    local log_data = {
        timestamp = ngx.time(),
        request_id = ngx.var.http_x_request_id,
        task_type = task_type,
        user_id = ngx.var.http_x_user_id,
        org_id = ngx.var.http_x_org_id,
        method = ngx.var.request_method,
        uri = ngx.var.uri,
        service = service_info
    }

    ngx.log(ngx.INFO, "Task request: ", cjson.encode(log_data))
end

-- Get task execution metrics (for monitoring)
function _M.get_task_metrics()
    -- This would integrate with monitoring systems
    -- For now, return basic information
    return {
        active_services = 0,
        total_requests = 0,
        success_rate = 0.0,
        average_response_time = 0.0
    }
end

return _M
