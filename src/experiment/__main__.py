#!/local/user2bmb/Software/anaconda/bin/python
# -*- coding: utf-8 -*-
import os
import sys
import argparse
from datetime import datetime, timedelta

from experiment import scheduling

from experiment import config
from experiment import directories
from experiment import dm
from experiment import log
from experiment import message

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

def email(args):

    '''Sends an email to all users on the current experiment
    with information on how to get their data from Sojourner.
    '''
    log.info('Sending e-mail to users on the DM experiment')
    # prepare the message
    args.msg = message.message(args)
    log.info('   Message to users start:')
    log.info('   *** %s' % args.msg.get_content())
    log.info('   Message to users end')
    # send the message
    message.send_email(args)

def create(args):
    '''Create a DM experiment on Sojourner and add users to it.
    '''
    new_exp = dm.create_experiment(args)
    if new_exp is None:
        return
    if args.manual:
        # Build user list from --badges
        user_list = set()
        # Always add beamline contacts
        user_list.add('d' + str(args.primary_beamline_contact_badge))
        user_list.add('d' + str(args.secondary_beamline_contact_badge))
        # Add manually specified badges
        if args.badges:
            for badge in args.badges.split(','):
                badge = badge.strip()
                if badge:
                    user_list.add('d' + badge)
        log.info('Adding manual users to the DM experiment.')
    else:
        user_list = dm.make_dm_username_list(args)
        if user_list is None:
            exp_name = directories.make_directory_name(args)
            log.warning(f"   GUP {args.gup_number} not found in the scheduling system.")
            log.warning(f"   However, DM experiment '{exp_name}' already exists with these users:")
            dm.log_exp_users(exp_name)
            log.warning(f"   Do you want to use its existing users?")
            if message.yes_or_no('   *** Yes or No'):
                user_list = dm.make_username_list(args)
            else:
                log.info("   To add a user run: experiment add-user --badge <badge#>")
                return
        log.info('Adding users from the current proposal to the DM experiment.')
    dm.add_users(new_exp, user_list)

def start_daq(args):
    '''Start a Data Management DAQ on the analysis machine directory.
    '''
    dm.start_daq(args)


def stop_daq(args):
    '''Stop the Data Management DAQ set up for this experiment.
    '''
    dm.stop_daq(args)


