# NoobCoin
A crypto currency made for educational purposes

The noobs:
* Kimonas Sotirchos 
* Ermis Soumalias
* Markos Seferlis


## How to Run

```bash
./ngc start <n>  # <n> -> number of miners
./ngc stop
```

You can see the logs for each server at `logs/nX.log`
To view the PIDs of the running servers open `logs.running.log`. Then, `ngc stop` will terminate each PID from that file. Make sure you run it in order to free the used ports from the servers.