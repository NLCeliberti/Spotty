import discord
from discord.ext.commands import Bot
from discord.ext import commands

import spotipy
import spotipy.util as util

import sys
import random
import random_word
import data

username = 'z4m7ayxl6bzz5i9zjp0bz8133'
scope = 'playlist-modify-public user-modify-playback-state'
sp = None
playlistFile = '/home/pi/Spotty/playlists.txt'
wordRandomizer = random_word.RandomWords()

Client = discord.Client()
bot_prefix= "!"
bot = commands.Bot(command_prefix=bot_prefix)
bot.remove_command('help')

@bot.event
async def on_ready():
    print("Bot Online!")
    print("Name: {}".format(bot.user.name))
    print("ID: {}".format(bot.user.id))

    await bot.change_presence(activity=discord.Game(name='Spot.py Bot'))

    global sp
    with open('/home/pi/Spotty/secrets.txt', 'r') as f:
        client_id = f.readline().replace('\n', '')
        client_secret = f.readline().replace('\n', '')
    token = util.prompt_for_user_token(username, scope, client_id=client_id, client_secret=client_secret, redirect_uri='http://localhost:8888/callback')  # z4m7ayxl6bzz5i9zjp0bz8133 doodads
    if token:
        sp = spotipy.Spotify(auth=token)

@bot.command(pass_context=True)
async def help(ctx):
    msg = []
    msg.append('```yaml\n')
    msg.append('# Anything with & is required')
    msg.append('# Anything with * is optional')
    msg.append('!help ; This message you fucking idiot')
    msg.append('!add &name &playlistID ; adds a playlist to the known list. ID can be playlist link or URI')
    msg.append('!show ; shows the list of known playlists')
    msg.append('!shuffle &playlist ; shuffles a playlist. ')
    msg.append('!top &playlist *num ; gathers all of the artists from a playlist then gets there top [num] tracks and makes a playlist.')
    msg.append('!remove_live &playlist ; Probably removes all live sounds from a playlist [UNTESTED BADDEV]')
    msg.append('!sort &playlist &metrics ; Sorts a playlist based off of spotify metrics. !metrics for more information')
    msg.append('!q &song ; queues a song onto Nick\'s queue')
    msg.append('\n```')
    await ctx.channel.send('\n'.join(msg))

@bot.command(pass_context=True)
async def add(ctx, name, id):
    if 'open' in id:
        id = id.split('?')[0].split('/')[-1]
    elif 'playlist' in id:
        id = id.split(':')[2]
    count = 0
    with open(playlistFile, 'r+') as out:
        for _ in out:
            count += 1
        out.write(f'{name} {id}\n')
    await ctx.channel.send(f'```ini\nAdded Playlist: [{count}] {name} {id}```')

@bot.command(pass_context=True)
async def show(ctx):
    count = 0
    with open(playlistFile, 'r') as f:
        msg = ['```ini\n']
        for _ in f:
            name = _.split(' ')[0]
            msg.append(f'[{count}] {name}\n')
            count += 1
        msg.append('\n```')
        await ctx.channel.send(''.join(msg))

@bot.command(pass_context=True)
async def shuffle(ctx, from_playlist):
    playlists = await resolve_playlist(ctx, from_playlist, 'new')
    shuffle_playlist(playlists[0], playlists[1])
    await ctx.channel.send(f'Check out your new playlist! \n{get_playlist_link(playlists[1])}')

@bot.command(pass_context=True)
async def top(ctx, from_playlist, num=5, shuf=True):
    playlists = await resolve_playlist(ctx, from_playlist, 'new')
    create_top_tracks_playlist(playlists[0], playlists[1], num, shuf)
    await ctx.channel.send(f'Check out your new playlist! \n{get_playlist_link(playlists[1])}')

@bot.command(pass_context=True)
async def remove_live(ctx, from_playlist):
    playlists = await resolve_playlist(ctx, from_playlist, 'new')
    remove_live_tracks(playlists[0], playlists[1])
    await ctx.channel.send(f'Check out your new playlist! \n{get_playlist_link(playlists[1])}')

