import datetime

from dm import ExperimentDsApi, UserDsApi, ExperimentDaqApi
from dm.common.exceptions.objectAlreadyExists import ObjectAlreadyExists

from globus import log
from globus import directories
from globus import scheduling

exp_api = ExperimentDsApi()
user_api = UserDsApi()
daq_api = ExperimentDaqApi()
oee = ObjectAlreadyExists

__author__ = "Alan L Kastengren"
__copyright__ = "Copyright (c) 2020, UChicago Argonne, LLC."
__version__ = "0.0.1"
__docformat__ = 'restructuredtext en'


def make_dm_username_list(args):
    '''Make a list of DM usernames 'd+badge#' from the current proposal (GUP number).
    '''
    log.info('Making a list of DM system usernames from target proposal')
    target_prop = scheduling.get_beamtime(str(args.gup_number), args)
    if target_prop is None:
        return None
    users = target_prop['beamtime']['proposal']['experimenters']
    log.info('   Adding the primary beamline contact')
    user_ids = {'d' + str(args.primary_beamline_contact_badge)}
    log.info('   Adding the secondary beamline contact')
    user_ids.add('d' + str(args.secondary_beamline_contact_badge))
    for u in users:
        log.info('   Adding user {0}, {1}, badge {2}'.format(
                    u['lastName'], u['firstName'], u['badge']))
        user_ids.add('d' + str(u['badge']))
    return user_ids


def log_exp_users(exp_name):
    '''Log the full name and badge of each user currently on a DM experiment.'''
    try:
        exp_obj = exp_api.getExperimentByName(exp_name)
        username_list = exp_obj.get('experimentUsernameList', [])
        if not username_list:
            log.info('   No users currently on this experiment')
            return
        for uname in username_list:
            try:
                user_obj = user_api.getUserByUsername(uname)
                log.info('   {:s}, badge {:s}'.format(
                    make_pretty_user_name(user_obj), user_obj['badge']))
            except Exception:
                log.info('   {:s} (could not retrieve details)'.format(uname))
    except Exception as e:
        log.warning('   Could not query DM experiment: %s' % str(e))


def make_username_list(args):
    '''Make a list of the usernames from the current DM experiment.
    '''
    log.info('Making a list of DM system usernames from current DM experiment')
    exp_name = directories.make_directory_name(args)
    try:
        exp_obj = exp_api.getExperimentByName(exp_name)
        return exp_obj.get('experimentUsernameList', [])
    except Exception as e:
        log.error('No such experiment in the DM system: {:s}'.format(exp_name))
        log.error('   Error: %s' % str(e))
        log.error('   Have you run globus create yet?')
        return []


def make_user_email_list(username_list):
    '''Make a list of e-mail addresses from a list of DM usernames.
    
    Parameters
    ----------

    username_list : list
        list of DM usernames, each of which is in the form 'd+badge#'.

    Returns
    -------

    list 
        e-mail addresses.
    '''

    email_list = []
    for u in username_list:
        try:
            user_obj = user_api.getUserByUsername(u)
            email_list.append(user_obj['email'])
            log.info('   Added email {:s} for user {:s}'.format(email_list[-1], u))
        except Exception as e:
            log.warning('   Problem loading email for user {:s}: {:s}'.format(u, str(e)))
    return email_list
        

def create_experiment(args):
    '''Creates a new DM experiment on Sojourner.

    Returns
    -------
    Experiment object
    '''
    dir_name = directories.make_directory_name(args)
    log.info('See if there is already a DM experiment')
    try:
        old_exp = exp_api.getExperimentByName(dir_name)
        log.warning('   Experiment already exists: %s' % old_exp['name'])
        return old_exp
    except Exception as e:
        error_msg = str(e)
        if 'does not exist' in error_msg:
            log.info('   Experiment does not exist yet, will create it')
        else:
            log.error('   Could not query DM system: %s' % error_msg)
            return None

    log.info('Creating new DM experiment: {0:s}/{1:s}'.format(args.year_month, dir_name))

    if args.manual:
        # Manual experiment: use dates from args
        start_date = args.manual_start
        end_date   = args.manual_end
    else:
        # Scheduled experiment: get dates from scheduling system
        target_beamtime = scheduling.get_beamtime(args.gup_number, args)
        if target_beamtime is None:
            log.error('  Could not find beamtime for GUP %s. '
                      'If this is a commissioning run with no proposal, use '
                      '"globus create --manual --name <LastName> '
                      '--title <Title> --badges <badge1,badge2,...>"'
                      % args.gup_number)
            return None
        start_datetime = datetime.datetime.strptime(
                            target_beamtime['startTime'],
                            '%Y-%m-%dT%H:%M:%S%z')
        end_datetime = datetime.datetime.strptime(
                            target_beamtime['endTime'],
                            '%Y-%m-%dT%H:%M:%S%z')
        start_date = start_datetime.strftime('%d-%b-%y')
        end_date   = end_datetime.strftime('%d-%b-%y')

    try:
        new_exp = exp_api.addExperiment(dir_name, typeName = args.experiment_type,
                            description = args.gup_title, rootPath = args.year_month,
                            startDate = start_date,
                            endDate = end_date)
        log.info('   Experiment successfully created: %s' % new_exp['name'])
        return new_exp
    except oee:
        log.warning('   Experiment already exists (caught on create). Retrieving: %s' % dir_name)
        return exp_api.getExperimentByName(dir_name)
    except Exception as e:
        log.error('   Could not create DM experiment: %s' % str(e))
        return None



