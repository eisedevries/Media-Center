--	time.lua
--	'c' shows current time on keypress;                     keybind name: "show_time_fn"
--	'C' shows what the time will be at the end of playback; keybind name: "show_end_time_fn"
--	Link: https://github.com/mustaqimM/mpv-scripts/time.lua


options = require 'mp.options'

local opts = {
	hour = '%H',
}
options.read_options(opts)
hour = string.gsub(opts.hour, '"', "")

-- Function to update current time
function update_current_time()
    local clock_hour = tonumber(os.date(hour))
    local clock_minutes = tonumber(os.date("%M"))
    
    mp.set_property("user-data/current_hour", string.format("%02d", clock_hour))
    mp.set_property("user-data/current_min", string.format("%02d", clock_minutes))
end

-- Function to update end time
function update_end_time()
    local remaining_t_seconds = mp.get_property_number("playtime-remaining")
    if not remaining_t_seconds then 
        mp.set_property("user-data/end_hour", "")
        mp.set_property("user-data/end_min", "")
        return 
    end
    
    local clock_hour = tonumber(os.date(hour))
    local clock_minutes = tonumber(os.date("%M"))
    
    local remaining_t_hours = math.floor(remaining_t_seconds / 3600)
    local remaining_t_min = (remaining_t_seconds / 60) % 60
    
    local end_hour = clock_hour + remaining_t_hours
    local end_min = math.floor(clock_minutes + remaining_t_min)
    
    if end_min >= 60 then
        end_hour = math.floor(end_hour + (end_min / 60))
        end_min = math.floor(end_min % 60)
    end
    
    if end_hour >= 24 then
        end_hour = math.abs(end_hour % 24)
    end
    
    mp.set_property("user-data/end_hour", string.format("%02d", end_hour))
    mp.set_property("user-data/end_min", string.format("%02d", end_min))
end

-- Update times every second
mp.add_periodic_timer(1, update_current_time)
mp.observe_property("playback-time", "number", update_end_time)

function show_time_fn()
	mp.msg.info(os.date(hour .. ':%M'))
	mp.osd_message(os.date(hour .. ":%M"))
end
