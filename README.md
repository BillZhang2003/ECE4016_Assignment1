# ECE4016 Assignment 1

## Requirements
- Python 3.9
- Ubuntu 20
- Python libraries: `socket`, `threading`, `dnslib`

## How to execute code
1. Use `cd` to goto the file where `Local_DNS_Server.py` is in.

2. Run the local DNS server with the following command: `python3 Local_DNS_Server.py`

3. When prompted, enter one of the following options:

- Enter `0` for public DNS querying.
- Enter `1` for iterative DNS searching.

4. To test the server, you can use a DNS client like `dig`. Open a new terminal, enter test code, like `dig www.example.com @127.0.0.1 -p 1234` and `dig www.baidu.com @127.0.0.1 -p 1234`.

## How to stop the server
To stop the DNS server, press `Ctrl + C`. This will gracefully shut down the server.

