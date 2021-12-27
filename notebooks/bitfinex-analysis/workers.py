# Functions that can be threaded

import numpy as np


def determine_sell(work_tuple):
    local_chunk, pair, i, row, MIN_PROFIT, current_batch_end = work_tuple
    pair = row['pair']
    if row['price'] * (1 + MIN_PROFIT) < local_chunk['high'].iloc[0]:  # sell
        amount_to_sell = row['amount']
        sell_price = row['price'] * (1 + MIN_PROFIT) * row['amount']
        sell_price_with_fee = sell_price * (1 - 0.002)
        print(f"Sold {amount_to_sell} of {pair} for {sell_price_with_fee} on {current_batch_end}")
        print(f"Made profit of {row['amount'] * row['price'] * MIN_PROFIT}")
        print("--------------------------------------")
        return {
            'id': i,
            'mts': current_batch_end,
            'pair': pair,
            'amount': row['amount'],
            'price': sell_price_with_fee,
            'type': 'SELL'
        }


def calculate_slope(work_tuple):
    pair, local_chunk = work_tuple
    slope = np.polyfit(local_chunk.index, local_chunk['avg'], 1)[0]
    return (slope, pair)
