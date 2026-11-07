import argparse
import sys
import socket

from utils import PacketHeader, compute_checksum


def receiver(receiver_ip, receiver_port, window_size):
    """TODO: Listen on socket and print received message to sys.stdout."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((receiver_ip, receiver_port))
    truenext_seq=0
    buffer={}
    flag= False
    sender_addr=None
    def send_ack(seq_num):
        if sender_addr is None:
            return
        ack=PacketHeader(
            type=3,
            seq_num=seq_num,
            length=0,
            checksum=0
        )
        ack.checksum =compute_checksum(bytes(ack))
        s.sendto(bytes(ack),sender_addr)
    while True:
        # Receive packet; address includes both IP and port
        pkt, address = s.recvfrom(2048)

        # Extract header and payload
        pkt_header = PacketHeader(pkt[:16])
        msg = pkt[16 : 16 + pkt_header.length]

        # Verity checksum
        pkt_checksum = pkt_header.checksum
        pkt_header.checksum = 0
        computed_checksum = compute_checksum(pkt_header / msg)
        if pkt_checksum != computed_checksum:
            continue
        pkt_type=pkt_header.type
        seq_num=pkt_header.seq_num


        if pkt_type==0:
            if flag== False and seq_num==0:
                flag=True
                sender_addr=address
                truenext_seq=1
                send_ack(1)
            elif flag== True and sender_addr==address:
                send_ack(1)
            elif flag== True and sender_addr!=address:
                continue
            continue


        if pkt_type==2:
            if seq_num>= truenext_seq + window_size or seq_num<truenext_seq:
                send_ack(truenext_seq)
                continue
            buffer[seq_num]=msg
            while truenext_seq in buffer:
                takeout=buffer.pop(truenext_seq)
                sys.stdout.buffer.write(takeout)
                sys.stdout.flush()
                truenext_seq=truenext_seq+1
            send_ack(truenext_seq)

        elif pkt_type==1:
            if seq_num==truenext_seq:
                send_ack(seq_num+1)
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

    receiver(args.receiver_ip, args.receiver_port, args.window_size)


if __name__ == "__main__":
    main()
