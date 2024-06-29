import numpy as np
import discord as d
from discord.ext import commands as Astro
from discord import app_commands as app
import random

class TicTacToeView(d.ui.View):
    def __init__(self, board, player_mark, bot_mark):
        super().__init__(timeout=45)  # Set timeout to 45 seconds
        self.board = board
        self.player_mark = player_mark
        self.bot_mark = bot_mark
        self.moves = []  # To keep track of the moves
        self.add_buttons()
        self.add_resign_button()

    def add_buttons(self):
        for i in range(3):
            for j in range(3):
                button = d.ui.Button(label="\u200b", row=i, style=d.ButtonStyle.gray)
                button.callback = self.button_callback
                button.custom_id = f"{i},{j}"
                self.add_item(button)

    def add_resign_button(self):
        resign_button = d.ui.Button(label="\u200b", style=d.ButtonStyle.blurple, emoji='🚩', row=4)
        resign_button.callback = self.resign_callback
        self.add_item(resign_button)

    async def resign_callback(self, interaction: d.Interaction):
        await interaction.response.edit_message(content="You resigned! Bot wins!", view=self)
        self.stop()

    async def button_callback(self, interaction: d.Interaction):
        i, j = map(int, interaction.data['custom_id'].split(','))
        if self.board[i][j] == ' ':
            self.board[i][j] = self.player_mark
            self.children[i*3+j].label = self.player_mark
            self.children[i*3+j].disabled = True
            self.children[i*3+j].style = d.ButtonStyle.red if self.player_mark == 'X' else d.ButtonStyle.green
            self.moves.append((i, j))
            if len(self.moves) > 6:
                old_i, old_j = self.moves.pop(0)
                self.board[old_i][old_j] = ' '
                self.children[old_i*3+old_j].label = "\u200b"
                self.children[old_i*3+old_j].disabled = False
                self.children[old_i*3+old_j].style = d.ButtonStyle.gray
            if len(self.moves) == 6:
                next_old_i, next_old_j = self.moves[0]
                self.children[next_old_i*3+next_old_j].style = d.ButtonStyle.blurple
            if self.check_win(self.player_mark):
                await interaction.response.edit_message(content="You win!", view=self)
                self.stop()
            else:
                await interaction.response.edit_message(view=self)
                await self.bot_move(interaction)
        else:
            await interaction.response.send_message("Invalid move!", ephemeral=True)

    async def bot_move(self, interaction: d.Interaction):
        if self.is_board_full():
            await interaction.edit_original_response(content="It's a tie!", view=self)
            self.stop()
            return

        best_score = float('-inf')
        best_move = None
        for i in range(3):
            for j in range(3):
                if self.board[i][j] == ' ':
                    self.board[i][j] = self.bot_mark
                    score = self.minimax(self.board, 0, False)
                    self.board[i][j] = ' '
                    if score > best_score:
                        best_score = score
                        best_move = (i, j)

        if best_move:
            i, j = best_move
            self.board[i][j] = self.bot_mark
            self.children[i*3+j].label = self.bot_mark
            self.children[i*3+j].disabled = True
            self.children[i*3+j].style = d.ButtonStyle.red if self.bot_mark == 'X' else d.ButtonStyle.green
            self.moves.append((i, j))
            if len(self.moves) > 6:
                old_i, old_j = self.moves.pop(0)
                self.board[old_i][old_j] = ' '
                self.children[old_i*3+old_j].label = "\u200b"
                self.children[old_i*3+old_j].disabled = False
                self.children[old_i*3+old_j].style = d.ButtonStyle.gray
            if len(self.moves) == 6:
                next_old_i, next_old_j = self.moves[0]
                self.children[next_old_i*3+next_old_j].style = d.ButtonStyle.blurple
            if self.check_win(self.bot_mark):
                await interaction.edit_original_response(content="Bot wins!", view=self)
                self.stop()
            else:
                await interaction.edit_original_response(view=self)

    def minimax(self, board, depth, is_maximizing):
        if self.check_win(self.bot_mark):
            return 10 - depth
        elif self.check_win(self.player_mark):
            return depth - 10
        elif self.is_board_full():
            return 0

        if is_maximizing:
            best_score = float('-inf')
            for i in range(3):
                for j in range(3):
                    if board[i][j] == ' ':
                        board[i][j] = self.bot_mark
                        score = self.minimax(board, depth + 1, False)
                        board[i][j] = ' '
                        best_score = max(score, best_score)
            return best_score
        else:
            best_score = float('inf')
            for i in range(3):
                for j in range(3):
                    if board[i][j] == ' ':
                        board[i][j] = self.player_mark
                        score = self.minimax(board, depth + 1, True)
                        board[i][j] = ' '
                        best_score = min(score, best_score)
            return best_score

    def is_board_full(self):
        return all(self.board[i][j] != ' ' for i in range(3) for j in range(3))

    def check_win(self, mark):
        for i in range(3):
            if all(self.board[i][j] == mark for j in range(3)):
                return True
            if all(self.board[j][i] == mark for j in range(3)):
                return True
        if all(self.board[i][i] == mark for i in range(3)):
            return True
        if all(self.board[i][2-i] == mark for i in range(3)):
            return True
        return False

    async def on_timeout(self):
        await self.message.edit(content="You ran out of time, guess you lost!", view=self)
        self.stop()

class InfiniteTicTacToe(Astro.Cog):
    def __init__(self, bot):
        self.bot = bot

    infinite = app.Group(name="infinite", description="Infinite Tic Tac Toe")

    @infinite.command(name="tictactoe", description="Start a game of tictactoe")
    async def inftictactoe(self, interaction: d.Interaction):
        board = [[' ' for _ in range(3)] for _ in range(3)]
        player_mark, bot_mark = random.sample(['X', 'O'], 2)
        view = TicTacToeView(board, player_mark, bot_mark)
        message = await interaction.response.send_message(f"Let's play Tic-Tac-Toe! You are {player_mark}, I am {bot_mark}.", view=view)
        view.message = message  # Assign the message object to view.message
        if bot_mark == 'X':
            board[0][0] = bot_mark
            view.children[0].label = bot_mark
            view.children[0].disabled = True
            view.children[0].style = d.ButtonStyle.red
            view.moves.append((0, 0))
            await interaction.edit_original_response(view=view)

async def setup(bot):
    await bot.add_cog(InfiniteTicTacToe(bot))

