-- this script allows to seek and change volume with the mouse wheel
-- the left 10% of the screen is used for seeking, the rest for volume
-- change the `left_zone_percentage` variable to adjust the seek zone size


local left_zone_percentage = 0.1

-- Function to handle mouse wheel up events
function on_wheel_up(event)
    local mouse_x, _ = mp.get_mouse_pos()
    local display_width, _ = mp.get_osd_size()
    if mouse_x < display_width * left_zone_percentage then
        -- Left side: Seek forward with OSD
        mp.command("seek 5")
    else
        -- Right side: Increase volume with OSD
        mp.command("add volume 2")
    end
end

-- Function to handle mouse wheel down events
function on_wheel_down(event)
    local mouse_x, _ = mp.get_mouse_pos()
    local display_width, _ = mp.get_osd_size()
    if mouse_x < display_width * left_zone_percentage then
        -- Left side: Seek backward with OSD
        mp.command("seek -5")
    else
        -- Right side: Decrease volume with OSD
        mp.command("add volume -2")
    end
end

-- Bind the functions to mouse wheel events
mp.add_forced_key_binding("WHEEL_UP", "wheel_up", on_wheel_up)
mp.add_forced_key_binding("WHEEL_DOWN", "wheel_down", on_wheel_down)
