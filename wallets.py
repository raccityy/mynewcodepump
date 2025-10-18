# wallets.py

# SOL Wallets for different order types
SOL_WALLETS = [
    "2zrCVuirbTz3CQdMZA8ERM8YEKYnaWFvb4pnaCJBfxni",  # Default/0.3 SOL
    "5PKpHD5LAsX8N5jE5azUsdvSMMfE4HWeJb39d92i86Mg",  # 0.4 SOL
    "FAyrUDNrupJ3JbpLs88P9D16krKKG8BRSKwYy1E9k2dd",  # 0.5 SOL
    "3mhbzo3WfMEPb6ihrwU5VzdbQcDAYvMyY8EVq7ACc32b",  # 0.6 SOL
]

# 2
# 5
# f
# 3

# Default SOL Wallet (first address)
SOL_WALLET = SOL_WALLETS[0]

# ETH Wallets for ETH Trending
ETH_WALLET_100 = "0xfD9adBAcDB5d3482693b62a4ED0857A48A8E9D5D"  # 100$
ETH_WALLET_200 = "0x354F9d7Ee03569A340A2269126bdAC7B7d999324"  # 200$
ETH_WALLET_300 = "0xF682bcF76dFcD51F716B8A14ee2019e04028c476"  # 300$

# PumpFun Trending Wallet (if different from SOL)
PUMPFUN_WALLET = SOL_WALLET  # Using the same as SOL for now

# Default Wallet (for fallback or legacy)
DEFAULT_WALLET = SOL_WALLET