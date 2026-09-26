# ablibrary gRPC-web client. The server rejects urllib's default User-Agent
# with 403, so send a browser one.
import struct, urllib.request
from pb import frames, walk
BASE='https://grpc.ablibrary.net/ablibrary.services.book_service.BookService/'
HDRS={'Content-Type':'application/grpc-web+proto','X-Grpc-Web':'1',
      'Origin':'https://ablibrary.net','Referer':'https://ablibrary.net/',
      'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
      'Accept':'*/*'}
def call(method, book_id, timeout=60):
    bid=str(book_id).encode(); msg=b'\x0a'+bytes([len(bid)])+bid
    body=b'\x00'+struct.pack('>I',len(msg))+msg
    req=urllib.request.Request(BASE+method, data=body, headers=HDRS)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()
def leaves(raw, maxd=6):
    out={}
    def rec(b,path=(),d=0):
        if d>maxd: return
        try: items=list(walk(b))
        except Exception: return
        for p,w,v in items:
            if w!=2: continue
            k='.'.join(map(str,path+p))
            try:
                s=v.decode('utf-8')
                if s and all(ord(c)>=32 or c in '\n\t' for c in s):
                    out.setdefault(k,s); continue
            except Exception: pass
            rec(v,path+p,d+1)
    if raw:
        for fl,p in frames(raw):
            if fl==0: rec(p)
    return out
