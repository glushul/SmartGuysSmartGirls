from aiohttp.web_response import json_response
from alembic.command import current

from app.store.bot.state_controller import GameStates
from app.store.database.sqlalchemy_base import AnswerModel
from app.web.app import View


class GameListView(View):

    async def get(self):
        games = await self.store.games.list_games()

        result = {"active_games": [], "ended_games": []}
        for game in games:
            dict_game = {
                "id": game.id,
                "chat_id": game.chat_id,
                "theme_id": game.theme_id,
                "answer_time": game.answer_time,
                "state": game.state,
                "current_question_id": game.current_question_id,
            }
            if game.state == GameStates.GAME_ENDED.value:
                result["ended_games"].append(dict_game)
            else:
                result["active_games"].append(dict_game)

        return json_response(data=result)


class ParticipantListView(View):

    async def get(self):
        game_id = int(self.request.query.get("game_id"))

        game = await self.store.games.get_game_by_game_id(game_id=game_id)
        participants = await self.store.participants.get_participants_by_game_id(game_id=game_id)

        if game is None:
            return json_response(status=401, reason="Game doesn't exist")
        result = {"participants": []}
        for participant in participants:
            participant_data = {
                "game_id": participant.game_id,
                "user_id": participant.user_id,
                "level": participant.level,
                "correct_answers": participant.correct_answers,
                "incorrect_answers": participant.incorrect_answers
            }
            if game.state == GameStates.GAME_ENDED.value:
                if participant.current:
                    participant_data["state"] = "Победитель"
                else:
                    participant_data["state"] = "Проигравший"
            result["participants"].append(participant_data)
        return json_response(data=result)

