import os
import discord
import config
import asyncio
import requests
from bs4 import BeautifulSoup
from io import BytesIO

CHECK_INTERVAL = 60

intents = discord.Intents.all()
client = discord.Client(intents=intents)
LAST_URL_FILE = 'last_blog_url.txt'
HIYORI_BLOG_URL = 'https://www.hinatazaka46.com/s/official/diary/member/list?ima=0000&ct=17'
BASE_URL = 'https://www.hinatazaka46.com'

def load_last_blog_url():
    if os.path.exists(LAST_URL_FILE):
        with open(LAST_URL_FILE, 'r') as file:
            return file.read().strip()
    return None

def save_last_blog_url(url):
    with open(LAST_URL_FILE, 'w') as file:
        file.write(url)



async def check_website():
   
    await client.wait_until_ready()
    channel = client.get_channel(config.CHANNEL_ID)

    while not client.is_closed():
        print('Checking website...')
        last_blog_url = load_last_blog_url()
        response = requests.get(HIYORI_BLOG_URL)
        soup = BeautifulSoup(response.content, 'html.parser')

        blog_articles = soup.find_all('div', {'class': 'p-blog-article'})

        new_articles = []

        for article in blog_articles:
            detail_div = article.find('div', {'class': 'p-button__blog_detail'})
            if detail_div:
                detail_link = detail_div.find('a', {'class': 'c-button-blog-detail'})
                if detail_link:
                    blog_url = detail_link['href']
                    if blog_url == last_blog_url:
                        break
                    new_articles.append(article)

        new_articles.reverse()

        for article in new_articles:
            detail_div = article.find('div', {'class': 'p-button__blog_detail'})
            if detail_div:
                detail_link = detail_div.find('a', {'class': 'c-button-blog-detail'})
                if detail_link:
                    blog_url = detail_link['href']
                    images = []
                    text_div = article.find('div', {'class': 'c-blog-article__text'})
                    if text_div:
                        img_tags = text_div.find_all('img')
                        for img_tag in img_tags:
                            image_url = img_tag['src']
                            image_response = requests.get(image_url)
                            image_data = BytesIO(image_response.content)
                            images.append(discord.File(image_data, os.path.basename(image_url)))

                    if images:
                        await channel.send(f"ひよりブログが更新されました！\n{BASE_URL}{blog_url}", files=images)
                    else:
                        await channel.send(f"ひよりブログが更新されました！\n{BASE_URL}{blog_url}")

                    last_blog_url = blog_url
                    save_last_blog_url(last_blog_url)

        await asyncio.sleep(CHECK_INTERVAL)

@client.event
async def on_ready():
    print(f'Logged in as {client.user.name}')
    client.loop.create_task(check_website())

async def main():
    await client.start(config.DISCORD_TOKEN)

asyncio.run(main())