def add_users(exp_obj, username_list):
    '''Add a list of users to a DM experiment
    '''
    existing_unames = exp_obj.get('experimentUsernameList', [])
    for uname in username_list:
        try:
            user_obj = user_api.getUserByUsername(uname)
        except Exception as e:
            log.error('   Could not find user {:s}: {:s}'.format(uname, str(e)))
            continue
        if uname in existing_unames:
            log.warning('   User {:s} is already a user for the experiment'.format(
                        make_pretty_user_name(user_obj)))
            continue
        try:
            user_api.addUserExperimentRole(uname, 'User', exp_obj['name'])
            log.info('   Added user {0:s} to the DM experiment'.format(
                        make_pretty_user_name(user_obj)))
        except Exception as e:
            log.error('   Could not add user {:s}: {:s}'.format(uname, str(e)))

def start_daq(args):
    '''Starts the data managememnt (DM) data acquisition (DAQ) system. 
    In this mode of operation, the DM system will monitor specified data directory 
    for incoming files, and will transfer data automatically.
    Alternative is to upload files after experiment is done.
    '''
    exp_name = directories.make_directory_name(args)
    analysis_dir_name = directories.create_analysis_dir_name(args)
    log.info('Check that the directory exists on the analysis machine')
    dir_check = directories.check_local_directory(args.analysis, analysis_dir_name) 
    if dir_check == 2:
        log.info('   Need to make the analysis machine directory')
        mkdir_response = directories.create_local_directory(
                            args.analysis, analysis_dir_name)
        if mkdir_response:
            log.error('   Unknown response when creating analysis machine directory.  Exiting')
            return
    elif dir_check == 0:
        log.info('   Directory already exists')
    else:
        log.warning('   Unknown response when checking for analysis machine directory.  Exiting')
        return    
    dm_dir_name = "@{0:s}:{1:s}".format(args.analysis,analysis_dir_name)
    log.info('Check to make sure the appropriate DAQ is not already running.')
    try:
        current_daqs = daq_api.listDaqs()
    except Exception as e:
        log.error('   Could not list DAQs: %s' % str(e))
        return
    for d in current_daqs:
        if (d['experimentName'] == exp_name and d['status'] == 'running'
            and d['dataDirectory'] == dm_dir_name):
            log.warning('   DAQ is already running.  Returning.')
            return
    log.info('Add a DAQ to experiment {:s}'.format(exp_name))
    try:
        daq_obj = daq_api.startDaq(exp_name, dm_dir_name)
    except Exception as e:
        log.error('   Could not start DAQ: %s' % str(e))


def stop_daq(args):
    '''Stops the currently running DM DAQ. 
    '''
    exp_name = directories.make_directory_name(args)
    log.info('Stopping all DM DAQs for experiment {:s}'.format(exp_name))
    try:
        daqs = daq_api.listDaqs()
    except Exception as e:
        log.error('   Could not list DAQs: %s' % str(e))
        return
    removed_daq_counter = 0
    for d in daqs:
        if d['experimentName'] == exp_name and d['status'] == 'running':
            log.info('   Found running DAQ for this experiment.  Stopping now.')
            try:
                daq_api.stopDaq(d['experimentName'],d['dataDirectory'])
                removed_daq_counter += 1
            except Exception as e:
                log.error('   Could not stop DAQ: %s' % str(e))
    if removed_daq_counter == 0:
        log.info('   No active DAQs for this experiment were found')


def get_user_name_by_badge(badge):
    '''Return the pretty name for a badge number, or None if not found.'''
    try:
        user_obj = user_api.getUserByUsername('d{:d}'.format(badge))
        return make_pretty_user_name(user_obj)
    except Exception:
        return None


def add_user(args):
    '''Add a user to the DM experiment.
    '''
    exp_name = directories.make_directory_name(args)
    try:
        exp_obj = exp_api.getExperimentByName(exp_name)
    except Exception as e:
        log.error('   No appropriate DM experiment found: %s' % str(e))
        return
    try:
        add_users(exp_obj, ['d{:d}'.format(args.badge)])
    except Exception as e:
        log.error('   Problem adding the user: %s' % str(e))
    

