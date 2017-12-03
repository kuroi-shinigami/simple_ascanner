#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
Simple IPv4 mac finder. Requires python 3.6 (Hello, syntax shugar!)

Special for vispiano
"""

import re
import sys
import locale
import asyncio


def timer(func):
    import time

    def wrapper(*args, **kwargs):
        start_time = time.time()
        res = func(*args, **kwargs)
        print("Timer ({}): {}".format(func.__name__, time.time() - start_time))
        return res

    return wrapper


class AsyncExeWrapper:
    """Asynchronous wrapper above executables. Default is echo"""
    def __init__(self, executable='echo'):
        self.executable = executable
        asyncio.wait(asyncio.ensure_future(self.checks()))

    async def checks(self):
        """ Method to ensure that provided executable even callable. May be redefined in special cases """
        # await self.execute(self.executable)

    async def execute(self, some_command='', raise_on_error=True):
        """ Main method for which the whole thing is implemented"""

        if type(some_command) is list:                                                      # ToDo: Shit & sticks, redo
            some_command = " ".join(some_command)
            while "  " in some_command:
                some_command = some_command.replace("  ", " ")
        some_command = [self.executable] + some_command.split()
        # print('executing `{}`'.format(some_command))
        buffer = bytearray()
        _name, _encoding = locale.getdefaultlocale()                # Terminal encodings may differ and break everything

        create = asyncio.create_subprocess_exec(*some_command, stdout=asyncio.subprocess.PIPE,)
        proc = await create
        while True:
            line = await proc.stdout.readline()
            if not line:
                break
            buffer.extend(line)

        await proc.communicate()
        return_code = proc.returncode

        stdoutdata = bytes(buffer).decode(_encoding)
        if return_code and raise_on_error:
            raise AsyncExeWrapperError(f"{stdoutdata}")

        return stdoutdata.strip(), return_code


class AsyncExeWrapperError(BaseException):
                                    # RuntimeError -> BaseException beacuse of
                                    # TypeError: catching classes that do not inherit from BaseException is not allowed
    """Common Exception for AsyncExeWrapper"""
    # ToDo: Investigate
    # how children could catch this exception and throw one's own without constantly rewriting the code


def ip2int(some_str):
    """returns int instead of dotted IPv4"""
    return sum(int(octet) << ((3 - i) << 3) for i, octet in enumerate(some_str.split('.')))


def int2ip(some_int):
    """returns dotted IPv4 from int"""
    return '.'.join(str(some_int >> off & 0xff) for off in (24, 16, 8, 0))


def iprange(s, e=None):
    """
    Generates ips in range from s to e or vice versa.
    inb4: there is no use 'cause fpingg can use multiple args of text file as input
    :param s:   start ip
    :param e:   end ip. If no end ip provided will consider that single host should be generated
    :return:    list of strings in range from s to e
    """
    # https://stackoverflow.com/questions/20525330

    if e is None:  # No real need to get out of here right now
        e = s

    if is_ip(s) and is_ip(e):
        _s = ip2int(s)
        _e = ip2int(e)
        for addr in range(min(_s, _e), max(_s, _e) + 1):
            yield int2ip(addr)


# noinspection PyBroadException
def is_ip(some_string):     # ToDo: implement different representations if ip addresses such as submasks, hex, dns names
    """returns True if arg looks like a valid ip address"""
    try:
        ip = [int(x) for x in some_string.split('.')]
        if len(ip) == 4:
            for x in ip:
                if not (0 <= x <= 255):
                    return False
            return True
    except Exception:
        pass
    return False


# noinspection PyBroadException,PyTypeChecker
async def ping_all(start, end=None):
    """
    Just pings hosts by ping/fping tool in the host system
    :param start:   start ip
    :param end:     end ip. If no end ip provided will scan single host
    :return:        None
    """

    ip_generator = iprange(start, end)
    ping = AsyncExeWrapper('fping')
    try:
        await ping.execute('-v')  # or -h, without args fping waits user's imput
        cmd = [x for x in ip_generator] + ['-c', '1']  # 1 package
        # We do not store anything in stdout 'cause we don't need anything from it: we will see everything in arp.
        # The main thing we need is just to await when all hosts will be pinged
        await ping.execute(cmd, raise_on_error=False)
    except Exception:
        print("Couldn't find fping. Using ping instead")
        ping = AsyncExeWrapper('ping')
        # For now, just bulk suppression for errors: ping returns error code if host is unavailable
        # ToDo:
        tasks = [asyncio.ensure_future(ping.execute([ip, '-c', '1'], raise_on_error=False)) for ip in ip_generator]
        print('Tasks are ready... Awaiting...')
        # If you are interested if tasks are really executed, feel free to uncomment print in execute() method
        await asyncio.wait(tasks)
        print('Tasks are ready... Finished!')


async def scan_all(start, end=None):                    # ToDo: implement list of desired ips as input or use smth like
                                                        # [str(x) for x in ipaddress.ip_network("192.0.2.0/28").hosts()]
                                                        # from here: https://stackoverflow.com/questions/19157307
    """
    Scanner itself. Checks arp, fping/ping, executes them all.
    :param start:   start ip
    :param end:     end ip
    :return:        list of MAC adresses of hosts
    """
    if end is None:
        end = start

    arp = AsyncExeWrapper('arp')
    # noinspection PyBroadException
    try:
        await arp.execute()
    except Exception:
        whoami = AsyncExeWrapper('whoami')
        username, excit_code = await whoami.execute()
        is_root = 'No, you are not' if username != 'root' else 'Hm... yes, you are. Check net-tools.'
        print(f"Couldn't call arp. Are your root? (Hint: {is_root})\nExiting for now. Bye ;)")
        return

    await ping_all(start, end)

    res = []
    stdout, exit_code = await arp.execute('-a')
    regexp = re.compile(r'.*\((?P<ip>(\d+\.){3}\d+)\)\s+at\s+(?P<mac>[0-9:a-f]+).*')
    for x in [_s.strip() for _s in stdout.split('\n') if _s.strip()]:
        _m = re.match(regexp, x)
        if _m:
            res.append(_m.groupdict())
        else:                                               # Shouldn't be printed instead of <incomplete> for some macs
            # print("Mismatch: {}, {}".format(x, _m))
            pass
    for x in res:
        print(x)


@timer
def main(start, end=None, func=scan_all):
    if sys.platform == 'win32':
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
    else:
        if asyncio.get_event_loop().is_closed():
            asyncio.set_event_loop(asyncio.new_event_loop())
        loop = asyncio.get_event_loop()

    loop.run_until_complete(func(start, end))
    loop.close()


if __name__ == '__main__':
    main('192.168.1.1', '192.168.1.254', func=ping_all)
    # main('192.168.1.1', '192.168.1.254')
