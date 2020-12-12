import os
import psutil
from datetime import datetime


async def get_status(pid, bot):
    process = psutil.Process(pid)
    mem = int(round((process.memory_info()[0] / 1000000)))
    cpu = psutil.cpu_percent(interval=None)
    cores_used = len(process.cpu_affinity())
    cores_total = psutil.cpu_count()
    ping = round(bot.latency * 1000, 1)
    uptime = str(datetime.now() - bot.starttime).split(".")[0]
    return mem, cpu, cores_used, cores_total, ping, uptime
