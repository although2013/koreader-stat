local DataStorage = require("datastorage")
local InfoMessage = require("ui/widget/infomessage")
local MultiInputDialog = require("ui/widget/multiinputdialog")
local UIManager = require("ui/uimanager")
local WidgetContainer = require("ui/widget/container/widgetcontainer")
local NetworkMgr = require("ui/network/manager")
local ltn12 = require("ltn12")
local socket = require("socket")
local http = require("socket.http")
local socketutil = require("socketutil")
local logger = require("logger")
local T = require("ffi/util").template
local _ = require("gettext")

local Settings = require("settings")

local ReadingStat = WidgetContainer:extend{
    name = "readingstat",
    is_doc_only = false,
}

function ReadingStat:init()
    self.settings = Settings:load()
    self.ui.menu:registerToMainMenu(self)
end

function ReadingStat:addToMainMenu(menu_items)
    menu_items.readingstat = {
        text = _("Reading stat uploader"),
        sub_item_table = {
            {
                text = _("Upload now"),
                keep_menu_open = true,
                callback = function()
                    self:uploadDatabase()
                end,
            },
            {
                text = _("Server settings"),
                keep_menu_open = true,
                callback = function()
                    self:editServerSettings()
                end,
            },
            {
                text = _("Upload when closing a book (only if Wi-Fi is already connected)"),
                checked_func = function()
                    return self.settings:getSyncOnCloseEnabled()
                end,
                callback = function()
                    self.settings:setSyncOnCloseEnabled(not self.settings:getSyncOnCloseEnabled())
                end,
            },
        },
    }
end

function ReadingStat:onCloseDocument()
    if not self.settings:getSyncOnCloseEnabled() then
        return
    end
    if self.settings:getServerUrl() == "" or self.settings:getToken() == "" then
        logger.dbg("[ReadingStat] sync-on-close is enabled but server isn't configured yet, skipping")
        return
    end
    -- 只在已经连着 Wi-Fi 时才传，不主动开 Wi-Fi——避免像某些同步插件那样在
    -- 唤醒/关书时台面上打开 Wi-Fi 等联网，反而拖慢关书或耗电。
    if not (NetworkMgr:isWifiOn() and NetworkMgr:isConnected()) then
        logger.dbg("[ReadingStat] sync-on-close: Wi-Fi not connected, skipping")
        return
    end
    self:uploadDatabase(true)
end

function ReadingStat:editServerSettings()
    local dialog
    dialog = MultiInputDialog:new{
        title = _("Reading stat server settings"),
        fields = {
            {
                text = self.settings:getServerUrl(),
                hint = _("Server URL, e.g. https://example.com"),
            },
            {
                text = self.settings:getToken(),
                hint = _("Upload token"),
                text_type = "password",
            },
        },
        buttons = {
            {
                {
                    text = _("Cancel"),
                    id = "close",
                    callback = function()
                        UIManager:close(dialog)
                    end,
                },
                {
                    text = _("Save"),
                    callback = function()
                        local fields = dialog:getFields()
                        self.settings:setServerUrl((fields[1] or ""):gsub("/+$", ""))
                        self.settings:setToken(fields[2] or "")
                        UIManager:close(dialog)
                    end,
                },
            },
        },
    }
    UIManager:show(dialog)
    dialog:onShowKeyboard()
end

-- 手动拼 multipart/form-data，因为 KOReader 没有内置的 multipart 上传帮助库。
local function buildMultipartBody(boundary, filename, file_content)
    return table.concat({
        "--", boundary, "\r\n",
        'Content-Disposition: form-data; name="database"; filename="', filename, '"\r\n',
        "Content-Type: application/x-sqlite3\r\n\r\n",
        file_content,
        "\r\n--", boundary, "--\r\n",
    })
end

function ReadingStat:uploadDatabase(silent)
    local server_url = self.settings:getServerUrl()
    local token = self.settings:getToken()

    if server_url == "" then
        if not silent then
            UIManager:show(InfoMessage:new{ text = _("Please configure the server URL first (Reading stat uploader > Server settings).") })
        end
        return
    end

    local db_path = DataStorage:getSettingsDir() .. "/statistics.sqlite3"
    local db_file = io.open(db_path, "rb")
    if not db_file then
        UIManager:show(InfoMessage:new{ text = _("Could not open statistics.sqlite3.") })
        return
    end
    local content = db_file:read("*a")
    db_file:close()

    local boundary = "----readingstat" .. tostring(os.time())
    local body = buildMultipartBody(boundary, "statistics.sqlite3", content)

    local sink = {}
    local request = {
        url = server_url .. "/api/upload",
        method = "POST",
        headers = {
            ["Content-Type"] = "multipart/form-data; boundary=" .. boundary,
            ["Content-Length"] = tostring(#body),
            ["Authorization"] = "Bearer " .. token,
        },
        source = ltn12.source.string(body),
        sink = ltn12.sink.table(sink),
    }

    if not silent then
        UIManager:show(InfoMessage:new{ text = _("Uploading…"), timeout = 1 })
    end

    -- 大文件上传要给足超时，参照其他同步类插件（如 KoInsight）的做法。
    socketutil:set_timeout(socketutil.LARGE_BLOCK_TIMEOUT, socketutil.LARGE_TOTAL_TIMEOUT)
    local ok, code, _resp_headers, status = pcall(function()
        return socket.skip(1, http.request(request))
    end)
    socketutil:reset_timeout()

    if not ok then
        logger.err("[ReadingStat] upload failed", code)
        UIManager:show(InfoMessage:new{ text = _("Upload failed: network error.") })
        return
    end

    if code == 200 then
        if not silent then
            UIManager:show(InfoMessage:new{ text = _("Upload succeeded.") })
        end
    else
        logger.err("[ReadingStat] server rejected upload", code, status, table.concat(sink))
        UIManager:show(InfoMessage:new{
            text = T(_("Upload failed: server returned %1."), code or status),
        })
    end
end

return ReadingStat
