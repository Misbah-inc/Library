import sys, struct

def frames(b):
    i=0
    while i+5<=len(b):
        flag=b[i]; ln=struct.unpack('>I', b[i+1:i+5])[0]; i+=5
        yield flag, b[i:i+ln]; i+=ln

def varint(b,i):
    r=0; s=0
    while True:
        x=b[i]; i+=1; r|=(x&0x7f)<<s
        if not x&0x80: return r,i
        s+=7

def walk(b, depth=0, path=()):
    """yield (path, wire, value)"""
    i=0
    while i < len(b):
        try:
            key,i = varint(b,i)
        except Exception: return
        f, w = key>>3, key&7
        if f==0: return
        if w==0:
            v,i = varint(b,i); yield path+(f,), 0, v
        elif w==2:
            ln,i = varint(b,i)
            if i+ln>len(b): return
            payload=b[i:i+ln]; i+=ln
            yield path+(f,), 2, payload
        elif w==5: i+=4
        elif w==1: i+=8
        else: return

if __name__=='__main__':
    data=open(sys.argv[1],'rb').read()
    for flag,payload in frames(data):
        print('FRAME flag=%d len=%d' % (flag, len(payload)))
        if flag: 
            print(payload[:300]); continue
        for path,w,v in walk(payload):
            if w==0: print(' f%s varint %s' % ('.'.join(map(str,path)), v))
            else:
                try: s=v.decode('utf-8'); printable = s.isprintable() or '\n' in s
                except Exception: printable=False
                print(' f%s bytes len=%d %s' % ('.'.join(map(str,path)), len(v), (repr(s[:120]) if printable else '<binary/nested>')))
