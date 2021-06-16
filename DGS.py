import requests
import sys
import plyvel
import json
import re
import uuid
import os
import hashlib
from platform import system
from shutil import copytree, rmtree

tenor_API_token = 'JJHDC7UK73EH'
suffix = "/discord/Local Storage/leveldb"

id_pat = re.compile(r'\d+$')
tenor_pat = re.compile(r'https?://tenor.com')
name_pat = re.compile(r'/[^/]+$')

os_type = system()

db_path = os.path.expanduser('~')

if os_type == "Linux":
    db_path += ("/.config" + suffix)
elif os_type == "Windows":
    db_path += ("/AppData/Roaming" + suffix)

gif_key = b'_https://discord.com\x00\x01GIFFavoritesStore'
out_folder = 'Discord gifs'

#Writes a gif to the output directory making sure that it isn't creating duplicates via md5 comparisons
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

#Work directory prepping
working_dir = os.path.join(os.getcwd(), out_folder)
db_copy = os.path.join(working_dir, 'leveldb')

if not os.path.exists(out_folder):
    os.mkdir(out_folder)

os.chdir(working_dir)

if os.path.exists(db_copy):
    rmtree(db_copy)

copytree(db_path, db_copy)

#Opening copied leveldb files
try:
    db = plyvel.DB(db_copy)
except IOError as e:
    print("Working files could not be opened")
    print("Error: %s" % e)
    sys.exit(1)


j_data = json.loads(db.get(gif_key).decode('utf-8','ignore')[1:])
db.close()

gif_list = j_data['_state']['favorites']


tenor_gif_ids = []
normal_gif_urls = []


for gif_desc in gif_list:
    gif_url = gif_desc['url']

    if tenor_pat.match(gif_url):
        tenor_gif_ids.append(id_pat.search(gif_url).group(0))
    else:
        normal_gif_urls.append(gif_url)


#Normal gif section
for gif_url in normal_gif_urls:
    
    file_name = name_pat.search(gif_url).group(0)

    if file_name[-4:].lower() != '.gif':
        file_name += '.gif'

    data = requests.get(gif_url).content

    create_gif(data, file_name)

total_gifs = len(normal_gif_urls) + len(tenor_gif_ids)

if total_gifs == 0:
    print("You have no gifs saved.")
    sys.exit(0)

#Tenor gif section
for i in range(0,len(tenor_gif_ids)-1,50):
    #In order to download gifs from tenor by ID, one has to first make a query with their API and take the gif's actual link from there.
    #Tenor allows a max of 50 IDs to be searched at once, so to reduce the number of requests being made I decided to take advantage of that
    gif_id_sublist = ','.join(tenor_gif_ids[i:i+50])
    tenor_bs = requests.get(f'https://g.tenor.com/v1/gifs?ids={gif_id_sublist}&media_filter=minimal&key={tenor_API_token}')
    tenor_json_bs = json.loads(tenor_bs.content)
    for result in tenor_json_bs['results']:
        file_name = name_pat.search(result['itemurl']).group(0)
        data = requests.get(result['media'][0]['gif']['url']).content

        create_gif(data, file_name)
        
print(f"Now downloading {total_gifs} gif{'s' if total_gifs > 1 else ''}...")
print("Done!")
