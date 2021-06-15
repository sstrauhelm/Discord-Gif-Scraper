import requests
import plyvel
import json
import re
import uuid
import os
import hashlib
from getpass import getuser

tenor_API_token = 'JJHDC7UK73EH' #Eat shit Tenor
#Also, if the script doesn't work without giving an exception it's probably because this API key expired.
#You can get a new one by going to https://tenor.com/developer/keyregistration.
#Once here, open up web inspector and go to the debugging menu.
#In the output console you should see a block with something like "locationSet: /developer/keyregistration" as the title.
#Expand that and scroll down. You should find a variable named key. If you got a new key, congrats otherwise you either did something wrong,
#weren't looking hard enough, or Tenor pulled some fucky shit.
#I'll probably make a script to automatically pull this API key later, I just don't give a fuck right now.

id_pat = re.compile(r'\d+$')
tenor_pat = re.compile(r'https?://tenor.com')
name_pat = re.compile(r'/[^/]+$')

db_path = f"/home/{getuser()}/.config/discord/Local Storage/leveldb"
gif_key = b'_https://discord.com\x00\x01GIFFavoritesStore'
out_folder = 'Discord gifs'

#Writes a gif to the output directory making sure that it isn't creating duplicates
#while also handling name collisions.
def create_gif(data, file_name):
    if os.path.exists(file_name):
        new_file_hash = hashlib.md5()
        new_file_hash.update(data)

        old_file_hash = hashlib.md5()
        with open(file_name, 'rb') as file:
            old_file_hash.update(file.read())

        if new_file_hash.digest() == old_file_hash.digest():
            return

        while os.path.exists(file_name):
            file_name = uuid.uuid4() + '.gif'

    with open(os.getcwd() + '/' + file_name, 'wb+') as file:
        file.write(data)


try:
    db = plyvel.DB(db_path)
except IOError:
    print("The database could not be opened.")
    print("This could be caused if Discord is currently running, or the wrong user has run the script.")
    exit(1)

j_data = json.loads(db.get(gif_key).decode('utf-8','ignore')[1:])

gif_list = j_data['_state']['favorites']

os.mkdir(out_folder)
os.chdir(out_folder)

tenor_gif_ids = []

for gif_desc in gif_list:
    gif_url = gif_desc['url']

    if tenor_pat.match(gif_url):
        tenor_gif_ids.append(id_pat.search(gif_url).group(0))
        continue
    
    file_name = name_pat.search(gif_url).group(0)
    if file_name[-4:].lower() != '.gif':
        file_name += '.gif'

    data = requests.get(gif_url).content

    create_gif(data, file_name)

for i in range(0,len(tenor_gif_ids)-1,50):
    gif_id_sublist = ','.join(tenor_gif_ids[i:i+50])
    tenor_bs = requests.get(f'https://g.tenor.com/v1/gifs?ids={gif_id_sublist}&media_filter=minimal&key=JJHDC7UK73EH')
    tenor_json_bs = json.loads(tenor_bs.content)
    for result in tenor_json_bs['results']:
        file_name = name_pat.search(result['itemurl']).group(0)
        data = requests.get(result['media'][0]['gif']['url']).content

        create_gif(data, file_name)