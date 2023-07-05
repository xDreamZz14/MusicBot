from nextcord.ext import commands
import nextcord
from config import TOKEN
from time import sleep
import nextwave

intents = nextcord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix = "!", intents=intents)

@bot.event
async def on_ready():
    """
    Llama a la funcion para que el bot pueda conectarse al servidor
    El print muestra en la consola si se ha conectado sin problemas
    """
    print(f'{bot.user} has connected to Discord!')
    bot.loop.create_task(node_connect())


@bot.event
async def on_nextwave_node_ready(node: nextwave.Node):
    print(f"Node {node.identifier} is ready!")

async def node_connect():
    """
    Conecta el bot a un host (en este caso gratuito) para poder buscar las canciones
    en las fuentes indicadas en el codigo
    """
    await bot.wait_until_ready()
    await nextwave.NodePool.create_node(bot = bot,
                                        host = "eu-lavalink.lexnet.cc",
                                        port = 443,
                                        password = "lexn3tl@val!nk",
                                        https = True)

@bot.event
async def on_nextwave_track_end(player: nextwave.Player, track: nextwave.Track, reason):
    """
    Cuando una cancion termina, permite que reproduzca la siguiente cancion en la lista.
    En caso de no tener ninguna cancion que reproducir, se desconecta automaticamente despues de
    10 segundos.

    Muestra la cancion que esta en reproduccion actualmente.
    """
    ctx = player.ctx
    vc: player = ctx.voice_client

    if vc.loop:
        return await vc.play(track)

    if vc.queue.is_empty: # Se desconecta cuando la queue esta vacia
        sleep(10)
        return await vc.disconnect()

    nextSong = vc.queue.get()
    await vc.play(nextSong)
    await ctx.send(f"Ahora estas escuchando: {nextSong.title}")

@bot.command()
async def play(ctx: commands.Context, *,search: nextwave.YouTubeTrack): # ctx = Context
    """
    !play {Cancion a elegir}: Empieza a reproducir la cancion que hayamos escrito y en caso
    de tener alguna ya en reproduccion, añade a la cola.

    En caso de no estar en ningun canal de voz, te devuelve un mensaje avisandote
    """
    if not ctx.voice_client:
        vc: nextwave.Player = await ctx.author.voice.channel.connect(cls = nextwave.Player) # cls = Pertenece a la clase
    elif not ctx.author.voice:
        return await ctx.send("Primero entra a un canal de voz")
    else:
        vc: nextwave.Player = ctx.voice_client

    if vc.queue.is_empty and not vc.is_playing():
        await vc.play(search)
        await ctx.send(f"Ahora estas escuchando: {search.title}")
    else:
        await vc.queue.put_wait(search)
        await ctx.send(f"Has añadido {search.title} a la cola")
    vc.ctx = ctx
    setattr(vc, "loop", False)

@bot.command()
async def pause(ctx: commands.Context):
    """
    !pause: Permite pausar la cancion y devuelve al usuario un texto avisandole.

    En caso de no tener ninguna cancion en reproduccion, avisa al usuario.
    """
    if not ctx.voice_client:
        return await ctx.send("No hay ninguna cancion que pausar")
    elif not ctx.author.voice:
        return await ctx.send("Primero entra a un canal de voz")
    else:
        vc: nextwave.Player = ctx.voice_client

    await vc.pause()
    await ctx.send("Musica pausada")

@bot.command()
async def resume(ctx: commands.Context):
    """
    !resume: Permite volver a reproducir una cancion despues de haberlo pausado.

    Si no hay ninguna cancion que volver a reproducir, avisa al usuario
    """
    if not ctx.voice_client:
        return await ctx.send("No hay ninguna cancion que resumir")
    elif not ctx.author.voice:
        return await ctx.send("Primero entra a un canal de voz")
    else:
        vc: nextwave.Player = ctx.voice_client

    await vc.resume()
    await ctx.send("Musica resumida")

@bot.command()
async def stop(ctx: commands.Context):
    """
    !stop: Para la cancion y salta a la siguiente en la cola.

    En caso de no tener mas canciones, detiene el bot.
    """
    if not ctx.voice_client:
        return await ctx.send("No hay ninguna cancion que parar")
    elif not ctx.author.voice:
        return await ctx.send("Primero entra a un canal de voz")
    else:
        vc: nextwave.Player = ctx.voice_client

    await vc.stop()
    await ctx.send("Cancion saltada")

@bot.command()
async def disconnect(ctx: commands.Context):
    """
    !disconnect: Permite desconectar al bot manualmente en caso de que ya no se quiera seguir
    utilizando.

    Si no esta en ningun canal avisa al usuario de que no se puede usar.
    """
    if not ctx.voice_client:
        return await ctx.send("Aun no estoy en ningun canal")
    elif not ctx.author.voice:
        return await ctx.send("Primero entra a un canal de voz")
    else:
        vc: nextwave.Player = ctx.voice_client

    await vc.disconnect()
    await ctx.send("Vuelve a usarme pronto")

@bot.command()
async def loop(ctx: commands.Context):
    """
    !loop: Permite activar y desactivar el bucle de canciones. En caso de desactivarlo, solo
    reproduce la primera cancion introducida.
    """
    if not ctx.voice_client:
        return await ctx.send("Aun no estoy en ningun canal")
    elif not ctx.author.voice:
        return await ctx.send("Primero entra a un canal de voz")
    else:
        vc: nextwave.Player = ctx.voice_client

    try:
        vc.loop ^= True
    except Exception:
        setattr(vc, "loop", False)

    if vc.loop:
        return await ctx.send("El loop ahora esta habilitado")
    else:
        return await ctx.send("El loop ahora esta deshabilitado")

@bot.command()
async def queue(ctx: commands.Context):
    """
    !queue: Muestra las canciones que hay en la cola actualmente e indica el orden de reproduccion.

    En caso de estar vacia, se lo indica al usuario.
    """
    if not ctx.voice_client:
        return await ctx.send("Todavia no estoy reproduciendo ninguna cancion")
    elif not ctx.author.voice:
        return await ctx.send("Primero entra a un canal de voz")
    else:
        vc: nextwave.Player = ctx.voice_client

    if vc.queue.is_empty:
        return await ctx.send("La cola esta vacia")

    em = nextcord.Embed(title="Queue")
    queue = vc.queue.copy()
    songCount = 0
    for song in queue:
        songCount += 1
        em.add_field(name=f"Num cancion {songCount}", value=f"{song.title}")

    return await ctx.send(embed=em)

bot.run(TOKEN)

"""
elif not ctx.author.voice == ctx.me.voice:
    return await ctx.send("Tenemos que estar en el mismo canal de voz")
"""