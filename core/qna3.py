import json
import aiohttp
import asyncio
from data import config
from core.utils import web3_utils
from fake_useragent import UserAgent


class Qna3:
    def __init__(self, key: str, proxy: str):
        self.auth_token = self.user_id = None
        self.web3_utils = web3_utils.Web3Utils(key=key, http_provider=config.BNB_RPC)
        self.proxy = f"http://{proxy}" if proxy is not None else None

        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'ua-UA,ru;q=0.8,en-US;q=0.5,en;q=0.3',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Host': 'api.qna3.ai',
            'Origin': 'https://qna3.ai',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'TE': 'trailers',
            'User-Agent': UserAgent(os='windows').random,
            'x-lang': 'english',
        }

        self.session = aiohttp.ClientSession(headers=headers, trust_env=True)

    async def login(self):
        address = self.web3_utils.acct.address
        signature = self.web3_utils.get_signed_code("AI + DYOR = Ultimate Answer to Unlock Web3 Universe")

        params = {
            'invite_code': config.REF_CODE,
            'signature': signature,
            'wallet_address': address
        }

        resp = await self.session.post(url='https://api.qna3.ai/api/v2/auth/login?via=wallet', json=params, proxy=self.proxy)
        resp_txt = await resp.json()

        self.auth_token = 'Bearer ' + resp_txt.get('data').get('accessToken')
        self.user_id = resp_txt.get('data').get("user").get("id")

        self.session.headers['Authorization'] = self.auth_token
        self.session.headers['X-Id'] = self.user_id
        return True

    async def get_points_to_claim(self):
        while True:
            params = {
                "query": "query loadUserDetail($cursored: CursoredRequestInput!) {\n  userDetail {\n    checkInStatus {\n      checkInDays\n      todayCount\n    }\n    credit\n    creditHistories(cursored: $cursored) {\n      cursorInfo {\n        endCursor\n        hasNextPage\n      }\n      items {\n        claimed\n        extra\n        id\n        score\n        signDay\n        signInId\n        txHash\n        typ\n      }\n      total\n    }\n    invitation {\n      code\n      inviteeCount\n      leftCount\n    }\n    origin {\n      email\n      id\n      internalAddress\n      userWalletAddress\n    }\n    externalCredit\n    voteHistoryOfCurrentActivity {\n      created_at\n      query\n    }\n    ambassadorProgram {\n      bonus\n      claimed\n      family {\n        checkedInUsers\n        totalUsers\n      }\n    }\n  }\n}",
                "variables": {
                    "cursored": {
                        "after": "",
                        "first": 20
                    },
                    "headersMapping": {
                        "Authorization": self.auth_token,
                        "x-id": self.user_id,
                        "x-lang": "english",
                    }
                }
            }

            resp = await self.session.post(url='https://api.qna3.ai/api/v2/graphql', json=params, proxy=self.proxy)
            resp_json = await resp.json()

            if resp_json:
                return resp_json.get('data').get('userDetail').get('ambassadorProgram').get('bonus')
            await asyncio.sleep(30)

    async def claim_points(self):
        resp = await self.session.post('https://api.qna3.ai/api/v2/my/claim-all', json={})
        resp_json = (await resp.json()).get('data')

        data = self.generate_data(resp_json.get('amount'), resp_json.get('signature').get('nonce'), resp_json.get('signature').get('signature'))
        tx = {
            "from": self.web3_utils.acct.address,
            "to": "0xB342e7D33b806544609370271A8D074313B7bc30",
            "value": 0,
            "nonce": self.web3_utils.w3.eth.get_transaction_count(self.web3_utils.acct.address),
            "gasPrice": self.web3_utils.w3.to_wei(config.GWEI, 'gwei'),
            "chainId": 56,
            "data": data,
        }

        tx["gas"] = int(self.web3_utils.w3.eth.estimate_gas(tx))
        tx = self.web3_utils.w3.eth.account.sign_transaction(tx, self.web3_utils.acct.key.hex())
        transaction_hash = self.web3_utils.w3.eth.send_raw_transaction(tx.rawTransaction).hex()
        wait_tx = self.web3_utils.w3.eth.wait_for_transaction_receipt(transaction_hash)

        return wait_tx.status == 1, transaction_hash, resp_json.get('amount')

    def generate_data(self, amount, nonce, signature):
        amount_hex = self.web3_utils.w3.to_hex(amount)[2:]
        amount = '0' * (64 - len(amount_hex)) + amount_hex

        nonce_hex = self.web3_utils.w3.to_hex(nonce)[2:]
        nonce = '0' * (64 - len(nonce_hex)) + nonce_hex

        return f"0x624f82f5{amount}{nonce}00000000000000000000000000000000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000000000041{signature[2:]}00000000000000000000000000000000000000000000000000000000000000"

    async def logout(self):
        await self.session.close()
