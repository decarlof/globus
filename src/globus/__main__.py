#!/local/user2bmb/Software/anaconda/bin/python
# -*- coding: utf-8 -*-
import os
import re
import sys
import argparse
import pathlib
import logging
import time
from datetime import datetime, timedelta

from globus import scheduling

from globus import config
from globus import dm
from globus import log
from globus import pv
from globus import directories
from globus import message
from globus import globus

__author__ = "Francesco De Carlo"
__copyright__ = "Copyright (c) 2019, UChicago Argonne, LLC."
__version__ = "0.0.1"
__docformat__ = 'restructuredtext en'


def set_config(args):
    print(str(args.config))
    if not os.path.exists(str(args.config)):
        config.write(str(args.config))
    else:
        raise RuntimeError("{0} already exists".format(args.config))

def show(args):
    # show args from default (config.py) if not changed
    config.show_config(args)
    if (args.globus_server_name == 'petrel'):
        ac, tc = globus.create_clients(args)
        globus.show_endpoints(args, ac, tc)

def email(args):

    '''Sends an email to all users on the current experiment 
    with information on how to get their data from Sojourner.
    '''
    log.info('Sending e-mail to users on the DM experiment')
    # prepare the message
    args.msg = message.message(args)
    log.info('   Message to users start:')  
    log.info('   *** %s' % args.msg)  
    log.info('   Message to users end')  
    # send the message
    message.send_email(args)

def init(args):
    '''Initiate data management
    '''
    if (args.globus_server_name == 'sojourner'):
        new_exp = dm.create_experiment(args)
        if args.manual:
            # Build user list from --manual-badges
            user_list = set()
            # Always add beamline contacts
            user_list.add('d' + str(args.primary_beamline_contact_badge))
            user_list.add('d' + str(args.secondary_beamline_contact_badge))
            # Add manually specified badges
            if args.manual_badges:
                for badge in args.manual_badges.split(','):
                    badge = badge.strip()
                    if badge:
                        user_list.add('d' + badge)
            log.info('Adding manual users to the DM experiment.')
        else:
            user_list = dm.make_dm_username_list(args)
            log.info('Adding users from the current proposal to the DM experiment.')
        dm.add_users(new_exp, user_list)
    elif (args.globus_server_name == 'petrel'):
        globus.refresh_globus_token(args)
        ac, tc = globus.create_clients(args)
        log.info('Creating user directory on server %s:%s' % (args.globus_server_uuid, args.globus_server_top_dir))
        globus.create_globus_dir(args, ac, tc)

def start_daq(args):
    '''Start a Data Management DAQ on the analysis machine directory.
    '''
    dm.start_daq(args)

    
def stop_daq(args):
    '''Stop the Data Management DAQ set up for this experiment.
    '''
    dm.stop_daq(args)


def add_user(args):
    dm.add_user(args)


def remove_user(args):
    dm.remove_user(args)


def list_users(args):
    dm.list_users(args)


