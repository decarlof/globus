import datetime
import pytz

from epics import PV
from experiment import log


def init_general_PVs(args):

    global_PVs = {}

    global_PVs['ExperimentYearMonth'] = PV(args.tomoscan_prefix + 'ExperimentYearMonth')
    global_PVs['UserName']            = PV(args.tomoscan_prefix + 'UserName')
    global_PVs['UserLastName']        = PV(args.tomoscan_prefix + 'UserLastName')
    global_PVs['UserInstitution']     = PV(args.tomoscan_prefix + 'UserInstitution')
    global_PVs['UserBadge']           = PV(args.tomoscan_prefix + 'UserBadge')
    global_PVs['UserEmail']           = PV(args.tomoscan_prefix + 'UserEmail')
    global_PVs['ProposalNumber']      = PV(args.tomoscan_prefix + 'ProposalNumber')
    global_PVs['ProposalTitle']       = PV(args.tomoscan_prefix + 'ProposalTitle')
    global_PVs['UserInfoUpdate']      = PV(args.tomoscan_prefix + 'UserInfoUpdate')

    return global_PVs



def write_experiment_info(args):
    '''Write experiment metadata retrieved from the scheduling system to the tomoScan EPICS PVs.
    Equivalent to running `dmagic tag`.
    '''
    global_PVs = init_general_PVs(args)

    now = datetime.datetime.now(pytz.timezone('America/Chicago')).isoformat()

    global_PVs['ExperimentYearMonth'].put(args.year_month)
    global_PVs['UserName'].put(args.pi_first_name)
    global_PVs['UserLastName'].put(args.pi_last_name)
    global_PVs['UserInstitution'].put(args.pi_institution)
    global_PVs['UserBadge'].put(args.pi_badge)
    global_PVs['UserEmail'].put(args.pi_email)
    global_PVs['ProposalNumber'].put(str(args.gup_number))
    global_PVs['ProposalTitle'].put(args.gup_title)
    global_PVs['UserInfoUpdate'].put(now)

    log.info('   ExperimentYearMonth : %s' % args.year_month)
    log.info('   UserName            : %s' % args.pi_first_name)
    log.info('   UserLastName        : %s' % args.pi_last_name)
    log.info('   UserInstitution     : %s' % args.pi_institution)
    log.info('   UserBadge           : %s' % args.pi_badge)
    log.info('   UserEmail           : %s' % args.pi_email)
    log.info('   ProposalNumber      : %s' % args.gup_number)
    log.info('   ProposalTitle       : %s' % args.gup_title)
    log.info('   UserInfoUpdate      : %s' % now)
