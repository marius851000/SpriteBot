import TrackerUtils
from typing import TYPE_CHECKING, List
from .BaseCommand import BaseCommand
from Constants import PermissionLevel
import discord
from discord import AllowedMentions


if TYPE_CHECKING:
    from SpriteBot import SpriteBot, BotServer

class ChangeRessourceLicense(BaseCommand):
    def __init__(self, spritebot: "SpriteBot", resource_type: str) -> None:
        self.sprite_bot = spritebot
        self.resource_type = resource_type

    def getRequiredPermission(self) -> PermissionLevel:
        # there are still restriction enforced during execution
        return PermissionLevel.EVERYONE

    def getCommand(self) -> str:
        return f"change{self.resource_type}license"

    def getSingleLineHelp(self, server_config: "BotServer") -> str:
        return f"Update the license of a contributor’s work on {self.resource_type}."

    def getMultiLineHelp(self, server_config: "BotServer") -> str:
        return f"`{self.getCommand()} <Name> <License ID> <Pokemon Name> [Pokemon Form] [Shiny] [Gender]`\n" \
        f"Update a {self.resource_type} contributions of an author to be under a specific license\n" \
        "Contributors may only change the license if they are the only contributor to it (excluding Unspecified license or other already present identical license). " \
        "Other changes will need to be reviewed and executed by a reviewer.\n" \
        "`Name` - Name of the author (such as a Discord mention or the absentee profile id)\n" \
        "`License ID` - The ID of the license, as specified in the info channel\n" \
        "`Pokemon Name` - Name of the Pokemon\n" \
        "`Form Name` - [Optional] Form name of the Pokemon\n" \
        f"`Shiny` - [Optional] Specifies if you want the shiny {self.resource_type} or not\n" \
        "`Gender` - [Optional] Specifies the gender of the Pokemon\n" \
        + self.generateMultiLineExample(server_config.prefix, [
            "@Caitemis CC_BY_4 Sulphur_Nimbus"
        ])

    async def executeCommand(self, msg: discord.Message, args: List[str]):
        if len(args) < 3:
            await msg.reply("Not enough arguments provided")
            return

        user_permission = await self.sprite_bot.getUserPermission(msg.author, msg.guild)

        contributor_mention = args[0]
        new_license_id = args[1]
        name_seq = [TrackerUtils.sanitizeName(i) for i in args[2:]]
        
        # fetch data required to perform among other permission check. Better avoid await to avoid issue with race condition.
        full_idx = TrackerUtils.findFullTrackerIdx(self.sprite_bot.tracker, name_seq, 0)
        if full_idx is None:
            await msg.reply("No such Pokemon.")
            return
        
        mon_path = TrackerUtils.getDirFromIdx(self.sprite_bot.config.path, self.resource_type, full_idx)
        credits = TrackerUtils.getFileCredits(mon_path)

        if not user_permission.canPerformAction(PermissionLevel.STAFF):
            if not TrackerUtils.are_credit_name_identical(contributor_mention, msg.author.mention):
                await msg.reply("You do not have permission to edit license of other person.")
                return
            for entry in credits:
                if entry.license == TrackerUtils.UNSPECIFIED_LICENSE \
                    or TrackerUtils.are_credit_name_identical(entry.name, msg.author.mention) \
                    or entry.license == new_license_id:
                    pass
                else:
                    await msg.reply(
                        f"This {self.resource_type} is also credited to {entry.name}. Please ask a staff member to change your license.",
                        allowed_mentions=AllowedMentions(users=[msg.author])
                    )
                    return

        # permission granted

        nb_license_replaced = 0
        for entry in credits:
            if TrackerUtils.are_credit_name_identical(entry.name, contributor_mention):
                nb_license_replaced += 1
                entry.license = new_license_id

        if nb_license_replaced == 0:
            await msg.reply(f"No contribution from {contributor_mention} present on this {self.resource_type}.")
            return

        TrackerUtils.writeCredits(mon_path, credits)
        await msg.reply(f"The {self.resource_type} license of {contributor_mention} contributions has been set to {new_license_id}.")
