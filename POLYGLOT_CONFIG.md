cai WebControl 8 Plugin (NodeServer)

(This plugin should work with all WebControl 8 firmware versions (known from here out as WC8)).

Note: First off, I don't know what I am doing, so use at your own risk!!!

-A Heartbeat value that alternates between 1 and -1 changes with each poll event
-If you supply a custom name in the WC8 network config page, this plugin will use it. Other network settings such as port, username, password are 	user set in the plugin config page in PG3.
-Temp values automatically set to C or F depending on the WC8 configuration.
-Supply a user generated yaml single line for automatically naming each node with a friendly name, entered in the devlist value box in the plugin 	config page in PG3, or use the stock names with no devlist added. Note: Freq and counter cannot be renamed.
-shortPoll in seconds will poll the WC8 board and any value changes since the last poll will update IoX
-longPoll in seconds will force a full IoX update of all values
-Query on any node page will force a longPoll operation.

## Configuration

- Ensure the WC8 unit is running and accessible.
- Install the node server via PG3.
- Enter the IP address of the WC8 unit, example 192.168.0.123 
- Port is default 80
- username is default admin
- password is default password
- devlist is a yaml single line text file which will rename nodes on the fly. See example below.
- Monitor the IoX for updates.
- Set your shortPoll and longPoll to your desired times in seconds.

devlist example:
Every node has a nickname, aip1, aip2 and aip3 are analog inputs 1-3, ip1 to ip8 are inputs, op1-op8 are outputs, var1-var8 are variable, temp1-temp8 are temperature values.
Example, here is one of mine for example:
{"aip1": "AIP 1 Eye", "aip2": "AIP 2 WaterSofter", "aip3": "AIP 3 AC Mains", "op1": "OP 1 Media Server", "op2": "OP 2", "op3": "OP 3 BU Server", "op4": "OP 4 Fan", "op5": "OP 5 Eisy Pwr", "op6": "OP 6 Audio Pwr", "op7": "OP 7", "op8": "OP 8 WaterSoft Pwr", "temp1": "Temp 1 Outside", "temp2": "Temp 2 Attic", "temp3": "Temp 3 Equip Rm", "temp4": "Temp 4 Media Srvr", "temp5": "Temp 5 Box", "temp6": "Temp 6 Work Rm", "temp7": "Temp 7 Garage", "temp8": "Temp 8 Water Htr", "var1": "Var 1 Daylight", "var2": "Var 2 Watersoft", "var3": "Var 3 AC Mains", "var4": "Var 4 HB", "var5": "Var 5", "var6": "Var 6", "var7": "Var 7", "var8": "Var 8"}

Copy your single line yaml into the devlist value text box and press save, new friendly names will populate automatically.