@bot.command(pass_context=True)
async def sort(ctx, from_playlist, *metrics):
    playlists = await resolve_playlist(ctx, from_playlist, 'new')
    sort_by_metrics(playlists[0], playlists[1], metrics)
    await ctx.channel.send(f'Check out your new playlist! \n{get_playlist_link(playlists[1])}')

@bot.command(pass_context=True)
async def metrics(ctx):
    msg = []
    msg.append('```yaml\n')
    msg.append('Metrics:')
    msg.append('  - acousticness')
    msg.append('  - danceability')
    msg.append('  - energy')
    msg.append('  - instrumentalness')
    msg.append('  - liveness')
    msg.append('  - loudness')
    msg.append('  - speechiness')
    msg.append('  - tempo')
    msg.append('  - valence')
    msg.append('')
    msg.append('Danceability describes how suitable a track is for dancing based on a combination of musical elements including tempo, rhythm stability, beat strength, and overall regularity. A value of 0.0 is least danceable and 1.0 is most danceable.')
    msg.append('')
    msg.append('Energy is a measure from 0.0 to 1.0 and represents a perceptual measure of intensity and activity. Typically, energetic tracks feel fast, loud, and noisy. For example, death metal has high energy, while a Bach prelude scores low on the scale. Perceptual features contributing to this attribute include dynamic range, perceived loudness, timbre, onset rate, and general entropy.')
    msg.append('')
    msg.append('Valence is a measure from 0.0 to 1.0 describing the musical positiveness conveyed by a track. Tracks with high valence sound more positive (e.g. happy, cheerful, euphoric), while tracks with low valence sound more negative (e.g. sad, depressed, angry).')
    msg.append('')
    msg.append('Example: "!sort spotify:playlist:5mQ41bDZKcDe7rpFMuuia3 valence  {{Sorts the playlist by valence, from high to low}}"')
    msg.append('Example: "!sort spotify:playlist:5mQ41bDZKcDe7rpFMuuia3 valence:-1  {{Sorts the playlist by valence from low to high}}"')
    msg.append('Example: "!sort spotify:playlist:5mQ41bDZKcDe7rpFMuuia3 valence:.5 danceability:1 {{Sorts the playlist by valence at half value and danceability at full}}"')
    msg.append('')
    msg.append('Any combination of metrics works. Probably.')
    msg.append('\n```')
    await ctx.channel.send('\n'.join(msg))

@bot.command(pass_context=True)
async def q(ctx, id):
    sp.add_to_queue(id)
    await ctx.channel.send('Added to Nick\'s Queue!')

@bot.command(pass_context=True)
async def qp(ctx, id):
    playlist = await resolve_playlist(ctx, id, False)
    tracks = get_all_tracks_from_playlist(playlist, 'id')
    random.shuffle(tracks)
    for track in tracks[:50]:
        sp.add_to_queue(track)
    await ctx.channel.send('Added many to Nick\'s Queue!')

################## Not-Bot Commands
async def resolve_playlist(ctx, from_playlist, to=True):
    from_playlist = await getPlaylistID(ctx, from_playlist)
    if to:
        to_playlist = create_playlist()
        return [from_playlist, to_playlist]
    return from_playlist

async def getPlaylistID(ctx, id):
    try:
        int(id)
        with open(playlistFile, 'r') as f:
            playlist = f.readline()
            for _ in range(int(id)):
                playlist = f.readline()
            return playlist.split(' ')[1].replace('\n', '')
    except:
        with open(playlistFile, 'r') as f:
            for _ in f:
                if id == _.split(' ')[0]:
                    return _.split(' ')[1].replace('\n', '')

    if 'open' in id:
        id = id.split('?')[0].split('/')[-1]
    elif 'playlist' in id:
        id = id.split(':')[2]
    return id
    #await ctx.channel.send(f'Could not find playlist {id}')

def get_all_tracks_from_playlist(playlist, attribute=None):
    trks = []
    playlist = sp.user_playlist(username, playlist)
    tracks = playlist['tracks']

    while True:
        for item in tracks['items']:
            if attribute is None:
                trks.append(item['track'])
            else:
                trks.append(item['track'][attribute])
        if not tracks['next']: break
        tracks = sp.next(tracks)
    return trks