def add_user(args):
    if '--badge' not in sys.argv:
        # No badge given on the command line — use the last stored badge from config
        if not args.badge:
            log.info("No --badge entered and no badge stored in config.")
            log.info("   To add a user run: experiment add-user --badge <badge#>")
            return
        name = dm.get_user_name_by_badge(args.badge)
        display = f"{name}, badge {args.badge}" if name else f"badge {args.badge}"
        log.info(f"   No --badge entered, using last stored badge: {display}")
        # Check if already on the experiment before prompting
        current_users = dm.make_username_list(args)
        if 'd{:d}'.format(args.badge) in current_users:
            log.info(f"   {display} is already on the experiment.")
            log.info("   To add a different user run: experiment add-user --badge <badge#>")
            return
        if not message.yes_or_no('   *** Confirm? Yes or No'):
            log.info("   To add a different user run: experiment add-user --badge <badge#>")
            return
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

    lfname = logs_home + 'experiment_' + datetime.strftime(datetime.now(), "%Y-%m-%d_%H:%M:%S") + '.log'
    log.setup_custom_logger(lfname)


    parser = argparse.ArgumentParser()
    parser.add_argument('--config', **config.SECTIONS['general']['config'])
    globus_params = config.GLOBUS_PARAMS

    cmd_parsers = [
        ('config',       set_config,  globus_params,  "Create configuration file"),
        ('show',         show,        globus_params,  "Show status"),
        ('create',       create,      globus_params,  "Create a DM experiment and add users"),
        ('list-users',   list_users,  globus_params,  "List the users on the current DM experiment"),
        ('add-user',     add_user,    globus_params,  "Add a user to the current DM experiment by badge number"),
        ('remove-user',  remove_user, globus_params,  "Remove a user from the current DM experiment"),
        ('email',        email,       globus_params,  "Send email with link to all users on the proposal"),
    ]

    subparsers = parser.add_subparsers(title="Commands", metavar='')

    for cmd, func, sections, text in cmd_parsers:
        cmd_params = config.Params(sections=sections)
        cmd_parser = subparsers.add_parser(cmd, help=text, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        cmd_parser = cmd_params.add_arguments(cmd_parser)
        cmd_parser.set_defaults(_func=func)

    # daq subgroup
    daq_params = config.Params(sections=globus_params)
    daq_p = subparsers.add_parser('daq', help='Data acquisition commands')
    daq_p.set_defaults(_func=lambda args: daq_p.print_help())
    daq_sub = daq_p.add_subparsers(title='daq commands', metavar='')

    daq_start_p = daq_sub.add_parser('start', help='Start automated real-time file transfer to Sojourner',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    daq_params.add_arguments(daq_start_p)
    daq_start_p.set_defaults(_func=start_daq)

    daq_stop_p = daq_sub.add_parser('stop', help='Stop all running file transfers for the current experiment',
                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    daq_params.add_arguments(daq_stop_p)
    daq_stop_p.set_defaults(_func=stop_daq)

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

    # show only displays config values — no PVs or scheduling needed
    if args._func == show:
        args._func(args)
        return

    #Init here, otherwise we don't have parameters to do the following updates
    if args.manual:
        now = datetime.now()
        if args.date:
            try:
                ref_date = datetime.strptime(args.date, '%Y-%m')
            except ValueError:
                log.error(f"Invalid --date '{args.date}': expected format is yyyy-mm (e.g. 2025-12)")
                sys.exit(1)
        else:
            ref_date = now
        args.year_month    = ref_date.strftime('%Y-%m')
        args.pi_last_name  = args.name
        args.gup_number    = '0'
        args.gup_title     = args.title
        args.manual_start  = ref_date.strftime('%d-%b-%y')
        args.manual_end    = (ref_date + timedelta(days=14)).strftime('%d-%b-%y')
        log.info(f"Manual experiment: {args.year_month}-{args.pi_last_name}, "
                 f"title: {args.gup_title}")
    else:
        # Query the scheduling system for the run containing today+set days
        beamtimes = scheduling.list_beamtimes(args)
        if not beamtimes:
            log.error("No beamtimes found for the current run")
            sys.exit(1)
        elif len(beamtimes) == 1:
            bt = beamtimes[0]
            log.info(f"Found 1 beamtime in run {bt['run_name']}: GUP {bt['gup_number']} "
                     f"(PI: {bt['pi_last_name']}, {bt['gup_title'][:60]})")
        else:
            log.info(f"Found {len(beamtimes)} beamtimes in run {beamtimes[0]['run_name']}:")
            for i, bt in enumerate(beamtimes):
                print(f"  [{i}] GUP {bt['gup_number']} - PI: {bt['pi_last_name']} - "
                      f"{bt['gup_title'][:70]}")
                print(f"       {bt['start_time']} to {bt['end_time']}")
            while True:
                try:
                    choice = input(f"\nSelect beamtime [0-{len(beamtimes)-1}] or 'q' to quit: ").strip()
                    if choice.lower() == 'q':
                        log.info("No beamtime selected. Exiting.")
                        return
                    choice = int(choice)
                    if 0 <= choice < len(beamtimes):
                        bt = beamtimes[choice]
                        break
                    print(f"Please enter a number between 0 and {len(beamtimes)-1}")
                except (ValueError, EOFError):
                    print("Invalid input. Please enter a number or 'q' to quit.")

        args.year_month    = bt['year_month']
        args.pi_last_name  = bt['pi_last_name']
        args.pi_first_name = bt['pi_first_name']
        args.pi_institution = bt['pi_institution']
        args.pi_email      = bt['pi_email']
        args.pi_badge      = bt['pi_badge']
        args.gup_number    = bt['gup_number']
        args.gup_title     = bt['gup_title']
        log.info(f"Run {bt['run_name']}: {args.year_month}, "
                 f"PI: {args.pi_last_name}, GUP: {args.gup_number}")

        log.info("Write experiment metadata to tomoScan PVs?")
        if message.yes_or_no('   *** Yes or No'):
            try:
                from experiment import pv
                pv.write_experiment_info(args)
                log.info("   Metadata written to tomoScan PVs")
            except Exception as e:
                log.warning("   Could not write to tomoScan PVs: %s" % str(e))

    required_args = {
        'year_month': args.year_month,
        'pi_last_name': args.pi_last_name,
        'gup_number': args.gup_number,
        'gup_title': args.gup_title,
    }

    for name, value in required_args.items():
        if not value:
            log.error(f"Error: Required argument '{name}' is missing or empty. "
                      f"Check that tomoscan with prefix {args.tomoscan_prefix} is up and running")
            sys.exit(1)

    # Save CLI parameters to config file so they become the new defaults
    # Reset one-time flags so they don't persist into the next invocation.
    # Save and restore the values that the function still needs after the write.
    manual_for_run        = args.manual
    manual_badges_for_run = args.badges
    args.set    = 0
    args.manual = False
    args.date   = config.SECTIONS['globus']['date']['default']
    args.name   = config.SECTIONS['globus']['name']['default']
    args.title  = config.SECTIONS['globus']['title']['default']
    args.badges = config.SECTIONS['globus']['badges']['default']
    sections = config.GLOBUS_PARAMS
    config.write(args.config, args=args, sections=sections)
    args.manual  = manual_for_run
    args.badges  = manual_badges_for_run

    if args._func == create:
        exp_name = directories.make_directory_name(args)
        log.info('Create summary:')
        log.info('   Experiment : %s/%s' % (args.year_month, exp_name))
        log.info('   Title      : %s' % args.gup_title)
        if manual_for_run:
            log.info('   Start      : %s' % args.manual_start)
            log.info('   End        : %s' % args.manual_end)
        if not message.yes_or_no('   *** Confirm? Yes or No'):
            log.info('   Aborted.')
            return
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
