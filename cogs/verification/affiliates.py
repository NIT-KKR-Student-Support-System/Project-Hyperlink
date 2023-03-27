from collections.abc import Iterable

import discord
from discord.ext import commands

from cogs.verification.utils import kick_old
from main import ProjectHyperlink
from models.student import Student


# TODO: Add command support to add field checks
class AffiliateVerification(commands.Cog):
    """The Great Wall of affiliate servers"""

    def __init__(self, bot: ProjectHyperlink):
        self.bot = bot

    async def cog_load(self) -> None:
        affiliate_guild_ids: list[dict[str, int]] = await self.bot.pool.fetch(
            """
            SELECT
                DISTINCT guild_id
            FROM
                guild_role
            """
        )
        self.affiliate_guild_ids: list[int] = [
            affiliate_guild_id["guild_id"] for affiliate_guild_id in affiliate_guild_ids
        ]
        await super().cog_load()

    @commands.Cog.listener()
    async def on_member_join_affiliate(
        self, member: discord.Member, student: Student | None
    ):
        """Triggered when a user joins a affiliate's Discord server"""
        guild_roles = await self.bot.pool.fetch(
            """
            SELECT
                field,
                value,
                role_ids
            FROM
                guild_role
            WHERE
                guild_id = $1
            """,
            member.guild.id,
        )

        for guild_role in guild_roles:
            try:
                value = student.__getattribute__(guild_role["field"])
            except AttributeError:
                self.bot.logger.warning(
                    f"Field `{guild_role['field']}` not found in table `guild_role` for guild `{member.guild.name}`"
                )
                continue

            if not isinstance(value, Iterable):
                value = str(value)

            if str(guild_role["value"]) not in value:
                continue

            roles = []
            for role_id in guild_role["role_ids"]:
                role = member.guild.get_role(role_id)
                if role is not None:
                    roles.append(role)
                    continue

                self.bot.logger.warning(
                    f"Role id `{role_id}` not found in table `guild_role` for guild_id `{member.guild.id}`"
                )

            if roles:
                await member.add_roles(*roles)

    @commands.Cog.listener()
    async def on_affiliate_member_change(
        self,
        student: Student,
        old_user_id: int | None,
    ):
        """Triggered when a student verifies"""
        assert student.discord_id is not None

        for affiliate_guild_id in self.affiliate_guild_ids:
            guild = self.bot.get_guild(affiliate_guild_id)
            assert guild is not None

            l10n = await self.bot.get_l10n(guild.id)
            await kick_old(guild, old_user_id, l10n)

            member = guild.get_member(student.discord_id)
            if member is None:
                continue

            self.bot.dispatch("member_join_affiliate", member, student)


async def setup(bot: ProjectHyperlink):
    await bot.add_cog(AffiliateVerification(bot))
