import socket
import threading
import dnslib
from dnslib import DNSRecord, QTYPE
from dnslib import DNSHeader
import random


# Global cache for DNS records
cache = {}

def query_public_dns_server(domain):
    public_dns_server = ('8.8.8.8', 53)
    dns_request = DNSRecord.question(domain)
    packet = dns_request.pack()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5)
    try:
        sock.sendto(packet, public_dns_server)
        response_data, _ = sock.recvfrom(512)
        return DNSRecord.parse(response_data)
    except socket.timeout:
        print("Request to public DNS server timed out.")
        return None
    finally:
        sock.close()

def iterative_search(domain):
    root_servers = [
        '198.41.0.4',   # a.root-servers.net
        '199.9.14.201', # b.root-servers.net
        '192.33.4.12'   # c.root-servers.net
    ]

    next_server = (random.choice(root_servers), 53)
    # next_server = ('198.41.0.4', 53)
    # next_server = ('199.9.14.201', 53)
    query = DNSRecord.question(domain)

    while True:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2)
        try:
            print(f"Querying server: {next_server[0]}")
            sock.sendto(query.pack(), next_server)
            response_data, _ = sock.recvfrom(512)
            response = DNSRecord.parse(response_data)
            sock.close()

            if response.rr:
                # Check if the response contains a CNAME
                cname_record = next((rr for rr in response.rr if rr.rtype == QTYPE.CNAME), None)
                if cname_record:
                    cname = str(cname_record.rdata)
                    print(f"Found CNAME: {cname}")
                    return iterative_search(cname)
                
                # If we get an A record, return the response
                a_record = next((rr for rr in response.rr if rr.rtype == QTYPE.A), None)
                if a_record:
                    # print(f"Found A record for {domain} at {next_server[0]}")
                    return response

            # If there are authoritative records, follow them
            if response.auth:
                ns_record = response.auth[0].rdata
                ns_name = ns_record.toZone().split()[-1]
                ns_ip = resolve_ns_to_ip(ns_name)
                if ns_ip:
                    next_server = (ns_ip, 53)
                else:
                    print(f"Could not resolve NS record for: {ns_name}")
                    return None
            else:
                print("No further information from server.")
                return None
        except (socket.timeout, OSError) as e:
            print(f"Error querying server {next_server[0]}: {e}")
            return None

def resolve_ns_to_ip(ns_name):
    response = query_public_dns_server(ns_name)
    if response and response.rr:
        for rr in response.rr:
            if rr.rtype == QTYPE.A:
                return str(rr.rdata)
    return None

def resolve_domain(domain):
    # First check if the domain is already in cache
    if domain in cache:
        return cache[domain]
    
    response = iterative_search(domain)
    if response:
        cache[domain] = response
    return response

def handle_client_request(sock, data, client_address, flag):
    request = DNSRecord.parse(data)
    domain = str(request.q.qname)
    transaction_id = request.header.id

    # Print information about the incoming DNS query
    print(f"Received DNS query from {client_address[0]}:{client_address[1]} for {domain}")

    if domain in cache:
        print(f"Cache hit: {domain}")
        cached_response = cache[domain]
        response = DNSRecord(DNSHeader(id=transaction_id, qr=1, aa=1, ra=1), q=request.q)
        for rr in cached_response.rr:
            # Change the RR name to match the original domain
            rr.rname = request.q.qname
            response.add_answer(rr)
        print(f"Use the answer in cache as the DNS response")
    else:
        print(f"Cache miss: {domain}")
        if flag == 0:
            print(f"Ask the public DNS server for the IP address for {domain}")
            original_response = query_public_dns_server(domain)
        else:
            print("Start iterative searching...")
            original_response = iterative_search(domain)

        if original_response:
            cache[domain] = original_response
            response = DNSRecord(DNSHeader(id=transaction_id, qr=1, aa=1, ra=1), q=request.q)
            for rr in original_response.rr:
                # Change the RR name to match the original domain
                rr.rname = request.q.qname
                response.add_answer(rr)
        else:
            print("Failed to resolve domain.")
            return

    # Set additional flags to match the client's request
    response.header.rd = request.header.rd  # Copy recursion desired flag
    response.header.ra = 1  # Recursion available flag set to 1

    # Send the response back to the client
    sock.sendto(response.pack(), client_address)
    print("=======#########################################=======")

def start_dns_server(flag):
    server_address = ('127.0.0.1', 1234)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(server_address)
    print("Local DNS server is running on 127.0.0.1:1234...")
    print("=======#########################################=======")

    try:
        while True:
            data, client_address = sock.recvfrom(512)
            client_thread = threading.Thread(target=handle_client_request, args=(sock, data, client_address, flag))
            client_thread.start()
    except KeyboardInterrupt:
        print("\nShutting down local DNS server.")
    finally:
        sock.close()

if __name__ == "__main__":
    while True:
        try:
            num = int(input("Enter 0 for public DNS querying or 1 for iterative searching: "))
            if num == 0 or num == 1:
                break
            else:
                print("Input error, please enter again.")
        except ValueError:
            print("Invalid input, please enter an integer.")

    flag = num
    start_dns_server(flag)
