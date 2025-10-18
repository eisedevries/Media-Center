-- hit "a" to cycle through audio devices

local api = "wasapi"
local deviceList = mp.get_property_native("audio-device-list")
local aid = 1

local function cycle_adevice(s, e, d)
    mp.enable_messages("error")
    while s ~= e + d do -- until the loop would cycle back to the number we started on
        if string.find(mp.get_property("audio-device"), deviceList[s].name, 1, true) then
            while true do
                if s + d == 0 then       -- the device list starts at 1; 0 means we iterated too far
                    s = #deviceList + 1  -- restart at the last device
                elseif s + d == #deviceList + 1 then -- iterated past the last device
                    s = 0                -- start from the beginning
                end
                s = s + d                -- next device
                if string.find(deviceList[s].name, api, 1, true) then
                    mp.set_property("audio-device", deviceList[s].name)
                    deviceList[s].description = "▶ " .. string.match(deviceList[s].description, "[^%(]+")
                    
                    -- Find the longest device description to calculate the padding
                    local maxLength = 0
                    for i = 1, #deviceList do
                        local currentDescription = string.match(deviceList[i].description, "[^%(]+")
                        maxLength = math.max(maxLength, #currentDescription)
                    end

                    -- Build the list with aligned descriptions
                    local list = "AUDIO DEVICE:\n"
                    for i = 1, #deviceList do
                        local currentDescription = string.match(deviceList[i].description, "[^%(]+")
                        -- Calculate padding based on the longest description
                        local padding = string.rep(" ", maxLength - #currentDescription)
                        
                        if string.find(deviceList[i].name, api, 1, true) then
                            if deviceList[i].name ~= deviceList[s].name then
                                list = list .. "     " -- Optional indentation for other devices
                            end
                            list = list .. currentDescription .. padding .. "\n"
                        end
                    end

                    if mp.get_property("vid") == "no" then
                        print("audio=" .. deviceList[s].description)
                    else
                        mp.osd_message(list, 3)
                    end
                    mp.set_property("aid", aid)
                    -- Removed the seek command that triggers the "seeking" message.
                    return
                end
            end
        end
        s = s + d
    end
end

mp.observe_property("aid", function(id)
    if id ~= "no" then aid = id end
end)

mp.register_event("log-message", function(event)
    if event.text:find("Try unsetting it") then
        mp.set_property("audio-device", "auto")
        mp.set_property("aid", aid)
    end
end)

mp.add_key_binding("a", "cycleBack_adevice", function()
    deviceList = mp.get_property_native("audio-device-list")
    cycle_adevice(#deviceList, 1, -1) -- start at the last device, end at device 1, iterate backward delta=-1
end)