def remove_user(args):
    '''Remove a user from the DM experiment.
    Shows the current user list and lets the operator select by number.
    '''
    exp_name = directories.make_directory_name(args)
    try:
        exp_obj = exp_api.getExperimentByName(exp_name)
    except Exception as e:
        log.error('   No appropriate DM experiment found: %s' % str(e))
        return

    username_list = exp_obj.get('experimentUsernameList', [])
    if not username_list:
        log.info('   No users on this experiment')
        return

    # Resolve full user info for each username
    users = []
    for uname in username_list:
        try:
            user_obj = user_api.getUserByUsername(uname)
            users.append((uname, user_obj))
        except Exception:
            users.append((uname, None))

    # Display numbered list
    log.info('Users on experiment %s:' % exp_name)
    for i, (uname, user_obj) in enumerate(users):
        if user_obj:
            print('  [{:d}] {:s}, badge {:s}'.format(
                i, make_pretty_user_name(user_obj), user_obj['badge']))
        else:
            print('  [{:d}] {:s} (could not retrieve details)'.format(i, uname))

    # Prompt for selection
    while True:
        try:
            choice = input(f"\nSelect user to remove [0-{len(users)-1}] or 'q' to quit: ").strip()
            if choice.lower() == 'q':
                log.info('   No user removed.')
                return
            choice = int(choice)
            if 0 <= choice < len(users):
                break
            print(f"Please enter a number between 0 and {len(users)-1}")
        except (ValueError, EOFError):
            print("Invalid input. Please enter a number or 'q' to quit.")

    dm_username, user_obj = users[choice]
    name = make_pretty_user_name(user_obj) if user_obj else dm_username
    log.info('Removing user {:s} from experiment {:s}'.format(name, exp_name))
    try:
        user_api.deleteUserExperimentRole(dm_username, 'User', exp_name)
        log.info('   User {:s} successfully removed'.format(name))
    except Exception as e:
        log.error('   Problem removing the user: %s' % str(e))


def list_users(args):
    '''Lists the users on the current experiment in a nice format.
    First tries the DM experiment. If not found, lists users from the
    scheduling system proposal.
    '''
    exp_name = directories.make_directory_name(args)

    # Try the DM experiment first
    try:
        exp_obj = exp_api.getExperimentByName(exp_name)
        log.info('Listing the users on the DM experiment: %s' % exp_name)
        username_list = exp_obj.get('experimentUsernameList', [])
        if len(username_list) == 0:
            log.info('   No users for this experiment')
            return
        for uname in username_list:
            try:
                user_obj = user_api.getUserByUsername(uname)
                log.info('   User {0:s}, badge {1:s} is on the DM experiment'.format(
                            make_pretty_user_name(user_obj), user_obj['badge']))
            except Exception as e:
                log.warning('   Could not retrieve info for user {:s}: {:s}'.format(uname, str(e)))
        return
    except Exception as e:
        log.warning('   Could not query DM experiment: %s' % str(e))

    # No DM experiment found — list users from the scheduling system proposal
    log.info('No DM experiment found for: %s' % exp_name)
    log.info('Listing users from the scheduling system proposal (GUP %s)' % args.gup_number)
    target_prop = scheduling.get_beamtime(str(args.gup_number), args)
    if target_prop is None:
        log.error('   No beamtime found for GUP %s' % args.gup_number)
        return
    users = target_prop['beamtime']['proposal']['experimenters']
    if len(users) == 0:
        log.info('   No users on this proposal')
        return
    for u in users:
        pi_flag = ' (PI)' if u.get('piFlag') == 'Y' else ''
        log.info('   User {0:s}, {1:s}, badge {2:s}, {3:s}{4:s}'.format(
                    u['lastName'], u['firstName'], u['badge'],
                    u.get('email', 'no email'), pi_flag))


def list_users_this_dm_exp(args):
    '''Provide a list of user names for this DM expt 
    in the form "d(badge#)"
    '''
    log.info('Listing the users on the DM experiment')
    exp_name = directories.make_directory_name(args)
    try:
        exp_obj = exp_api.getExperimentByName(exp_name)
    except Exception as e:
        log.error('   No appropriate DM experiment found: %s' % str(e))
        return None
    username_list = exp_obj.get('experimentUsernameList', [])
    if len(username_list) == 0:
        log.info('   No users for this experiment')
        return None
    else:
        print(username_list)
        return username_list


def make_pretty_user_name(user_obj):
    '''Makes a printable name from the DM user object
    '''
    output_string = ''
    if 'firstName' in user_obj:
        output_string += user_obj['firstName'] + ' '
    if 'middleName' in user_obj:
        output_string += user_obj['middleName'] + ' '
    if 'lastName' in user_obj:
        output_string += user_obj['lastName']
    return output_string


def make_data_link(args):
    '''Makes the http link to the data. This link will be included in the email sent to the 
    users so they can access their data directly.
    '''
    exp_name = directories.make_directory_name(args)
    try:
        target_exp = exp_api.getExperimentByName(exp_name)
    except Exception as e:
        log.error('   Could not find DM experiment for data link: %s' % str(e))

    output_link = 'https://app.globus.org/file-manager?origin_id='
    output_link += args.globus_server_uuid
    output_link += '&origin_path='
    target_dir = '/' + args.year_month + '/' + exp_name + '/\n'
    output_link += target_dir.replace('/','%2F')
    return output_link
