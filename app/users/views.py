from aiohttp.web_response import json_response

from app.web.app import View


class UserAddView(View):

    async def post(self):
        data = await self.request.json()
        user = await self.request.app.store.users.create_user(data["id"], data["username"], data["name"])

        return json_response(data={"data": "hello"})