# sw-demo-ahr

Make sure to set the correct CAC address in /etc/init.d/netcat_gatttool.sh
The address(s) can be obtained using 'sudo hcitool lescan | grep CAC'
BLE Address for HAVEN-CAC-1939-0004 is 3C:71:BF:CC:0C:06

The data generator program is written for Python 3.

Use 'tail -f /var/log/data_generator.log' to see logging/debug messages from the simulator.  Here you will see if the generator is running, if it can/can't connect to the netcat/gatttool proxy, the database or the CAC.

The data generator can be restarted using 'sudo /etc/init.d/data_generator.py restart' or just a reboot.

To grab new code from GitHub, first 'cd ~/sw-demo-ahr' then 'git pull'.  If any changes are made locally remember to commit and push to GitHub: 'git commit -a' then 'git push'.

After pulling or updating data_generator.py you must run 'sudo ~/sw-demo-ahr/install.sh' to copy the data generator program into /etc/init.d.  After the copy, remember to reboot or restart the data generator as above.

The script/command for the netcat/gatttool proxy kludge is in '/etc/init.d/netcat_gatttool.sh'.  This script is run on boot by '/etc/rc.local'.

The database itself is a local install of PostgreSQL, database is 'pi', username is 'pi' and password is 'pi'.  pi/pi/pi!!!  To mess with the DB run a local Postgres console with 'psql'.

Any other questions call or text Colin @ 236-982-9075
