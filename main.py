import configparser
import requests
import nextcord
from nextcord.ext import commands
from nextcord import utils
import json
import asyncio

# Config: Load config
config = configparser.ConfigParser()
config.read("config/config.txt")
dc_token = config["Discord"]["TOKEN"]


def get_dog_data(dog_num):
    URL = f""
    with requests.Session() as s:
        dog = s.get(URL).json()['data'][0]
    
    return dog

def get_all_dogs():
    URL = f"https://api.secretdogsnft.com/discordnames.php"
    with requests.Session() as s:
        dogs = s.get(URL).json()
    
    return dogs

# Bot
"""
class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # create the background task and run it in the background
        self.bg_task = self.loop.create_task(self.my_background_task())


    async def my_background_task(self):
        await self.wait_until_ready()
        #counter = 0
        channel = self.get_channel(log_channel) # channel ID goes here
        while not self.is_closed():
            #counter += 1
            await channel.send(f"Checking for sPunk ownership now... 🕵️ 🗃️")
            await asyncio.sleep(60*15) # task runs every 15 minutes
"""
intents = nextcord.Intents.all()
bot = commands.Bot(command_prefix='/',intents=intents)

#log_channel = bot.get_channel(log_channel_id)

@bot.command(pass_context=True)
async def register(ctx):
    if isinstance(ctx.channel, nextcord.channel.DMChannel):
        await ctx.send(f"Please only use this command in the Secret Dogs server.")
        return

    author = ctx.message.author

    log_channel = ctx.message.guild.system_channel

    try:
        await ctx.message.delete()
    except:
        await log_channel.send(f"Could not delete message by {author} (ID: {author.id})")

    await author.send(f"Retrieving your files now... 🕵️ 🗃️")

    

    try:

        all_dogs_raw = get_all_dogs()
        all_dogs = {}

        for x in all_dogs_raw:
            dog_id = x["dog_id"].split("_")[-1]
            if x["discord_name"] is None:
                discord_name = None
            elif x["discord_name"][0] == '@':
                discord_name = x["discord_name"][1:]
            else:
                discord_name = x["discord_name"]
            breed = x["breed"]
            all_dogs[dog_id]={"name":discord_name,"id":author.id}

            if discord_name == str(author):
                dog_discord = str(author)
                dog_id_owner = dog_id
        
    except:
        msg = await author.send(f'Error while retrieving Secret Dogs ownership, please contact Secret Dogs management')
        await log_channel.send(f"{author} (ID: {author.id}) tried to register a dog, but could not retrieve Secret Dogs ownership list")
        return


    if (dog_discord is None) or (dog_discord != str(author)):
        msg = await author.send(f'Could not find proof that you own a Secret Dog. Please ensure you have have added the full Discord handle to your Secret Dog, for example: secretDog#0000')
        await log_channel.send(f"{author} (ID: {author.id}) tried to register a dog, but does not own one")
        return

    with open(f'data/dogs.json', 'r') as file:
        dogs = json.load(file)
    
    dog_id = dog_id_owner
    old_owner = dogs.get(str(dog_id), None)

    dog_owner = "Secret Dog Owner"
    roles = [dog_owner]

    if old_owner is None:
        await log_channel.send(f"Registered dog {dog_id} to {author} (ID: {author.id})")
    elif old_owner["id"] != author.id:
        await log_channel.send(f"Transferred dog {dog_id} from {old_owner['name']} (ID: {old_owner['id']}) to {author} (ID: {author.id})")
    elif old_owner["id"] == author.id: 
        await log_channel.send(f"Dog {dog_id} is already registered to {author} (ID: {author.id})")

    dogs[str(dog_id)] = {"name":str(author),"id":author.id, "roles": roles}

    with open(f"data/dogs.json", 'w', encoding='utf-8') as jsonf:
        jsonf.write(json.dumps(dogs, indent=4))

    for role_name in roles:
        try:
            role = utils.get(ctx.message.guild.roles, name=role_name)
            if role not in author.roles:
                await author.add_roles(role)
                await log_channel.send(f"Added {role_name} to {author} (ID: {author.id})")
                if role_name != dog_owner:
                    msg = await author.send(f'{role_name} Access Granted! Congratulations on acquiring your {role_name} dog!')
                else:
                    msg = await author.send(f'Access Granted! Congratulations on acquiring your dog!')
            else:
                msg = await author.send(f'{author} you have already successfully requested {role_name} access previously!')
        except:
            msg = await author.send(f'Failed to grant {role_name} access to {author}, please contact secretDog Management.')
            await log_channel.send(f"Failed to add {role_name} to {author} (ID: {author.id})")
            return 
        
        try:
            if (old_owner is not None) and (old_owner["id"] != author.id):
                old_owners = {}
                for key,value in dogs.items():
                    value["dog_id"]=key
                    old_owner_value = old_owners.get(value["id"],[])
                    old_owner_value.append(value) 
                    old_owners[value["id"]]=old_owner_value
                
                if role_name in set(sum([x["roles"] for x in old_owners.get(old_owner["id"], [])], [])):
                    if role_name != dog_owner:
                        await log_channel.send(f'{old_owner["name"]} (ID: {old_owner["id"]}) still owns another {role_name} dog')
                    else:
                        await log_channel.send(f'{old_owner["name"]} (ID: {old_owner["id"]}) still owns another dog')
                    continue

                # Find User instance of the previous owner
                #old_owner_user = await bot.fetch_user(old_owner["id"])
                old_member = nextcord.utils.find(lambda m : m.id == old_owner["id"], ctx.message.guild.members)
                #await old_owner_user.remove_roles(role)
                await old_member.remove_roles(role)
                await log_channel.send(f'Removed {role_name} from {old_owner["name"]} (ID: {old_owner["id"]})')
        except:
            if old_owner is not None:
                await log_channel.send(f"Failed to remove {role_name} from {old_owner['name']} (ID: {old_owner['id']})")



@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

bot.run(dc_token)