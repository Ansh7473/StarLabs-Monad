import random
import time
import asyncio
from typing import Dict, Tuple
from web3 import AsyncWeb3, Web3
from eth_account import Account
from loguru import logger
from primp import AsyncClient

from src.utils.config import Config
from src.utils.constants import EXPLORER_URL, RPC_URL
from .constants import (
    ROUTER_CONTRACT,
    WMON_CONTRACT,
    USDC_CONTRACT,
    ABI,
    AVAILABLE_TOKENS,
)


class CrystalSwap:
    def __init__(
        self,
        account_index: int,
        proxy: str,
        private_key: str,
        config: Config,
        session: AsyncClient,
    ):
        self.account_index = account_index
        self.proxy = proxy
        self.private_key = private_key
        self.config = config
        self.session = session
        self.account = Account.from_key(private_key)
        self.web3 = AsyncWeb3(
            AsyncWeb3.AsyncHTTPProvider(
                RPC_URL,
                request_kwargs={"proxy": (f"http://{proxy}"), "ssl": False},
            )
        )
        self.router = self.web3.eth.contract(address=ROUTER_CONTRACT, abi=ABI["router"])
        self.usdc = self.web3.eth.contract(address=USDC_CONTRACT, abi=ABI["token"])

    async def execute(self):
        """
        Execute CrystalSwap operations: perform random swaps between MON and USDC.
        """
        logger.info(f"[{self.account_index}] Starting CrystalSwap operations")

        # Check if CrystalSwap is enabled
        if not hasattr(self.config, "CRYSTAL_SWAP") or not self.config.CRYSTAL_SWAP.ENABLED:
            logger.info(f"[{self.account_index}] CrystalSwap is disabled in config")
            return

        # Get initial balances
        token_balances = {}
        for symbol, token_info in AVAILABLE_TOKENS.items():
            balance = await self.get_token_balance(self.account.address, token_info)
            token_balances[symbol] = balance
            logger.info(f"[{self.account_index}] Balance of {symbol}: {balance}")

        # Determine number of swaps
        min_swaps, max_swaps = self.config.FLOW.NUMBER_OF_SWAPS
        num_swaps = random.randint(min_swaps, max_swaps)
        logger.info(f"[{self.account_index}] Will perform {num_swaps} swaps")

        # Perform swaps
        for swap_num in range(1, num_swaps + 1):
            logger.info(f"[{self.account_index}] Executing swap {swap_num}/{num_swaps}")

            # Update balances
            for symbol, token_info in AVAILABLE_TOKENS.items():
                balance = await self.get_token_balance(self.account.address, token_info)
                token_balances[symbol] = balance

            # Select token pair and amount
            token_from, token_to, amount = await self._select_swap_pair(token_balances)

            if not token_from or not token_to:
                logger.warning(
                    f"[{self.account_index}] No suitable tokens for swap {swap_num}. Skipping."
                )
                continue

            logger.info(
                f"[{self.account_index}] Swap {swap_num}: {token_from} -> {token_to}, amount: {amount}"
            )

            if amount <= 0.01:
                logger.warning(
                    f"[{self.account_index}] Amount too small for swap {swap_num}. Skipping."
                )
                continue

            # Execute swap
            swap_result = await self.swap(token_from, token_to, amount)

            if swap_result["success"]:
                logger.success(
                    f"[{self.account_index}] Swap {swap_num} completed: "
                    f"{swap_result['amount_in']} {swap_result['from_token']} -> "
                    f"{swap_result['expected_out']} {swap_result['to_token']}. "
                    f"TX: {EXPLORER_URL}{swap_result['tx_hash']}"
                )
            else:
                logger.error(
                    f"[{self.account_index}] Swap {swap_num} failed: {swap_result.get('error', 'Unknown error')}"
                )

            # Pause between swaps
            if swap_num < num_swaps:
                pause_time = random.randint(
                    self.config.SETTINGS.RANDOM_PAUSE_BETWEEN_ACTIONS[0],
                    self.config.SETTINGS.RANDOM_PAUSE_BETWEEN_ACTIONS[1],
                )
                logger.info(
                    f"[{self.account_index}] Pausing for {pause_time} seconds before next swap"
                )
                await asyncio.sleep(pause_time)

        logger.success(f"[{self.account_index}] Completed all {num_swaps} CrystalSwap operations")

    async def get_gas_params(self) -> Dict[str, int]:
        """Get current gas parameters from the network."""
        latest_block = await self.web3.eth.get_block("latest")
        base_fee = latest_block["baseFeePerGas"]
        max_priority_fee = await self.web3.eth.max_priority_fee
        max_fee = base_fee + max_priority_fee
        return {
            "maxFeePerGas": max_fee,
            "maxPriorityFeePerGas": max_priority_fee,
        }

    async def estimate_gas(self, transaction: dict) -> int:
        """Estimate gas for transaction with a buffer."""
        try:
            estimated = await self.web3.eth.estimate_gas(transaction)
            return int(estimated * 1.1)
        except Exception as e:
            logger.warning(
                f"[{self.account_index}] Error estimating gas: {e}. Using default gas limit"
            )
            raise e

    async def get_token_balance(self, wallet_address: str, token: Dict) -> float:
        """Get token balance for a wallet."""
        max_retries = 15
        retries = 0
        last_exception = None

        while retries <= max_retries:
            try:
                wallet_address = Web3.to_checksum_address(wallet_address)
                if token["native"]:
                    balance_wei = await self.web3.eth.get_balance(wallet_address)
                    return float(Web3.from_wei(balance_wei, "ether"))
                else:
                    balance_wei = await self.usdc.functions.balanceOf(wallet_address).call()
                    return float(balance_wei) / (10 ** token["decimals"])
            except Exception as e:
                retries += 1
                last_exception = e
                await asyncio.sleep(1)

        logger.error(
            f"[{self.account_index}] All {max_retries} retry attempts failed when checking balance. Last error: {last_exception}"
        )
        return 0

    async def check_allowance(self, token_address: str, spender_address: str, amount_wei: int) -> bool:
        """Check if allowance is sufficient for token."""
        token_contract = self.web3.eth.contract(address=token_address, abi=ABI["token"])
        current_allowance = await token_contract.functions.allowance(
            self.account.address, spender_address
        ).call()
        return current_allowance >= amount_wei

    async def approve_token(self, token: Dict, amount_wei: int, spender_address: str) -> str:
        """Approve token for spending if necessary."""
        if token["native"]:
            return None

        if await self.check_allowance(token["address"], spender_address, amount_wei):
            return None

        logger.info(f"[{self.account_index}] 🔑 [APPROVAL] Approving {token['name']}...")
        token_contract = self.web3.eth.contract(address=token["address"], abi=ABI["token"])
        approve_func = token_contract.functions.approve(spender_address, 2**256 - 1)
        gas_params = await self.get_gas_params()

        transaction = {
            "from": self.account.address,
            "to": token["address"],
            "data": approve_func._encode_transaction_data(),
            "chainId": 10143,
            "type": 2,
            "nonce": await self.web3.eth.get_transaction_count(self.account.address, "latest"),
        }

        estimated_gas = await self.estimate_gas(transaction)
        transaction.update({"gas": estimated_gas, **gas_params})

        signed_tx = self.web3.eth.account.sign_transaction(transaction, self.private_key)
        tx_hash = await self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = await self.web3.eth.wait_for_transaction_receipt(tx_hash)

        if receipt["status"] == 1:
            logger.success(
                f"[{self.account_index}] ✅ [APPROVAL] {token['name']} approved. TX: {EXPLORER_URL}{tx_hash.hex()}"
            )
            return Web3.to_hex(tx_hash)
        else:
            logger.error(f"[{self.account_index}] Approval transaction failed.")
            return None

    async def swap(self, token_from: str, token_to: str, amount: float, slippage: float = 0.5) -> Dict:
        """Execute a token swap between MON and USDC."""
        for retry in range(self.config.SETTINGS.ATTEMPTS):
            try:
                token_a = AVAILABLE_TOKENS[token_from]
                token_b = AVAILABLE_TOKENS[token_to]

                balance = await self.get_token_balance(self.account.address, token_a)
                if balance < amount:
                    raise ValueError(
                        f"Insufficient balance. Have {balance} {token_a['name']}, need {amount}"
                    )

                amount_in_wei = (
                    Web3.to_wei(amount, "ether") if token_a["native"]
                    else int(amount * (10 ** token_a["decimals"]))
                )

                path = (
                    [WMON_CONTRACT, token_b["address"]] if token_a["native"]
                    else [token_a["address"], WMON_CONTRACT]
                )

                amounts_out = await self.router.functions.getAmountsOut(amount_in_wei, path).call()
                expected_out = amounts_out[-1]
                min_amount_out = int(expected_out * (1 - slippage / 100))
                deadline = int(time.time()) + 3600

                if not token_a["native"]:
                    await self.approve_token(token_a, amount_in_wei, ROUTER_CONTRACT)

                gas_params = await self.get_gas_params()
                tx_func = (
                    self.router.functions.swapExactETHForTokens(
                        min_amount_out, path, self.account.address, deadline
                    ) if token_a["native"]
                    else self.router.functions.swapExactTokensForETH(
                        amount_in_wei, min_amount_out, path, self.account.address, deadline
                    )
                )

                transaction = {
                    "from": self.account.address,
                    "to": ROUTER_CONTRACT,
                    "value": amount_in_wei if token_a["native"] else 0,
                    "data": tx_func._encode_transaction_data(),
                    "chainId": 10143,
                    "type": 2,
                    "nonce": await self.web3.eth.get_transaction_count(self.account.address, "latest"),
                }

                estimated_gas = await self.estimate_gas(transaction)
                transaction.update({"gas": estimated_gas, **gas_params})

                signed_tx = self.web3.eth.account.sign_transaction(transaction, self.private_key)
                tx_hash = await self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
                logger.info(
                    f"[{self.account_index}] 🚀 [TX SENT] Transaction hash: {EXPLORER_URL}{tx_hash.hex()}"
                )

                receipt = await self.web3.eth.wait_for_transaction_receipt(tx_hash)
                if receipt["status"] == 1:
                    return {
                        "success": True,
                        "tx_hash": Web3.to_hex(tx_hash),
                        "from_token": token_a["name"],
                        "to_token": token_b["name"],
                        "amount_in": amount,
                        "expected_out": expected_out / (10 ** token_b["decimals"]),
                        "gas_used": receipt["gasUsed"],
                    }
                else:
                    logger.error(f"[{self.account_index}] Swap transaction failed.")
                    continue

            except Exception as e:
                logger.error(f"[{self.account_index}] Swap attempt {retry + 1} failed: {e}")
                if retry < self.config.SETTINGS.ATTEMPTS - 1:
                    await asyncio.sleep(random.randint(*self.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS))
        return {"success": False, "error": "Max retry attempts reached"}

    async def _select_swap_pair(self, token_balances: Dict[str, float]) -> Tuple[str, str, float]:
        """Select a random MON <-> USDC swap pair based on balances."""
        mon_balance = token_balances["MON"]
        usdc_balance = token_balances["USDC"]

        if mon_balance < 0.001 and usdc_balance < 0.01:
            return None, None, 0

        swap_mon = random.choice([True, False]) and mon_balance >= 0.001
        min_percent, max_percent = self.config.FLOW.PERCENT_OF_BALANCE_TO_SWAP
        percent = random.uniform(min_percent, max_percent)

        if swap_mon:
            token_from, token_to = "MON", "USDC"
            amount = mon_balance * (percent / 100)
            if amount < 0.001:
                return None, None, 0
        else:
            token_from, token_to = "USDC", "MON"
            amount = usdc_balance * (percent / 100)
            if amount < 0.01:
                return None, None, 0

        return token_from, token_to, amount
