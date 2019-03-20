# NoobCoin
A crypto currency made for educational purposes

The noobs:
* Kimonas Sotirchos 
* Ermis Soumalias
* Markos Diomataris


## How to Run

```bash
# Start 5 Servers
./nbc start 5 
./nbc stop

# Send a transaction with 10 NBCs from Node 2 to Node 4
./nbc t 2 4 10
```

You can see the logs for each server at `logs/nX.log`
To view the PIDs of the running servers open `logs.running.log`. Then, `ngc stop` will terminate each PID from that file. Make sure you run it in order to free the used ports from the servers.
