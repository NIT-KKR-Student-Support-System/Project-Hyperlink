import discord
import traceback

from cogs.verification.utils import authenticate
from main import ProjectHyperlink
from utils.utils import assign_student_roles


class VerificationView(discord.ui.View):
    def __init__(self, label: str, bot: ProjectHyperlink):
        super().__init__()

        button = VerificationButton(label, bot)
        self.add_item(button)


class VerificationButton(discord.ui.Button):
    def __init__(self, label, bot: ProjectHyperlink, **kwargs):
        super().__init__(label=label, style=discord.ButtonStyle.green, **kwargs)
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(VerificationModal(self.bot))


class VerificationModal(discord.ui.Modal, title="Verification"):
    roll = discord.ui.TextInput(
        label="Roll Number",
        placeholder="12022005",
        max_length=8,
    )

    def __init__(self, bot: ProjectHyperlink):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        # To please linter gods:
        assert isinstance(interaction.user, discord.Member)
        assert interaction.channel_id is not None
        assert self.roll.value is not None

        member = interaction.user

        student = await self.bot.pool.fetchrow(
            f"""
            SELECT
                section,
                name,
                email,
                batch,
                hostel_id
            FROM
                student
            WHERE
                roll_number = $1
            """,
            self.roll.value,
        )
        if not student:
            await interaction.response.send_message(
                f"{self.roll.value} was not found in our database. Please try again with a correct roll number. If you think this was a mistake, contact a moderator",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"An OTP has been sent to `{student['email']}`! Please paste the OTP below",
            ephemeral=True,
        )

        verified = await authenticate(
            self.roll.value,
            student["name"],
            student["email"],
            self.bot,
            member,
            interaction.channel_id,
            interaction.followup.send,
        )
        if verified is False:
            return

        await interaction.followup.send(
            f"Your email has been verified successfully, {member.mention}!"
        )

        await assign_student_roles(
            member,
            (
                student["section"][:2],
                student["section"][:4],
                student["section"][:3] + student["section"][4:].zfill(2),
                student["batch"],
                student["hostel_id"],
            ),
            self.bot.pool,
        )
        if member.display_name != student["name"]:
            first_name = student["name"].split(" ", 1)[0]
            await member.edit(nick=first_name)

    async def on_error(
        self, interaction: discord.Interaction, error: Exception
    ) -> None:
        await interaction.followup.send("Oops! Something went wrong.", ephemeral=True)

        traceback.print_exception(type(error), error, error.__traceback__)