def get_artists_top_songs(uri, num):
    tracks = []
    response = sp.artist_top_tracks(uri)
    for track in response['tracks'][:num]:
        tracks.append(track['id'])
    return tracks

def get_primary_artists(results):
    artists = []
    for item in results['items']:
        art_name = item['track']['artists'][0]['name'].lower()
        art_id = item['track']['artists'][0]['uri']
        art = [art_name, art_id]
        if art not in artists:
            artists.append(art)
    return artists

def get_all_artists(playlist):
    artists = []
    playlist = sp.playlist(playlist)
    tracks = playlist['tracks']
    while True:
        for art in get_primary_artists(tracks):
            if art not in artists:
                artists.append(art)
        if not tracks['next']: break
        tracks = sp.next(tracks)
    return artists

def get_features_from_ids(song_ids):
    out = []
    fts = []
    ids = []
    for id in song_ids:
        if id in data.song_features:
            out.append(data.song_features[id])
        else:
            ids.append(id)

    for i in range(int(len(ids) / 100)):
        fts.extend(sp.audio_features(ids[i*100:(i+1)*100]))
    if len(ids)%100:
        fts.extend(sp.audio_features(ids[-(len(ids)%100):]))
    for ft in fts:
        data.song_features[ft['id']] = ft
        out.append(ft)
    if fts:
        with open('data.py', 'w+') as f:
            f.write(f'song_features = {data.song_features}')
    return out

def add_features_to_db(fts):
    for ft in fts:
        data.song_features[ft['id']] = ft

def get_feature_single_song(id):
    return sp.audio_features(id)

def get_track_single_song(id):
    return sp.track(id)

def get_playlist_link(playlist):
    playlist = sp.user_playlist(username, playlist)
    return playlist['external_urls']['spotify']
    
################################## Utilities ###################################
def add_songs(to_playlist, songs):
    try:
        sp.user_playlist_add_tracks(username, to_playlist, songs)
    except:
        print(f'{songs} failed')

def add_tracks_to_playlist(to_playlist, tracks):
    for i in range(int(len(tracks) / 100)):
        add_songs(to_playlist, tracks[i*100:(i+1)*100])
    if len(tracks)%100:
        add_songs(to_playlist, tracks[-(len(tracks)%100):])

def create_playlist():
    try:
        name = ' '.join(wordRandomizer.get_random_words(limit=4)).title()
    except:
        name = 'Boring Name because it failed'
    p = sp.user_playlist_create(username, name)
    return p['uri'].split(':')[2]

################################# Entry Points #################################
def shuffle_playlist(from_playlist, to_playlist):
    tracks = get_all_tracks_from_playlist(from_playlist, 'id')
    random.shuffle(tracks)
    add_tracks_to_playlist(to_playlist, tracks)

def create_top_tracks_playlist(from_playlist, to_playlist, num=5, shuffle=True):
    artists = get_all_artists(from_playlist)
    top_songs = []
    for art in sorted(artists):
        res = get_artists_top_songs(art[1], num)
        top_songs.extend(res)
    top_songs = list(set(top_songs))  # Get rid of duplicates
    if shuffle:
        random.shuffle(top_songs)
    add_tracks_to_playlist(to_playlist, top_songs)

def sort_by_metrics(from_playlist, to_playlist, metrics, rtn=False):
    trks = get_all_tracks_from_playlist(from_playlist, 'id')
    fts = get_features_from_ids(trks)
    out = []
    for ft in fts:
        calc = 0
        for m in metrics:
            if ':' not in m:
                m += ':1'
            _ = m.split(':')
            if '-' in _[0]:
                calc += (1 - float(ft[_[0]])) * float(_[1].replace('-',''))
            else:
                calc += float(ft[_[0]]) * float(_[1])
        out.append([calc, ft['id']])

    out = sorted(out)[::-1]
    if rtn:
        return out
    add_tracks_to_playlist(to_playlist, [o[1] for o in out][:100])

def remove_live_tracks(from_playlist, to_playlist):
    trks = sort_by_metrics(from_playlist, to_playlist, ['liveness:1'], True)
    for i, trk in enumerate(trks):
        print(trk)

bot.run("Njk3NTgwODg4NTM1MzM0OTUy.Xo5XJg.giZxghxqmA44e-94pbOxWtl7eeE")
