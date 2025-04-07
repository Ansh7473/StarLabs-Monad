from web3 import Web3

# Contract addresses (from Madness constants)
ROUTER_CONTRACT = Web3.to_checksum_address("0x64Aff7245EbdAAECAf266852139c67E4D8DBa4de")
WMON_CONTRACT = Web3.to_checksum_address("0x760AfE86e5de5fa0Ee542fc7B7B713e1c5425701")
USDC_CONTRACT = Web3.to_checksum_address("0xf817257fed379853cde0fa4f97ab987181b1e5ea")

# Available tokens for CrystalSwap (subset of Madness tokens)
AVAILABLE_TOKENS = {
    "MON": {
        "name": "MON",
        "address": None,
        "decimals": 18,
        "native": True,
    },
    "USDC": {
        "name": "USDC",
        "address": USDC_CONTRACT,
        "decimals": 6,
        "native": False,
    },
}

# ABIs (reused from Madness, trimmed to essentials)
ABI = {
    "router": [
        {
            "type": "function",
            "stateMutability": "payable",
            "outputs": [{"type": "uint256[]", "name": "amounts", "internalType": "uint256[]"}],
            "name": "swapExactETHForTokens",
            "inputs": [
                {"type": "uint256", "name": "amountOutMin", "internalType": "uint256"},
                {"type": "address[]", "name": "path", "internalType": "address[]"},
                {"type": "address", "name": "to", "internalType": "address"},
                {"type": "uint256", "name": "deadline", "internalType": "uint256"},
            ],
        },
        {
            "type": "function",
            "stateMutability": "nonpayable",
            "outputs": [{"type": "uint256[]", "name": "amounts", "internalType": "uint256[]"}],
            "name": "swapExactTokensForETH",
            "inputs": [
                {"type": "uint256", "name": "amountIn", "internalType": "uint256"},
                {"type": "uint256", "name": "amountOutMin", "internalType": "uint256"},
                {"type": "address[]", "name": "path", "internalType": "address[]"},
                {"type": "address", "name": "to", "internalType": "address"},
                {"type": "uint256", "name": "deadline", "internalType": "uint256"},
            ],
 PROBLEM HERE        ],
        },
        {
            "type": "function",
            "stateMutability": "view",
            "outputs": [{"type": "uint256[]", "name": "amounts", "internalType": "uint256[]"}],
            "name": "getAmountsOut",
            "inputs": [
                {"type": "uint256", "name": "amountIn", "internalType": "uint256"},
                {"type": "address[]", "name": "path", "internalType": "address[]"},
            ],
        },
    ],
    "token": [
        {
            "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "spender", "type": "address"},
                {"internalType": "uint256", "name": "amount", "type": "uint256"},
            ],
            "name": "approve",
            "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [
                {"internalType": "address", "name": "owner", "type": "address"},
                {"internalType": "address", "name": "spender", "type": "address"},
            ],
            "name": "allowance",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
    ],
}