def main():
    home = os.path.expanduser("~")
    logs_home = home + '/logs/'

    # make sure logs directory exists
    if not os.path.exists(logs_home):
        os.makedirs(logs_home)

    lfname = logs_home + 'globus_' + datetime.strftime(datetime.now(), "%Y-%m-%d_%H:%M:%S") + '.log'
    log.setup_custom_logger(lfname)


    parser = argparse.ArgumentParser()
    parser.add_argument('--config', **config.SECTIONS['general']['config'])
    globus_params = config.GLOBUS_PARAMS

    cmd_parsers = [
        ('config',      set_config,     globus_params,  "Create configuration file"),
        ('show',        show,           globus_params,  "Show status"),
        ('init',        init,           globus_params,  "Initialize data mamagement"),
        ('list_users',  list_users,     globus_params,  "List the users on the current DM experiment"),
        ('add_user',    add_user,       globus_params,  "Add a user to the current DM experiment by badge number"),
        ('remove_user', remove_user,    globus_params,  "Remove a user from the current DM experiment by badge number"),
        ('email',       email,          globus_params,  "Send email with link to all users on the proposal"),
        ('start_daq',   start_daq,      globus_params,  "Start DM DAQ"),
        ('stop_daq',    stop_daq,       globus_params,  "Stop DM DAQ"),
    ]

    subparsers = parser.add_subparsers(title="Commands", metavar='')

    for cmd, func, sections, text in cmd_parsers:
        cmd_params = config.Params(sections=sections)
        cmd_parser = subparsers.add_parser(cmd, help=text, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        cmd_parser = cmd_params.add_arguments(cmd_parser)
        cmd_parser.set_defaults(_func=func)

    args = config.parse_known_args(parser, subparser=True)

    # If no subcommand was provided, print help and exit
    if not hasattr(args, '_func'):
        parser.print_help()
        sys.exit(0)
   
    #Do config here, because otherwise we won't have PVs to update our info anyway
    if args._func == set_config:
        try:
            args._func(args)
            return
        except RuntimeError as e:
            log.error(str(e))
            sys.exit(1)
        return

    if (args.globus_server_name == 'sojourner'):
        args.globus_server_uuid = '054a0877-97ca-4d80-947f-47ca522b173e'
        # args.globus_server_top_dir = '/gdata/dm/7BM'
    elif (args.globus_server_name == 'petrel'):
        args.globus_server_uuid = 'e133a81a-6d04-11e5-ba46-22000b92c6ec'
        args.globus_app_uuid = 'a9badd00-39c3-4473-b180-8bccc113ba1d' # for usr32idc/petrel
        args.globus_server_top_dir = '/2-BM/'
    else:
        log.error("%s is not a supported globus server" % args.globus_server_name)
        exit()

    #Init here, otherwise we don't have parameters to do the following updates
    if args.manual:
        now = datetime.now()
        args.year_month    = now.strftime('%Y-%m')
        args.pi_last_name  = args.manual_name
        args.gup_number    = '0'
        args.gup_title     = args.manual_title
        args.manual_start  = now.strftime('%d-%b-%y')
        args.manual_end    = (now + timedelta(days=14)).strftime('%d-%b-%y')
        log.info(f"Manual experiment: {args.year_month}-{args.pi_last_name}, "
                 f"title: {args.gup_title}")
    elif args.set != 0:
        # Past experiment: retrieve info from the scheduling system
        beamtimes = scheduling.list_beamtimes(args)
        if not beamtimes:
            log.error("No beamtimes found for the given --set offset")
            sys.exit(1)
        elif len(beamtimes) == 1:
            bt = beamtimes[0]
            log.info(f"Found 1 beamtime in past run: GUP {bt['gup_number']} "
                     f"(PI: {bt['pi_last_name']}, {bt['gup_title'][:60]})")
        else:
            log.info(f"Found {len(beamtimes)} beamtimes in past run {beamtimes[0]['run_name']}:")
            for i, bt in enumerate(beamtimes):
                print(f"  [{i}] GUP {bt['gup_number']} - PI: {bt['pi_last_name']} - "
                      f"{bt['gup_title'][:70]}")
                print(f"       {bt['start_time']} to {bt['end_time']}")
            while True:
                try:
                    choice = int(input(f"\nSelect beamtime [0-{len(beamtimes)-1}]: "))
                    if 0 <= choice < len(beamtimes):
                        bt = beamtimes[choice]
                        break
                    print(f"Please enter a number between 0 and {len(beamtimes)-1}")
                except (ValueError, EOFError):
                    print("Invalid input. Please enter a number.")

        args.year_month   = bt['year_month']
        args.pi_last_name = bt['pi_last_name']
        args.gup_number   = bt['gup_number']
        args.gup_title    = bt['gup_title']
        log.info(f"Using past experiment: {args.year_month}, "
                 f"PI: {args.pi_last_name}, GUP: {args.gup_number}")
    else:
        # Current experiment: read from EPICS PVs
        args.year_month, args.pi_last_name, args.gup_number, args.gup_title = pv.update_experiment_info(args)

    required_args = {
        'year_month': args.year_month,
        'pi_last_name': args.pi_last_name,
        'gup_number': args.gup_number,
        'gup_title': args.gup_title,
    }

    for name, value in required_args.items():
        if value is None:
            log.error(f"Error: Required argument '{name}' is missing. "
                      f"Check that tomoscan with prefix {args.tomoscan_prefix} is up and running")
            sys.exit(1)

    # Save CLI parameters to config file so they become the new defaults
    # Reset 'set' to 0 — it's a one-time offset, not a persistent setting
    args.set = 0
    sections = config.GLOBUS_PARAMS
    config.write(args.config, args=args, sections=sections)

    if args._func == init:
        try:
            args._func(args)
            return
        except RuntimeError as e:
            log.error(str(e))
            sys.exit(1)
        return

    try:
        args._func(args)
    except RuntimeError as e:
        log.error(str(e))
        sys.exit(1)

if __name__ == '__main__':
    main()