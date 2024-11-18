from aiohttp.web_response import json_response
from aiohttp.web_urldispatcher import View


class UserLoginView(View):

    async def get(self):
        return json_response(data={"data": "hello"})