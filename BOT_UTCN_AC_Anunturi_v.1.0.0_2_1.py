import discord
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup
import re

channel_id = 1147223076237492295

# Set up your Discord bot
bot_token = "token-to-be-inserted"

# Define your intents including Message Content
intents = discord.Intents.default()
intents.typing = True
intents.presences = True
intents.message_content = True  # Add this line to enable message content intent

# Create a bot instance with the command extension and intents
bot = commands.Bot(command_prefix="!", intents=intents)

# Create a variable to store the last announcements message ID
last_announcements_message_id = None
# dorel: create a set to store previously displayed announcements
previous_announcements = set()


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    # dorel: get the previously posted announcements
    await initialize_previous_announcements()
    # Start the announcements refresh task when the bot is ready
    refresh_announcements.start()


@tasks.loop(seconds=10)
async def refresh_announcements():
    global last_announcements_message_id

    try:
        # Scrape the website for the announcements section
        url = "https://ac.utcluj.ro/acasa.html"
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the specific HTML section containing announcements
        announcements_section = soup.find('div', class_='col-md-6 col-lg-6 pt-md-0 pt-5')

        if announcements_section:
            # Extract each announcement and collect them in a list
            # dorel: modified announcements to be a set
            new_announcements = set()

            # Find all <a> elements within the announcements section
            for link in announcements_section.find_all('a'):
                announcement_text = link.get_text()
                announcement_href = link.get('href')

                # Prepend the base URL to create a valid URL
                announcement_url = f"https://ac.utcluj.ro/{announcement_href}"

                # dorel: create an unique way to identify announcements
                announcement_id = f"{announcement_text}-{announcement_url}"

                if announcement_id not in previous_announcements:
                    new_announcements.add(announcement_id)
                    # Create an embed for each announcement
                    embed = discord.Embed(title=announcement_text, url=announcement_url)

                    # dorel: sending the new announcements as soon at was found
                    message = await bot.get_channel(channel_id).send(embed=embed)
                    last_announcements_message_id = message.id

                # dorel: add the new announcements to the list of all found announcements
                previous_announcements.update(new_announcements)

        else:
            await bot.get_channel(channel_id).send("The announcements section was not found on the website.")

    except Exception as e:
        await bot.get_channel(channel_id).send("An error occurred while fetching the announcements.")
        print(f"Error: {e}")


async def initialize_previous_announcements():
    global previous_announcements

    try:
        channel = bot.get_channel(channel_id)
        async for message in channel.history():
            for embed in message.embeds:
                announcement_id = f"{embed.title}-{embed.url}"
                previous_announcements.add(announcement_id)

    except Exception as e:
        print(f"Error initializing previous announcements: {e}")

# Start the bot with your token
bot.run(bot_token)
