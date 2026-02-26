import datetime as dt
import pytz
import json
import requests
from globus import log
from globus import authorize

__author__ = "Alan L Kastengren"
__copyright__ = "Copyright (c) 2025, UChicago Argonne, LLC."
__version__ = "0.0.1"
__docformat__ = 'restructuredtext en'


def current_run(args):
    """
    Determine the current run

    Returns
    -------
    run : string
        Run name 2024-1.
    """
    auth = authorize.basic(args.credentials)
    if auth is None:
        log.error('Cannot authenticate to scheduling system')
        return None
    end_point         = "beamline-scheduling/sched-api/run/getAllRuns"
    api_url = args.url + "/" + end_point 

    reply = requests.get(api_url, auth=auth)

    if reply.status_code == 404:
        log.error("No response from the restAPI. Error: %s" % reply.status_code)    
        return None
    reply = reply.json()
    start_times = [item['startTime'] for item in reply]
    end_times   = [item['endTime']   for item in reply]
    runs        = [item['runName']   for item in reply]
    time_now = dt.datetime.now(pytz.timezone('America/Chicago')) + dt.timedelta(args.set)
    for i in range(len(start_times)):
        prop_start = dt.datetime.fromisoformat(fix_iso(start_times[i]))
        prop_end   = dt.datetime.fromisoformat(fix_iso(end_times[i]))
        if prop_start <= time_now and prop_end >= time_now:
            return runs[i]
    return None


def get_beamtime(gup_number, args):
    """
    Get the data for the beamtime in the current run with the same GUP
    number as the one in the target PVs.
    
    Parameters
    -----------
    gup_number : int
        The GUP number for the current proposal

    Returns
    -------
    item : dict-like object
        Beamtime information for the target beamtime
    """
    auth = authorize.basic(args.credentials)
    end_point = "beamline-scheduling/sched-api/activity/findByRunNameAndBeamlineId"
    run_name = current_run(args)
    api_url = (args.url + '/' + end_point + 
                '/' + run_name + '/' + args.beamline)
    reply = requests.get(api_url, auth=auth)
    if reply.status_code == 404:
        log.error("No response from the restAPI. Error: %s" % reply.status_code)    
        return None
    for item in reply.json():
        # log.info(item['beamtime']['proposal'])
        # log.info(item['beamtime']['proposal']['gupId'])
        if int(item['beamtime']['proposal']['gupId']) == int(gup_number):
            log.info("Beamtime for GUP {0} found in run {1}".format(gup_number, run_name))
            return item
    log.error(f"No beamtime from proposal {gup_number} found in run {run_name}")
    return None


def list_beamtimes(args):
    """
    List all beamtimes for the run determined by the --set offset.


    Returns
    -------
    list of dict
        Each dict contains: gup_number, pi_last_name, gup_title, year_month, start_time, end_time
    """
    auth = authorize.basic(args.credentials)
    if auth is None:
        log.error('Cannot authenticate to scheduling system')
        return []
    end_point = "beamline-scheduling/sched-api/activity/findByRunNameAndBeamlineId"
    run_name = current_run(args)
    if run_name is None:
        log.error("Could not determine run for the given --set offset")
        return []
    api_url = (args.url + '/' + end_point +
                '/' + run_name + '/' + args.beamline)
    reply = requests.get(api_url, auth=auth)
    if reply.status_code == 404:
        log.error("No response from the restAPI. Error: %s" % reply.status_code)
        return []

    beamtimes = []
    for item in reply.json():
        proposal = item['beamtime']['proposal']
        # Find the PI
        pi_last_name = 'Unknown'
        for exp in proposal.get('experimenters', []):
            if exp.get('piFlag') == 'Y':
                pi_last_name = exp['lastName']
                break

        start_dt = dt.datetime.fromisoformat(fix_iso(item['startTime']))
        year_month = start_dt.strftime('%Y-%m')

        beamtimes.append({
            'gup_number': str(proposal['gupId']),
            'gup_title': proposal.get('proposalTitle', ''),
            'pi_last_name': pi_last_name,
            'year_month': year_month,
            'start_time': item['startTime'],
            'end_time': item['endTime'],
            'run_name': run_name,
        })

    return beamtimes

def fix_iso(s):
    """
    This is a temporary fix until timezone is returned as -05:00 instead of -0500

    Parameters
    ----------
    s : string
        Like "2022-07-31T01:51:05-0400"

    Returns
    -------
    s : string
        Like "2022-07-31T01:51:05-04:00"

    """
    pos = len("2022-07-31T01:51:05-0400") - 2 # take off end "00"
    if len(s) == pos:                 # missing minutes completely
        s += ":00"
    elif s[pos:pos+1] != ':':         # missing UTC offset colon
        s = f"{s[:pos]}:{s[pos:]}"
    return s
