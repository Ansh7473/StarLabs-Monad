import asyncio
import random
import subprocess
import os

from loguru import logger

from src.model.crusty_swap.instance import CrustySwap
from src.model.disperse_from_one.instance import DisperseFromOneWallet
from src.model.balance_checker.instance import BalanceChecker
from src.model.disperse_one_one.instance import DisperseOneOne
from src.model.crystal_swap.instance import CrystalSwap  # Added import
import src.utils
from src.utils.output import show_dev_info, show_logo
import src.model
from src.utils.statistics import print_wallets_stats
from src.utils.check_github_version import check_version
from src.utils.logs import ProgressTracker, create_progress_tracker


async def start():
    async def launch_wrapper(index, proxy, private_key, discord_token, twitter_token, email):
        async with semaphore:
            await account_flow(
                index,
                proxy,
                private_key,
                discord_token,
                twitter_token,
                email,
                config,
                lock,
                progress_tracker,
            )

    show_logo()
    show_dev_info()

    try:
        await check_version("0xStarLabs", "StarLabs-Monad")
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Failed to check version: {e}")
        logger.info("Continue with current version\n")

    print("")

    print("Available options:\n")
    print("[1] 😈 Start farm")
    print("[2] 🔧 Edit config")
    print("[3] 🔍 Balance checker")
    print("[4] 🔄 Update")
    print("[5] 👋 Exit")
    
    try:
        choice = input("Enter option (1-5): ").strip()
    except Exception as e:
        logger.error(f"Input error: {e}")
        return
    if choice == "5" or not choice:
        return
    elif choice == "4":
        try:
            logger.info("Running update.bat script...")
            current_dir = os.path.dirname(os.path.abspath(__file__))
            update_script = os.path.join(current_dir, "update.bat")
            subprocess.run(update_script, shell=True, check=True)
            logger.success("Update completed")
            return
        except Exception as e:
            logger.error(f"Failed to run update script: {e}")
            return
    elif choice == "3":
        proxies = src.utils.read_txt_file("proxies", "data/proxies.txt")
        if len(proxies) == 0:
            logger.error("No proxies found in data/proxies.txt")
            return
        proxies = src.utils.check_proxy_format(proxies)
        if proxies is False:
            return
        private_keys = src.utils.read_txt_file("private keys", "data/private_keys.txt")
        balance_checker = BalanceChecker(private_keys, proxies[0])
        await balance_checker.run()
        return
    elif choice == "2":
        config_ui = src.utils.ConfigUI()
        config_ui.run()
        return
    elif choice == "1":
        pass
    else:
        logger.error(f"Invalid choice: {choice}")
        return

    config = src.utils.get_config()

    proxies = src.utils.read_txt_file("proxies", "data/proxies.txt")
    if len(proxies) == 0:
        logger.error("No proxies found in data/proxies.txt")
        return
    proxies = src.utils.check_proxy_format(proxies)
    if proxies is False:
        return
    
    if "disperse_farm_accounts" in config.FLOW.TASKS:
        main_keys = src.utils.read_txt_file("private keys", "data/private_keys.txt")
        farm_keys = src.utils.read_txt_file("private keys", "data/keys_for_faucet.txt")
        disperse_one_one = DisperseOneOne(main_keys, farm_keys, proxies, config)
        await disperse_one_one.disperse()
        return
    elif "disperse_from_one_wallet" in config.FLOW.TASKS:
        main_keys = src.utils.read_txt_file("private keys", "data/private_keys.txt")
        farm_keys = src.utils.read_txt_file("private keys", "data/keys_for_faucet.txt")
        disperse_one_wallet = DisperseFromOneWallet(farm_keys[0], main_keys, proxies, config)
        await disperse_one_wallet.disperse()
        return

    if "farm_faucet" in config.FLOW.TASKS:
        private_keys = src.utils.read_txt_file("private keys", "data/keys_for_faucet.txt")
    else:
        private_keys = src.utils.read_txt_file("private keys", "data/private_keys.txt")

    if "dusted" in config.FLOW.TASKS and not config.DUSTED.SKIP_TWITTER_VERIFICATION:
        twitter_tokens = src.utils.read_txt_file("twitter tokens", "data/twitter_tokens.txt")
        if len(twitter_tokens) < len(private_keys):
            logger.error(f"Not enough twitter tokens. Twitter tokens: {len(twitter_tokens)} < Private keys: {len(private_keys)}")
            return
    else:
        twitter_tokens = [""] * len(private_keys)
    
    if "crusty_refuel_from_one_to_all" in config.FLOW.TASKS:
        private_keys_to_distribute = private_keys[1:]
        crusty_swap = CrustySwap(1, proxies[0], private_keys[0], config)
        await crusty_swap.refuel_from_one_to_all(private_keys_to_distribute)
        return

    if "crystal_swap" in config.FLOW.TASKS:
        from primp import AsyncClient  # Import here to avoid issues if primp is missing
        session = AsyncClient(proxy=f"http://{proxies[0]}")
        crystal_swap = CrystalSwap(1, proxies[0], private_keys[0], config, session)
        await crystal_swap.execute()
        return

    start_index = config.SETTINGS.ACCOUNTS_RANGE[0]
    end_index = config.SETTINGS.ACCOUNTS_RANGE[1]

    if start_index == 0 and end_index == 0:
        if config.SETTINGS.EXACT_ACCOUNTS_TO_USE:
            selected_indices = [i - 1 for i in config.SETTINGS.EXACT_ACCOUNTS_TO_USE]
            accounts_to_process = [private_keys[i] for i in selected_indices]
            logger.info(f"Using specific accounts: {config.SETTINGS.EXACT_ACCOUNTS_TO_USE}")
            start_index = min(config.SETTINGS.EXACT_ACCOUNTS_TO_USE)
            end_index = max(config.SETTINGS.EXACT_ACCOUNTS_TO_USE)
        else:
            accounts_to_process = private_keys
            start_index = 1
            end_index = len(private_keys)
    else:
        accounts_to_process = private_keys[start_index - 1 : end_index]

    discord_tokens = [""] * len(accounts_to_process)
    emails = [""] * len(accounts_to_process)

    threads = config.SETTINGS.THREADS
    cycled_proxies = [proxies[i % len(proxies)] for i in range(len(accounts_to_process))]

    shuffled_indices = list(range(len(accounts_to_process)))
    random.shuffle(shuffled_indices)

    account_order = " ".join(str(start_index + idx) for idx in shuffled_indices)
    logger.info(f"Starting with accounts {start_index} to {end_index} in random order...")
    logger.info(f"Accounts order: {account_order}")

    lock = asyncio.Lock()
    semaphore = asyncio.Semaphore(value=threads)
    tasks = []

    total_accounts = len(accounts_to_process)
    progress_tracker = await create_progress_tracker(total=total_accounts, description="Accounts completed")

    for shuffled_idx in shuffled_indices:
        tasks.append(
            asyncio.create_task(
                launch_wrapper(
                    start_index + shuffled_idx,
                    cycled_proxies[shuffled_idx],
                    accounts_to_process[shuffled_idx],
                    discord_tokens[shuffled_idx],
                    twitter_tokens[shuffled_idx],
                    emails[shuffled_idx],
                )
            )
        )

    await asyncio.gather(*tasks)
    logger.success("Saved accounts and private keys to a file.")
    print_wallets_stats(config)


