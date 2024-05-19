import json

v3_cache = {}
def v3_get_token(w3, pair_address):
    if pair_address in v3_cache:
        return v3_cache[pair_address]['token0'], v3_cache[pair_address]['token1']
    abi = '[{"constant": true,"inputs": [],"name": "token0","outputs": [{"internalType": "address","name": "","type": "address"}],"payable": false,"stateMutability": "view","type": "function"},{"constant": true,"inputs": [],"name": "token1","outputs": [{"internalType": "address","name": "","type": "address"}],"payable": false,"stateMutability": "view","type": "function"}]'
    abi = json.loads(abi)
    contract = w3.eth.contract(address=pair_address, abi=abi)
    token0 = contract.functions.token0().call()
    token1 = contract.functions.token1().call()
    v3_cache[pair_address] = {
        'token0': token0,
        'token1': token1
    }
    return token0, token1

class UniV3Parser:
    symbol = 'uni_v3'
    topic0 = [
        '0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67'
    ]
    def process_log(w3, log):
        block_number = log['blockNumber']
        transaction_hash = log['transactionHash'].hex()
        pair_address = log['address']
        if log['topics'][0].hex() != '0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67':
            return None
        
        from_address = '0x' + log['topics'][1].hex()[26:]
        to_address = '0x' + log['topics'][2].hex()[26:]
        from_amount = 0
        to_amount = 0

        data = log['data'].hex()[2:]
        amount0 = data[:64]
        amount1 = data[64: 64 * 2]
        from_token, to_token = v3_get_token(w3, pair_address)
        # print(log)
        
        if int(amount0[0], 16) < 8 and int(amount1[0], 16) >= 8:
            from_amount = int(amount0, 16)
            to_amount = 2**256 - int(amount1, 16)
        elif int(amount0[0], 16) >= 8 and int(amount1[0], 16) < 8:
            from_amount = int(amount1, 16)
            to_amount = 2**256 - int(amount0, 16)
            to_token, from_token = from_token, to_token
        else:
            # print(log, amount0, amount1)
            return None
        # print([block_number, transaction_hash, from_address, to_address, from_amount, to_amount, from_token, to_token, pair_address])
        return [block_number, transaction_hash, from_address, to_address, from_amount, to_amount, from_token, to_token, pair_address]