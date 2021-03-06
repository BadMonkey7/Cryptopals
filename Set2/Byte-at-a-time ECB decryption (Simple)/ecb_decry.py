# coding=utf-8
from base64 import b64decode
from  random import randint
from AES_ECB import AES_128_ECB
import string
# ecb mode attack explain
# considering real scenes where you can encrypt you message through an api,and you can catch the encrypted message.
# but in the process your message is added into a template string, like 'hi,{your message},welcome to my home!'
# if the encrypt method is a block cipher like aes,(actually i just learned aes so it easy to start)
# the first thing is to find the block size which is the number of bytes that are encrypted every time
# the second thing is detected which mode is used in the aes encryption (actually ecb mode can be detected)
# besides we also want to know how long is the offside which is the distance
# between the first letter of your message and the first letter of the whole string(really important)
# and then we can use brute force to attack every bytes
# this blog is very useful to understand this attack:
# https://zachgrace.com/posts/attacking-ecb/

# random key generate
def generate_random(length):
    key = ''
    for i in range(length):
        key += chr(randint(0,255))
    return key

# global key
key = generate_random(16)

# api encrypt
def oracle(message):
    add = 'Um9sbGluJyBpbiBteSA1LjAKV2l0aCBteSByYWctdG9wIGRvd24gc28gbXkgaGFpciBjYW4gYmxvdwpUaGUgZ2lybGllcyBvbiBzdGFuZGJ5IHdhdmluZyBqdXN0IHRvIHNheSBoaQpEaWQgeW91IHN0b3A/IE5vLCBJIGp1c3QgZHJvdmUgYnkK'
    unknown = b64decode(add)
    message = 'hi,this is my place{}'.format(message)+unknown
    enc = AES_128_ECB(message,key)
    return enc

# find the offside
def find_offside():
    bs = find_block_size()
    # offside = k*block_size + m => offside = m(mod block_size)
    enc = oracle('')
    length = len(enc)
    if length == 0:
        return 0
    record = [enc[i*bs:bs*i+bs] for i in range(length/bs)]
    for i in range(bs):
        message = i*'A'+'A'*bs*2
        cur = oracle(message)
        tmp = [cur[bs*j:bs*j+bs] for j in range(len(cur)/bs)]
        # detected offside
        pos = -1
        # find the first different encrypt block
        for j in range(len(record)):
            if tmp[j] != record[j]:
                pos = j
                break
        if pos == -1:
            return length
        else:
            if pos == len(record)-1:
                if tmp[pos+1] == tmp[pos+2]:
                    return (pos+1)*bs-i
            else:
                if tmp[pos + 1] == tmp[pos + 2]:
                    if tmp[pos+3] == record[pos+1]:
                        return (pos+1)*bs
                    else:
                        return (pos+1)*bs -i
    return 0


## find the block size in aes
def find_block_size():
    block_size = 0
    cur = 0
    for i in range(0,32):
        tmp = len(oracle('A'*i))
        if cur == 0:
            cur = tmp
            continue
        elif tmp > cur:
            block_size = tmp -cur
            break
    return block_size
# judge if this is aes ecb mode
def detect_ecb():
    bs = find_block_size()
    enc = oracle('A'*bs*5)
    record = [enc[i*bs:i*bs+bs] for i in range(len(enc)/bs)]
    for i in record:
        if record.count(i)>1:
            return True
    return False
# single byte encry
def pure_oracle(string,bs=find_block_size(),off=find_offside()):
    if off%bs:
        length = off / bs +1
    else:
        length = off /bs
    mess = (length*bs-off)*'A'+string
    enc = oracle(mess)[length*bs:length*bs+bs]
    return enc

# brute force
def find_fir_diff(bs,off,pad):
    enc = oracle('')
    record = [enc[i*bs:i*bs+bs] for i in range(len(enc)/bs)]
    if off%bs:
        length = off / bs +1
    else:
        length = off /bs
    cur = oracle(pad*(length*bs-off+bs))
    tmp = [cur[i*bs:i*bs+bs] for i in range(len(cur)/bs)]
    pos = -1
    for i in range(len(record)):
        if tmp[i] != record[i]:
            pos = i+1
            break
    num = len(record)-pos
    return [pos,num]


# find the unknown string
def decry_ecb():
    bs = find_block_size()
    off = find_offside()
    if detect_ecb():
        [start,tot] = find_fir_diff(bs,off,'A')
        pre = bs - off % bs
        # total bytes
        plain = 'A'*bs
        all = string.printable
        for byte in range(tot+1):
            cur = pre * 'A'
            pos = start+byte
            # attack every bit
            record = list(plain[-bs+1:]+plain[-bs])
            nt = ''
            for bit in range(bs):
                payload = cur +(bs-bit-1)*'A'
                enc = oracle(payload)[pos*bs:pos*bs+bs]
                for item in all:
                    record[-1] = item
                    tmp = ''.join(record)
                    if pure_oracle(tmp) == enc:
                        nt = tmp[-bit-1:]
                        tmp = tmp[1:] + tmp[0]
                        record = list(tmp)
                        break
            plain += nt
        plain = plain[bs:]
        return plain
    else:
        return ''


print decry_ecb()