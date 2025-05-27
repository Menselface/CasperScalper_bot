from infrastructure.db_pack.repositories import GetUsersRepo


class AdminChecker:
    @staticmethod
    async def check_user_is_admin(user_id: int):
        return await GetUsersRepo().user_is_admin_return(user_id)
