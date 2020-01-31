# sw-demo-ahr

Make sure to set the correct CAC address in /etc/init.d/netcat_gatttool.sh
The address(s) can be obtained using 'sudo hcitool lescan | grep CAC'
BLE Address for HAVEN-CAC-1939-0004 is 3C:71:BF:CC:0C:06

Use 'tail -f /var/log/rc.local' to see logging/debug messages from the simulator