async def account_flow(
    account_index: int,
    proxy: str,
    private_key: str,
    discord_token: str,
    twitter_token: str,
    email: str,
    config: src.utils.config.Config,
    lock: asyncio.Lock,
    progress_tracker: ProgressTracker,
):
    try:
        pause = random.randint(
            config.SETTINGS.RANDOM_INITIALIZATION_PAUSE[0],
            config.SETTINGS.RANDOM_INITIALIZATION_PAUSE[1],
        )
        logger.info(f"[{account_index}] Sleeping for {pause} seconds before start...")
        await asyncio.sleep(pause)

        report = False
        instance = src.model.Start(
            account_index, proxy, private_key, discord_token, twitter_token, email, config
        )

        result = await wrapper(instance.initialize, config)
        if not result:
            report = True

        result = await wrapper(instance.flow, config)
        if not result:
            report = True

        pause = random.randint(
            config.SETTINGS.RANDOM_PAUSE_BETWEEN_ACCOUNTS[0],
            config.SETTINGS.RANDOM_PAUSE_BETWEEN_ACCOUNTS[1],
        )
        logger.info(f"Sleeping for {pause} seconds before next account...")
        await asyncio.sleep(pause)

        await progress_tracker.increment(1)
    except Exception as err:
        logger.error(f"{account_index} | Account flow failed: {err}")
        await progress_tracker.increment(1)


async def wrapper(function, config: src.utils.config.Config, *args, **kwargs):
    attempts = config.SETTINGS.ATTEMPTS
    for attempt in range(attempts):
        result = await function(*args, **kwargs)
        if isinstance(result, tuple) and result and isinstance(result[0], bool):
            if result[0]:
                return result
        elif isinstance(result, bool):
            if result:
                return True
        if attempt < attempts - 1:
            pause = random.randint(
                config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
            )
            logger.info(
                f"Sleeping for {pause} seconds before next attempt {attempt+1}/{config.SETTINGS.ATTEMPTS}..."
            )
            await asyncio.sleep(pause)
    return result


def task_exists_in_config(task_name: str, tasks_list: list) -> bool:
    for task in tasks_list:
        if isinstance(task, list):
            if task_exists_in_config(task_name, task):
                return True
        elif task == task_name:
            return True
    return False
