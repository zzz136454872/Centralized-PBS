import time
import pandas as pd
import csv
import os
import sys
import datetime as dt
from .constants import *
from swap import *
import shutil

start_time = time.time()

start_date = dt.datetime.strptime(sys.argv[1], "%Y-%m-%d")
end_date = dt.datetime.strptime(sys.argv[2], "%Y-%m-%d")
total_days = (end_date - start_date).days

for symbol in symbols:
    if not os.path.exists(f"{ROOT}/swaps/{symbol}"):
        try:
            os.makedirs(f"{ROOT}/swaps/{symbol}")
        except:
            pass
    # shutil.rmtree(f"{PATH}/errors/{symbol}", ignore_errors=True)
    if not os.path.exists(f"{ROOT}/swaps/errors/{symbol}"):
        try:
            os.makedirs(f"{ROOT}/swaps/errors/{symbol}")
        except:
            pass

swaps = {}

for day in range(total_days):
    # date = start_date + dt.timedelta(days=day, hours=8)
    date = start_date + dt.timedelta(days=day, hours=8)
    from_block = find_block(date)
    to_block = find_block(date + dt.timedelta(days=1))
    print(f"start date {date.date()}, from block {from_block} to {to_block}")

    for symbol in symbols:
        swaps[symbol] = [SWAP_HEADER]

    for block_num in range(from_block, to_block):
        block = w3.eth.get_block(block_num)
        # print(block)
        # exit()
        block_ts = int(block['timestamp'])
        logs = w3.eth.get_logs({
            'fromBlock': block_num,
            'toBlock': block_num,
            'topics': [topics]
        })
        for log in logs:
            for parser in PARSERS:
                if log['topics'][0].hex() in parser.topic0:
                    # print(log)
                    res = parser.process_log(w3, log)
                    # print(res)
                    if res:
                        res.append(block_ts)
                        swaps[parser.symbol].append(res)
                    break

    for symbol in symbols:
        with open(f"{ROOT}/swaps/{symbol}/{date.date()}.csv", "w") as f:
            w = csv.writer(f)
            w.writerows(swaps[symbol])
