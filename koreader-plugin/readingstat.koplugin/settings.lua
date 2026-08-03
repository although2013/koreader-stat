local DataStorage = require("datastorage")
local LuaSettings = require("luasettings")

local SETTINGS_FILE = DataStorage:getSettingsDir() .. "/readingstat.lua"

local ReadingStatSettings = {}

function ReadingStatSettings:load()
    self.settings = LuaSettings:open(SETTINGS_FILE)
    return self
end

function ReadingStatSettings:getServerUrl()
    return self.settings:readSetting("server_url", "")
end

function ReadingStatSettings:setServerUrl(value)
    self.settings:saveSetting("server_url", value)
    self.settings:flush()
end

function ReadingStatSettings:getToken()
    return self.settings:readSetting("token", "")
end

function ReadingStatSettings:setToken(value)
    self.settings:saveSetting("token", value)
    self.settings:flush()
end

function ReadingStatSettings:getSyncOnCloseEnabled()
    return self.settings:isTrue("sync_on_close")
end

function ReadingStatSettings:setSyncOnCloseEnabled(value)
    self.settings:saveSetting("sync_on_close", value)
    self.settings:flush()
end

return ReadingStatSettings
