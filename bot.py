import struct
import socket
import json
import discord
from discord.ext import commands
# config
import config

intents = discord.Intents.all()
activity = discord.Activity(type=discord.ActivityType.watching, name=f"{config.prefix}stats")
bot = commands.Bot(command_prefix=config.prefix, intents=intents,activity=activity, status=discord.Status.idle)

# For the rest of requests see wiki.vg/Protocol
def ping(ip, port):
    def read_var_int():
        i = 0
        j = 0
        while True:
            k = sock.recv(1)
            if not k:
                return 0
            k = k[0]
            i |= (k & 0x7f) << (j * 7)
            j += 1
            if j > 5:
                raise ValueError('var_int too big')
            if not (k & 0x80):
                return i
    sock = socket.socket()
    sock.connect((ip, port))
    try:
        host = ip.encode('utf-8')
        data = b''  # wiki.vg/Server_List_Ping
        data += b'\x00'  # packet ID
        data += b'\x04'  # protocol variant
        data += struct.pack('>b', len(host)) + host
        data += struct.pack('>H', port)
        data += b'\x01'  # next state
        data = struct.pack('>b', len(data)) + data
        sock.sendall(data + b'\x01\x00')  # handshake + status ping
        length = read_var_int()  # full packet length
        if length < 10:
            if length < 0:
                raise ValueError('negative length read')
            else:
                raise ValueError('invalid response %s' % sock.read(length))
        sock.recv(1)  # packet type, 0 for pings
        length = read_var_int()  # string length
        data = b''
        while len(data) != length:
            chunk = sock.recv(length - len(data))
            if not chunk:
                raise ValueError('connection abborted')
            data += chunk
        return json.loads(data)
    finally:
        sock.close()
        
with open(f'lang/{config.language}.json', 'r', encoding="utf-8") as f:
    translations = json.load(f)
#
def players(mc):
    if 'sample' in mc['players']: 
        return ", ".join([item["name"] for item in mc['players']["sample"][:len(mc['players']['sample'])]])
    else:
        return translations['embed_empty_players']
        
@bot.command()
async def stats(ctx):
    try:
        mc = ping(config.ip, int(config.port))
        embed = discord.Embed(color = 0x6b6b6b, title = translations['embed_description'])
        embed.set_thumbnail(url="https://i.gifer.com/origin/06/06ace2e9b4e856f6955f230594f2998e.gif")
        embed.add_field(name=translations['embed_version'],value=f"{mc['version']['name']}", inline = True)
        embed.add_field(name=translations['embed_online'],value=f"{mc['players']['online']}/{mc['players']['max']}", inline = True)
        embed.add_field(name=translations['embed_players'],value=f"{players(mc)}", inline = False)
        embed.set_footer(text=f"{translations['embed_state']} 🔵")
        await ctx.send(embed = embed) 
    except socket.gaierror:
        embed = discord.Embed(color = 0xff0051, title = translations['embed_description'])
        embed.set_thumbnail(url="https://i.gifer.com/origin/06/06ace2e9b4e856f6955f230594f2998e.gif")
        embed.add_field(name=translations['embed_server_is_down'],value="", inline = True)
        embed.set_footer(text=f"{translations['embed_state']} 🔴")
        await ctx.send(embed = embed) 
    except ConnectionRefusedError:
        embed = discord.Embed(color = 0xff0051, title = translations['embed_description'])
        embed.set_thumbnail(url="https://i.gifer.com/origin/06/06ace2e9b4e856f6955f230594f2998e.gif")
        embed.add_field(name=translations['embed_server_is_down'],value="", inline = True)
        embed.set_footer(text=f"{translations['embed_state']} 🔴")
        await ctx.send(embed = embed) 

bot.run(config.token)
