TASKS = [
    "CRUSTY_SWAP", "crystal_swap",
]

# MAGICEDEN WORKS ONLY WITH THESE NFT https://magiceden.io/mint-terminal/monad-testnet

CRUSTY_SWAP = [
    "crusty_refuel",
    # "crusty_sell",
    # "crusty_refuel_from_one_to_all",
]

FAUCET = [
    "faucet",
]


NERZO_SOULBOUND = [
    "nerzo_soulbound",
]

MONAIGG = [
    "monaigg",
]

"""
EN:
You can create your own task with the modules you need 
and add it to the TASKS list or use our ready-made preset tasks.

( ) - Means that all of the modules inside the brackets will be executed 
in random order
[ ] - Means that only one of the modules inside the brackets will be executed 
on random
SEE THE EXAMPLE BELOW:

RU:
Вы можете создать свою задачу с модулями, которые вам нужны, 
и добавить ее в список TASKS, см. пример ниже:

( ) - означает, что все модули внутри скобок будут выполнены в случайном порядке
[ ] - означает, что будет выполнен только один из модулей внутри скобок в случайном порядке
СМОТРИТЕ ПРИМЕР НИЖЕ:

CHINESE:
你可以创建自己的任务，使用你需要的模块，
并将其添加到TASKS列表中，请参见下面的示例：

( ) - 表示括号内的所有模块将按随机顺序执行
[ ] - 表示括号内的模块将按随机顺序执行

--------------------------------
!!! IMPORTANT !!!
EXAMPLE | ПРИМЕР | 示例:

TASKS = [
    "CREATE_YOUR_OWN_TASK",
]
CREATE_YOUR_OWN_TASK = [
    "crusty_refuel",
    ("apriori", "magma", "shmonad"),
    ["ambient", "izumi", "bean"],
    "collect_all_to_monad",
]
--------------------------------


BELOW ARE THE READY-MADE TASKS THAT YOU CAN USE:
СНИЗУ ПРИВЕДЕНЫ ГОТОВЫЕ ПРИМЕРЫ ЗАДАЧ, КОТОРЫЕ ВЫ МОЖЕТЕ ИСПОЛЬЗОВАТЬ:
以下是您可以使用的现成任务：
"""


BRIDGE_AND_SWAPS = [
    "crusty_refuel",
    ("izumi", "ambient", "bean", "swaps"),
    "collect_all_to_monad",
]


FULL_TASK = [
    ["izumi", "swaps", "ambient", "bean", "skip"],
    ["izumi", "swaps", "ambient", "bean", "skip", "skip", "skip"],
    ["izumi", "swaps", "ambient", "bean", "skip", "skip", "skip"],
    ["izumi", "lilchogstars", "bean", "swaps", "skip"],
    ["ambient", "izumi", "bean", "skip", "skip"],
    "collect_all_to_monad",
    ["apriori", "magma", "shmonad", "kintsu", "skip", "skip"],
    ["apriori", "magma", "shmonad", "kintsu", "skip"],
    ["ambient", "izumi", "bean", "magiceden", "monadking", "skip"],
    ["magiceden", "monadking", "skip", "skip"],
    "collect_all_to_monad",
    ["ambient", "izumi", "bean", "magiceden", "monadking", "skip"],
    ["izumi", "swaps", "ambient", "bean", "skip", "skip", "skip"],
    ["owlto", "skip", "skip"],
    ["izumi", "swaps", "ambient", "bean", "skip", "skip"],
    "logs",
]

BRIDGE_SEPOLIA_AND_CONVERT_TO_MON = [
    "testnet_bridge",
    "orbiter",
    "collect_all_to_monad",
]

SWAPS_TASK = [
    ("izumi", "ambient", "bean", "swaps"),
    "collect_all_to_monad",
]

STAKING_TASK = [
    ("apriori", "magma", "shmonad", "kintsu"),
]

EXCHANGE_TASK = [
    "cex_withdrawal",
]

EXCHANGE_AND_TESTNET_BRIDGE_TASK = [
    "cex_withdrawal",
    "testnet_bridge",
    "orbiter",
    "collect_all_to_monad",
]

EXCHANGE_AND_CRUSTY_SWAP_TASK = [
    "cex_withdrawal",
    "crusty_refuel",
]

EXCHANGE_AND_MEMEBRIDGE_TASK = [
    "cex_withdrawal",
    "memebridge",
]


CRYSTAL_SWAP = [
    "crystal_swap",  # Maps to CrystalSwap module
]

# FAUCETS
# "disperse_farm_accounts" - disperse tokens from farm accounts to main accounts | keys_for_faucet.txt -> private_keys.txt
# "disperse_from_one_wallet" - disperse tokens from one wallet to all other wallets | keys_for_faucet.txt (first wallet) -> private_keys.txt

# SWAPS
# "collect_all_to_monad" - swap all tokens to native token (MON)
# "swaps" - testnet.monad.xyz/ page token swaps
# "bean" - swap tokens on Bean DEX
# "ambient" - swap tokens on Ambient DEX
# "izumi" - swap tokens on Izumi DEX
# "madness_swaps" - swap tokens on madness.finance/swap

# STAKES
# "apriori" - stake MON token
# "magma" - stake MON token on Magma
# "shmonad" - buy and stake shmon on shmonad.xyz | LOOK SETTINGS BELOW
# "kintsu" - stake MON token on kintsu.xyz/
# "nostra" - deposit, borrow, repay, withdraw
# "multiplifi" - stake USDC token on https://testnet.multipli.fi/?stake-tab=stake
# "flapsh" - buy memcoin for MON on https://monad.flap.sh/board

# MINT
# "magiceden" - mint NFT on magiceden.io
# "owlto" - deploy contract on Owlto
# "lilchogstars" - mint NFT on testnet.lilchogstars.com/
# "monadking" - mint NFT on nerzo.xyz/monadking
# "monadking_unlocked" - mint NFT on www.nerzo.xyz/unlocked
# "easynode_deploy" - deploy contract on easynode.xyz
# "onchaingm_deploy" - deploy contract on onchaingm.com/deploy
# "morkie_monhog" - mint NFT on https://morkie.xyz/monhog # price 0.5 MON
# "morkie_monarch" - mint NFT on https://morkie.xyz/monarch # price 0.1 MON
# "monaigg" - mint NFT on https://monai.gg/nft
# "nerzo_soulbound" - mint NFT on https://nerzo.xyz/soulbound

# REFUEL
# "crusty_refuel" - refuel from arbitrum, optimism, base to monad
# "gaszip" - gaszip refuel from arbitrum, optimism, base to monad
# "orbiter" - bridge ETH from Sepolia to Monad via Orbiter
# "memebridge" - memebridge refuel from arbitrum, optimism, base to monad

# CEX WITHDRAWAL
# "cex_withdrawal" - withdraw tokens from cex

# GAMES
# "frontrunner" - play frontrunner game

# OTHER
# "logs" - show logs: MON balance | number of transactions | avarage balance | avarage number of transactions
# "nad_domains" - register random domain on nad.domains
# "monsternad_whitelist" - add to monsternad whitelist airdrop.monsternad.xyz/dashboard/
