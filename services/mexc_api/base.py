import asyncio

from db_pack.repositories import GetUsersRepo


class BaseMexcAPI:
    def __init__(self, user_id: int, api_key: str, secret_key: str):
        self.user_id = user_id
        self.api_key = api_key
        self.secret_key = secret_key

    @classmethod
    async def create(cls, user_id: int):
        user_repo = GetUsersRepo()
        api_key = await user_repo.api_key(user_id)
        secret_key = await user_repo.secret_key(user_id)
        return cls(user_id, api_key, secret_key)


#
# async def main():
#     sd = await BaseMexcAPI.create(653500570)
#     print(sd.api_key)
#
# asyncio.run(main())
