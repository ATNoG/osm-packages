import io
import ipaddress
from packaging import version
import subprocess
import os
import socket
import shlex
import traceback
import sys
import yaml
from shutil import which
from subprocess import (
    check_call,
    Popen,
    CalledProcessError,
    PIPE,
)
import os
import subprocess
import logging

logger = logging.getLogger(__name__)

class SSHProxy:
    def __init__(self, hostname: str, username: str, password: str = ""):
        self.hostname = hostname
        self.username = username
        self.password = password

    def run(self, cmd):
        """Run a command remotely via SSH.
        Note: The previous behavior was to run the command locally if SSH wasn't
        configured, but that can lead to cases where execution succeeds when you'd
        expect it not to.
        """
        if isinstance(cmd, str):
            cmd = shlex.split(cmd)

        host = self.hostname
        user = self.username
        passwd = self.password

        # Make sure we have everything we need to connect
        if host and user:
            return self.ssh(cmd)

        raise Exception("Invalid SSH credentials.")

    def scp(self, source_file, destination_file):
        """Execute an scp command. Requires a fully qualified source and
        destination.
        :param str source_file: Path to the source file
        :param str destination_file: Path to the destination file
        :raises: :class:`CalledProcessError` if the command fails
        """
        if which("sshpass") is None:
            SSHProxy.install()
        cmd = [
            "sshpass",
            "-p",
            self.password,
            "scp",
        ]
        destination = "{}@{}:{}".format(self.username, self.hostname, destination_file)
        cmd.extend([source_file, destination])
        subprocess.run(cmd, check=True)

    def ssh(self, command):
        """Run a command remotely via SSH.
        :param list(str) command: The command to execute
        :return: tuple: The stdout and stderr of the command execution
        :raises: :class:`CalledProcessError` if the command fails
        """

        if which("sshpass") is None:
            SSHProxy.install()
        destination = "{}@{}".format(self.username, self.hostname)
        cmd = [
            "sshpass",
            "-p",
            self.password,
            "ssh",
            destination,
        ]
        cmd.extend(command)
        print(cmd)
        output = subprocess.run(
            cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        return (
            output.stdout.decode("utf-8").strip(),
            output.stderr.decode("utf-8").strip(),
        )
