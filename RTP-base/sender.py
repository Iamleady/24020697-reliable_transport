import argparse
import socket
import time
import sys

from utils import PacketHeader, compute_checksum


def sender(receiver_ip, receiver_port, window_size):
    """TODO: Open socket and send message from sys.stdin."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0.01)
    reciever_addr=(receiver_ip,receiver_port)
    inputdata=sys.stdin.buffer.read()
    max_payload=1456




    chunks=[]
    for i in range(0,len(inputdata),max_payload):
        start=i
        end=i+max_payload
        onechunk=inputdata[start:end]
        chunks.append(onechunk)
    if len(chunks)==0:
        chunks=[b""]





    def create_packet(pkt_type,seq_num,data=b""):
        pkt_header=PacketHeader(
            type=pkt_type,
            seq_num=seq_num,
            length=len(data),
            checksum=0
        )
        pkt_header.checksum = compute_checksum(pkt_header / data)
        return bytes(pkt_header / data)

    


    start_part=create_packet(0,0,b"")
    while True:
        s.sendto(start_part,reciever_addr)
        try:
            reciever_ack,ippp=s.recvfrom(2048)
            if len(reciever_ack)>=16:
                size=16
                cut=reciever_ack[0:16]
                ack_header=PacketHeader(cut)
                ack_checksum=ack_header.checksum
                ack_header.checksum=0
                if( ack_checksum==compute_checksum(bytes(ack_header)) and ack_header.type==3 and ack_header.seq_num==1 ):
                    break
        except socket.timeout:
            continue



    need_send=1
    next_seq_num=1
    total_packets=len(chunks)
    timer_start=None
    while need_send<=total_packets:
        while(next_seq_num<need_send+window_size and next_seq_num<=total_packets):
            data=create_packet(2,next_seq_num,chunks[next_seq_num-1])
            s.sendto(data,reciever_addr)
            if timer_start is None:
                timer_start=time.time()
            next_seq_num=next_seq_num+1
        try:
            reciever_ack,ippp=s.recvfrom(2048)
            if len(reciever_ack)>=16:
                size=16
                cut=reciever_ack[0:16]
                ack_header=PacketHeader(cut)
                ack_checksum=ack_header.checksum
                ack_header.checksum=0
                if(ack_checksum == compute_checksum(bytes(ack_header)) and ack_header.type==3):
                    ack_seq=ack_header.seq_num
                    if ack_seq>need_send:
                        need_send=ack_seq
                        if need_send<next_seq_num:
                            timer_start=time.time()
                        else:
                            timer_start= None
        except socket.timeout:
            pass
        if timer_start and (time.time() - timer_start >= 0.5):
            timer_start = time.time()
            for seq_num in range(need_send, next_seq_num):
                pkt_data = create_packet(2, seq_num, chunks[seq_num - 1])
                s.sendto(pkt_data, reciever_addr)



    end_seq_num=total_packets+1
    end_pkt=create_packet(1,end_seq_num,b"")
    end_timer=time.time()
    while True:
        s.sendto(bytes(end_pkt), reciever_addr)
        try:
            reciever_ack,ippp=s.recvfrom(2048)
            if len(reciever_ack)>=16:
                size=16
                cut=reciever_ack[0:16]
                ack_header=PacketHeader(cut)
                ack_checksum=ack_header.checksum
                ack_header.checksum=0
                if(ack_checksum == compute_checksum(bytes(ack_header)) and ack_header.type==3 and ack_header.seq_num==end_seq_num+1):
                    break
        except socket.timeout:
            pass
        if time.time() - end_timer>=0.5:
            break
    s.close()
        






def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "receiver_ip", help="The IP address of the host that receiver is running on"
    )
    parser.add_argument(
        "receiver_port", type=int, help="The port number on which receiver is listening"
    )
    parser.add_argument(
        "window_size", type=int, help="Maximum number of outstanding packets"
    )
    args = parser.parse_args()

    sender(args.receiver_ip, args.receiver_port, args.window_size)


if __name__ == "__main__":
    main()
