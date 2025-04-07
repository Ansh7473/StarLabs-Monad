import random
import time
import asyncio
from typing import Dict
from web3 import AsyncWeb3
from eth_account import Account
from loguru import logger

from src.utils.config import Config
from src.utils.constants import (
    ROUTER_CONTRACT,
    WMON_CONTRACT,
    USDC_CONTRACT,
    ABI,
    AVAILABLE_TOKENS as ALL_TOKENS,
    RPC_URL,
    EXPLORER_URL,
)


class CrystalSwap:
    def __init__(
        self,
        account_index: int,
        proxy: str,
        private_key: str,
        config: Config,
    ):
        self.account_index = account_index
        self.proxy = proxy
        self.private_key = private_key
        self.config = config
        self.account = Account.from_key(private_key)
        self.web3 = AsyncWeb3(
            AsyncWeb3.AsyncHTTPProvider(
                RPC_URL,
                request_kwargs={"proxy": (f"http://{proxy}" if proxy else None)},
            )
        )
        self.router = self.web3.eth.contract(address=ROUTER_CONTRACT, abi=ABI["router"])
        self.usdc = self.web3.eth.contract(address=USDC_CONTRACT, abi=ABI["token"])
        self.AVAILABLE_TOKENS = {
            "MON": ALL_TOKENS["MON"],
            "USDC": ALL_TOKENS["USDC"],
        }

    async def get_gas_params(self) -> Dict[str, int]:
        latest_block = await self.web3.eth.get_block("latest")
        base_fee = latest_block["baseFeePerGas"]
        max_priority_fee = await self.web3.eth.max_priority_fee
        max_fee = base_fee + max_priority_fee
        return {
            "maxFeePerGas": max_fee,
            "maxPriorityFeePerGas": max_priority_fee,
        }

    async def estimate_gas(self, transaction: dict) -> int:
        try:
            estimated = await self.web3.eth.estimate_gas(transaction)
            return int(estimated * 1.2)
        except Exception as e:
            logger.warning(f"[{self.account_index}] Error estimating gas: {e}")
            return 200000

    async def get_token_balance(self, token: Dict) -> float:
        try:
            if token["native"]:
                balance_wei = await self.web3.eth.get_balance(self.account.address)
                return float(self.web3.from_wei(balance_wei, "ether"))
            else:
                balance_wei = await self.usdc.functions.balanceOf(self.account.address).call()
                return float(balance_wei) / (10 ** token["decimals"])
        except Exception as e:
            logger.error(f"[{self.account_index}] Failed to get balance: {e}")
            return 0.0

    async def approve_usdc(self, amount_wei: int) -> bool:
        try:
            allowance = await self.usdc.functions.allowance(
                self.account.address, ROUTER_CONTRACT
            ).call()
            if allowance >= amount_wei:
                return True

            logger.info(f"[{self.account_index}] Approving USDC for router...")
            tx = {
                "from": self.account.address,
                "to": USDC_CONTRACT,
                "data": self.usdc.functions.approve(ROUTER_CONTRACT, 2**256 - 1)._encode_transaction_data(),
                "chainId": 10143,
                "type": 2,
                "nonce": await self.web3.eth.get_transaction_count(self.account.address),
                **await self.get_gas_params(),
            }
            tx["gas"] = await self.estimate_gas(tx)
            signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = await self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = await self.web3.eth.wait_for_transaction_receipt(tx_hash)
            if receipt["status"] == 1:
                logger.success(f"[{self.account_index}] USDC approved: {EXPLORER_URL}{tx_hash.hex()}")
                return True
            logger.error(f"[{self.account_index}] Approval failed")
            return False
        except Exception as e:
            logger.error(f"[{self.account_index}] Approval error: {e}")
            return False

    async def swap_mon_to_usdc(self, amount: float) -> Dict:
        amount_wei = self.web3.to_wei(amount, "ether")
        path = [WMON_CONTRACT, USDC_CONTRACT]
        deadline = int(time.time()) + 600

        for attempt in range(self.config.SETTINGS.ATTEMPTS):
            try:
                tx = {
                    "from": self.account.address,
                    "to": ROUTER_CONTRACT,
                    "value": amount_wei,
                    "data": self.router.functions.swapExactETHForTokens(
                        0, path, self.account.address, deadline
                    )._encode_transaction_data(),
                    "chainId": 10143,
                    "type": 2,
                    "nonce": await self.web3.eth.get_transaction_count(self.account.address),
                    **await self.get_gas_params(),
                }
                tx["gas"] = await self.estimate_gas(tx)
                signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
                tx_hash = await self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
                receipt = await self.web3.eth.wait_for_transaction_receipt(tx_hash)
                if receipt["status"] == 1:
                    return {
                        "success": True,
                        "tx_hash": tx_hash.hex(),
                        "from_token": "MON",
                        "to_token": "USDC",
                        "amount_in": amount,
                    }
                return {"success": False, "error": "Transaction reverted"}
            except Exception as e:
                logger.error(f"[{self.account_index}] Swap attempt {attempt + 1} failed: {e}")
                if attempt < self.config.SETTINGS.ATTEMPTS - 1:
                    await asyncio.sleep(random.randint(*self.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS))
        return {"success": False, "error": "All attempts failed"}

    async def swap_usdc_to_mon(self, amount: float) -> Dict:
        amount_wei = int(amount * 10**6)
        path = [USDC_CONTRACT, WMON_CONTRACT]
        deadline = int(time.time()) + 600

        for attempt in range(self.config.SETTINGS.ATTEMPTS):
            try:
                if not await self.approve_usdc(amount_wei):
                    return {"success": False, "error": "Approval failed"}
                tx = {
                    "from": self.account.address,
                    "to": ROUTER_CONTRACT,
                    "data": self.router.functions.swapExactTokensForETH(
                        amount_wei, 0, path, self.account.address, deadline
                    )._encode_transaction_data(),
                    "chainId": 10143,
                    "type": 2,
                    "nonce": await self.web3.eth.get_transaction_count(self.account.address),
                    **await self.get_gas_params(),
                }
                tx["gas"] = await self.estimate_gas(tx)
                signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
                tx_hash = await self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
                receipt = await self.web3.eth.wait_for_transaction_receipt(tx_hash)
                if receipt["status"] == 1:
                    return {
                        "success": True,
                        "tx_hash": tx_hash.hex(),
                        "from_token": "USDC",
                        "to_token": "MON",
                        "amount_in": amount,
                    }
                return {"success": False, "error": "Transaction reverted"}
            except Exception as e:
                logger.error(f"[{self.account_index}] Swap attempt {attempt + 1} failed: {e}")
                if attempt < self.config.SETTINGS.ATTEMPTS - 1:
                    await asyncio.sleep(random.randint(*self.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS))
        return {"success": False, "error": "All attempts failed"}

    async def execute(self):
        if not hasattr(self.config, "CRYSTAL_SWAP") or not self.config.CRYSTAL_SWAP.ENABLED:
            logger.info(f"[{self.account_index}] Crystal Swap is disabled")
            return

        logger.info(f"[{self.account_index}] Starting Crystal Swap operations")
        min_swaps, max_swaps = self.config.FLOW.NUMBER_OF_SWAPS
        num_swaps = random.randint(min_swaps, max_swaps)

        for swap_num in range(1, num_swaps + 1):
            logger.info(f"[{self.account_index}] Executing swap {swap_num}/{num_swaps}")
            mon_balance = await self.get_token_balance(self.AVAILABLE_TOKENS["MON"])
            usdc_balance = await self.get_token_balance(self.AVAILABLE_TOKENS["USDC"])

            if mon_balance < 0.001 and usdc_balance < 0.01:
                logger.error(f"[{self.account_index}] Insufficient balance for swap {swap_num}")
                break

            swap_mon = random.choice([True, False]) and mon_balance >= 0.001
            min_percent, max_percent = self.config.FLOW.PERCENT_OF_BALANCE_TO_SWAP
            percent = random.uniform(min_percent, max_percent)
            if swap_mon:
                amount = mon_balance * (percent / 100)
                if amount < 0.001:
                    logger.warning(f"[{self.account_index}] Amount too small: {amount} MON")
                    continue
                result = await self.swap_mon_to_usdc(amount)
            else:
                amount = usdc_balance * (percent / 100)
                if amount < 0.01:
                    logger.warning(f"[{self.account_index}] Amount too small: {amount} USDC")
                    continue
                result = await self.swap_usdc_to_mon(amount)

            if result["success"]:
                logger.success(f"[{self.account_index}] Swap {swap_num} completed: {EXPLORER_URL}{result['tx_hash']}")
            else:
                logger.error(f"[{self.account_index}] Swap {swap_num} failed: {result['error']}")

            if swap_num < num_swaps:
                pause = random.randint(*self.config.SETTINGS.PAUSE_BETWEEN_SWAPS)
                logger.info(f"[{self.account_index}] Pausing for {pause} seconds")
                await asyncio.sleep(pause)

        logger.success(f"[{self.account_index}] Crystal Swap operations completed")
