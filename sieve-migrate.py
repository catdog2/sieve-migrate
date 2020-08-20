#! /usr/bin/env python3
import sys

import click

import managesieve


@click.group()
def cli():
    pass


@cli.command()
@click.option("--from-host", type=str, required=True)
@click.option("--from-port", type=int, required=False, default=managesieve.SIEVE_PORT)
@click.option("--from-username", type=str, required=True)
@click.option("--from-password", type=str, envvar="MIGRATE_FROM_PASSWORD", prompt=True, hide_input=True)
@click.option("--from-tls", type=bool, default=True)
@click.option("--to-host", type=str, required=True)
@click.option("--to-port", type=int, required=False, default=managesieve.SIEVE_PORT)
@click.option("--to-username", type=str, required=True)
@click.option("--to-password", type=str, envvar="MIGRATE_TO_PASSWORD", prompt=True, hide_input=True)
@click.option("--to-tls", type=bool, default=True)
def migrate(from_host, from_port, from_username, from_password, from_tls, to_host, to_port, to_username, to_password,
            to_tls):
    from_sieve = managesieve.MANAGESIEVE(from_host, port=from_port, use_tls=from_tls)
    if from_sieve.login("", from_username, from_password) != "OK":
        raise Exception(f'Login to {from_host} failed for {from_username}')

    to_sieve = managesieve.MANAGESIEVE(to_host, port=to_port, use_tls=to_tls)
    if to_sieve.login("", to_username, to_password) != "OK":
        raise Exception(f'Login to {to_host} failed for {to_username}')

    from_scripts = from_sieve.listscripts()
    if from_scripts[0] != "OK":
        raise Exception(f"Err {from_scripts}")

    script_contents = {}

    for sn, active in from_scripts[1]:
        cur_script = from_sieve.getscript(sn)
        if cur_script[0] != "OK":
            raise Exception(f"Unable to get script {sn}")

        script_contents[sn] = {"active": active, "content": cur_script[1]}

    for sn, content in script_contents.items():
        if to_sieve.putscript(sn, content["content"]) != "OK":
            raise Exception(f"Unable to put script {sn} to {to_host}")

    for sn, content in script_contents.items():
        if content["active"]:
            if to_sieve.setactive(sn) != 'OK':
                raise Exception(f"Unable to set script {sn} active on {to_host}")

    print(f"Migrated list({script_contents.keys()}) from {from_host}({from_username}) to {to_host}({to_username})",
          file=sys.stderr)


if __name__ == "__main__":
    cli()
