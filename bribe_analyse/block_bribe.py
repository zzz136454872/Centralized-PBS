import json
import requests
from web3 import Web3, HTTPProvider
from datetime import datetime as dt
from datetime import timedelta as td
from tqdm import tqdm
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock


def find_block(w3, date):
    date_utc8 = dt.strptime(date, '%Y-%m-%d')
    data_utc0 = date_utc8 + td(hours=8)
    target_ts = dt.timestamp(data_utc0)
    print(date_utc8, data_utc0, target_ts)
    left = 1
    right = w3.eth.block_number

    l_block = w3.eth.get_block(left)
    r_block = w3.eth.get_block(right)
    l_ts = l_block['timestamp']
    r_ts = r_block['timestamp']
    if l_ts > target_ts or r_ts < target_ts:
        l_dt = dt.fromtimestamp(l_ts)
        r_dt = dt.fromtimestamp(r_ts)
        target_dt = dt.fromtimestamp(target_ts)
        raise RuntimeError(f"{w3.eth.chain_id} not in range: l_dt {l_dt} r_dt {r_dt} target_dt {target_dt}")

    while left < right - 1:
        mid = (left + right) // 2
        mid_block = w3.eth.get_block(mid)
        
        mid_ts = mid_block['timestamp']
        if mid_ts > target_ts:
            right = mid
        else:
            left = mid
    return right

def get_bribe(url, s, tx_hash, miner_lower):
    data = {
        "method": "trace_replayTransaction",
        "params": [tx_hash, ["stateDiff"]],
        "id": 1,
        "jsonrpc": "2.0",
    }
    resp = s.post(url, json=data)
    res = json.loads(resp.text)
    diff = res["result"]["stateDiff"]
    if diff.get(miner_lower, None):
        if "*" in diff[miner_lower]["balance"]:
            return (
                int(diff[miner_lower]["balance"]["*"]["to"], 16)
                - int(diff[miner_lower]["balance"]["*"]["from"], 16)
            ) 
    return 0

def get_bribe_for_block(w3, block):
    builder = block['miner']
    bribe_b = (w3.eth.get_balance(builder, block['number']) - w3.eth.get_balance(builder, block['number'] - 1)) / 1e18
    if len(block['transactions']) == 0:
        bribe_p = 0
    else:
        #proposer = block['transactions'][-1]['to']
        last_tx = block['transactions'][-1]
        #print(last_tx['from'], builder, last_tx['input'].hex(), '0x')
        if last_tx['from'] != builder or last_tx['input'].hex() != '0x':
            bribe_p = None
        else:
            bribe_p = get_bribe(url, s, block['transactions'][-1]['hash'].hex(), builder.lower()) / 1e18
            if bribe_p >= 0:
                print(block['number'], builder, bribe_p, 'bride_p >= 0')
            else:
                bribe_p = abs(bribe_p)
        #bribe_p =  (w3.eth.get_balance(proposer, block['number']) - w3.eth.get_balance(proposer, block['number'] - 1)) / 1e18
    return {'block': block['number'], 'builder' : block['miner'], 'bribe_b': bribe_b, 'bribe_p': bribe_p}

url = 'http://127.0.0.1:8547'
w3 = Web3(HTTPProvider(url))

s = requests.Session()
print(w3.is_connected())

start_date = '2024-04-01'
end_date = '2024-04-02'

start_block = find_block(w3, start_date)
end_block = find_block(w3, end_date)
print(f"start_block: {start_block}, end_block: {end_block}")
count_not_from = 0
count_not_data_0x = 0

results = []
pbar = tqdm(total=end_block - start_block)
# for block in range(start_block, end_block + 1):
#     res = get_bribe_for_block(w3, w3.eth.get_block(block, full_transactions=True))
#     results.append(res)
#     pbar.update(1)
lock = Lock()
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = []
    for block in tqdm(range(start_block, end_block + 1), desc = 'loading'):
        futures.append(executor.submit(get_bribe_for_block, w3, w3.eth.get_block(block, full_transactions=True)))

    for future in as_completed(futures):
        pbar.update(1)
        res = future.result()
        with lock:
            results.append(res)
df = pd.DataFrame(results)
df = df.sort_values(by='block')
df.to_csv(f'bribe_{start_date}_{end_date}.csv', index=False)


