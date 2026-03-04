from epics import PV
from experiment import log
import numpy as np


def init_general_PVs(args):

    global_PVs = {}

    global_PVs['ExperimentYearMonth'] = PV(args.tomoscan_prefix + 'ExperimentYearMonth')
    global_PVs['UserEmail'] = PV(args.tomoscan_prefix + 'UserEmail')
    global_PVs['UserLastName'] = PV(args.tomoscan_prefix + 'UserLastName')
    global_PVs['ProposalNumber'] = PV(args.tomoscan_prefix + 'ProposalNumber')
    global_PVs['ProposalTitle'] = PV(args.tomoscan_prefix + 'ProposalTitle')

    return global_PVs

def update_experiment_info(args):
    '''Retrieve the information for the current experiment from the beamline PVs.
    Returns:
    Year and month of the current experiment as a string in the format %Y-%m
    Last name of the PI as a string
    Proposal number as a string
    '''
    global_PVs = init_general_PVs(args)

    year_month = global_PVs['ExperimentYearMonth'].get(as_string=True)
    pi_last_name = global_PVs['UserLastName'].get(as_string=True)
    pi_email = global_PVs['UserEmail'].get(as_string=True)
    gup_number = global_PVs['ProposalNumber'].get(as_string=True)
    gup_title = global_PVs['ProposalTitle'].get(as_string=True)
    return year_month, pi_last_name, gup_number, gup_title


def write_experiment_info(args):
    '''Write experiment metadata retrieved from the scheduling system to the tomoScan EPICS PVs.'''
    global_PVs = init_general_PVs(args)
    global_PVs['ExperimentYearMonth'].put(args.year_month)
    global_PVs['UserLastName'].put(args.pi_last_name)
    global_PVs['ProposalNumber'].put(str(args.gup_number))
    global_PVs['ProposalTitle'].put(args.gup_title)
    log.info('   ExperimentYearMonth : %s' % args.year_month)
    log.info('   UserLastName        : %s' % args.pi_last_name)
    log.info('   ProposalNumber      : %s' % args.gup_number)
    log.info('   ProposalTitle       : %s' % args.gup_title)


