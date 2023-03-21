from typing import Any

import discord

from cogs.verification.utils import authenticate, post_verification_handler
from main import ProjectHyperlink

GUILD_IDS = {
    904633974306005033: 0,
    783215699707166760: 2024,
    915517972594982942: 2025,
}


class VerificationView(discord.ui.View):
    def __init__(self, label: str, bot: ProjectHyperlink, fmv):
        super().__init__(timeout=None)
        self.bot = bot

        button = VerificationButton(label, bot, fmv)
        self.add_item(button)

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        _: discord.ui.Item[Any],
    ) -> None:
        await self.bot.tree.on_error(interaction, error)


class VerificationButton(discord.ui.Button):
    def __init__(self, label, bot: ProjectHyperlink, fmv, **kwargs):
        super().__init__(label=label, style=discord.ButtonStyle.green, **kwargs)
        self.bot = bot
        self.fmv = fmv

    async def callback(self, interaction: discord.Interaction):
        assert isinstance(interaction.user, discord.Member)

        # TODO: Change this to use the check
        for role in interaction.user.roles:
            if role.name == "verified":
                raise discord.app_commands.CheckFailure("UserAlreadyVerified")

        await interaction.response.send_modal(VerificationModal(self.bot, self.fmv))


class VerificationModal(discord.ui.Modal, title="Verification"):
    roll = discord.ui.TextInput(
        label="Roll Number",
        placeholder="12022005",
        max_length=8,
        min_length=8,
    )

    def __init__(self, bot: ProjectHyperlink, fmv):
        super().__init__()
        self.bot = bot
        self.fmv = fmv

    async def on_submit(self, interaction: discord.Interaction):
        assert isinstance(interaction.user, discord.Member)
        assert self.roll.value is not None

        await verify(self.bot, interaction, interaction.user, self.roll.value)

    async def on_error(
        self, interaction: discord.Interaction, error: Exception
    ) -> None:
        await self.bot.tree.on_error(interaction, error)
