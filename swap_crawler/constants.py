import datetime as dt
from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware

START_DATE = dt.datetime(2021, 5, 5)
END_DATE = dt.datetime(2023, 9, 9)

w3 = Web3(HTTPProvider('http://127.0.0.1:8547'))
if w3.eth.chain_id != 1:
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

ROOT = '/data/hackthon'

def find_block(date):
    target_ts = dt.datetime.timestamp(date)
    l = 1
    r = w3.eth.block_number

    l_block = w3.eth.get_block(l)
    r_block = w3.eth.get_block(r)
    l_ts = l_block['timestamp']
    r_ts = r_block['timestamp']
    if l_ts > target_ts or r_ts < target_ts:
        raise RuntimeError('not in range')

    while l < r - 1:
        mid = (l + r) // 2
        mid_block = w3.eth.get_block(mid)
        
        mid_ts = mid_block['timestamp']
        if mid_ts > target_ts:
            r = mid
        else:
            l = mid
    return r

START_BLOCK = find_block(START_DATE)
END_BLOCK = find_block(END_DATE)

BLOCK_HEADER = ['block_num', 'timestamp']
TX_HEADER = ['tx_hash', 'block_num', 'from', 'to', 'index', 'gas_price', 'gas']
SWAP_HEADER = ['block_num', 'tx_hash', 'from_address', 'to_address', 'from_amount', 'to_amount', 'from_token', 'to_token', 'pool_address', 'block_ts']
CREATE_POOL_HEADER = ['block_num', 'tx_hash', 'factory_address', 'pool_address', 'token0', 'token1', 'fee', 'tick_spacing', 'pool_index']
MINT_HEADER = ['block_num', 'tx_hash', 'token']
TRANSFER_HEADER = ['block_num', 'tx_hash', 'from_address', 'to_address', 'amount']
# TRANSFER_HEADER = ['block_num', 'tx_hash', 'token_address', 'from_address', 'to_address', 'amount']