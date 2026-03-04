======
GLOBUS
======

`globus <https://github.com/xray-imaging/globus>`_ is a CLI tool for managing beamline experiments at the
`Advanced Photon Source (APS) <https://www.aps.anl.gov/>`_. It bridges three systems:

- **EPICS** — reads experiment metadata from beamline `TomoScan <https://tomoscan.readthedocs.io/en/latest/tomoScanApp.html#user-information>`_ process variables
- **APS scheduling system** — looks up proposals, PI names, GUP numbers, and experimenter lists
- **APS Data Management (Sojourner) + Globus** — creates DM experiments, manages users, starts automated file transfers, and sends data-access emails

CLI parameters are saved to ``~/globus.conf`` after each run and reused as defaults, so they only need to be specified once.


Commands at a Glance
--------------------

+------------------+-------------------------------------------------------------+
| Command          | Purpose                                                     |
+==================+=============================================================+
| ``show``         | Display current configuration                               |
+------------------+-------------------------------------------------------------+
| ``init``         | Create a DM experiment on Sojourner and add users           |
+------------------+-------------------------------------------------------------+
| ``list_users``   | List users on the current DM experiment                     |
+------------------+-------------------------------------------------------------+
| ``add_user``     | Add a user to the DM experiment by badge number             |
+------------------+-------------------------------------------------------------+
| ``remove_user``  | Remove a user from the DM experiment                        |
+------------------+-------------------------------------------------------------+
| ``email``        | Send data-access email with Globus link to all users        |
+------------------+-------------------------------------------------------------+
| ``start_daq``    | Start automated real-time file transfer to Sojourner        |
+------------------+-------------------------------------------------------------+
| ``stop_daq``     | Stop all running file transfers for the current experiment  |
+------------------+-------------------------------------------------------------+


Dependencies
------------

Dependency list: ``envs/requirements.txt``.


Installation
------------

Install from `Anaconda <https://www.anaconda.com/distribution/>`_ python3.x::

    $ git clone https://github.com/xray-imaging/globus.git
    $ cd globus
    $ pip install .


Environment Configuration
-------------------------

Several environment variables are required for the DM API. Copy the contents of
``/home/dm_bm/etc/dm.conda.setup.sh`` into your ``~/.bashrc``.


Configuration
-------------

Create a default configuration file::

    $ globus config

On first use, pass beamline-specific parameters. These are saved to ``~/globus.conf`` and used as
defaults for all subsequent commands::

    $ globus show --tomoscan-prefix 2bmb:TomoScan: --beamline 2-BM-A,B --experiment-type 2BM \
                  --globus-server-uuid 054a0877-97ca-4d80-947f-47ca522b173e \
                  --globus-server-top-dir /gdata/dm/2BM \
                  --primary-beamline-contact-badge 218262 \
                  --primary-beamline-contact-email pshevchenko@anl.gov \
                  --secondary-beamline-contact-badge 49734 \
                  --secondary-beamline-contact-email decarlo@anl.gov \
                  --globus-message-file message-2bm.txt


Typical Workflows
-----------------

**Scheduled experiment (EPICS PVs loaded by the control system)**::

    $ globus init           # create DM experiment, add users from scheduling system
    $ globus list_users     # verify user list
    $ globus add_user --badge 123456    # add a user not on the proposal
    $ globus remove_user
    $ globus start_daq      # begin automated data transfer
    $ globus email          # send data-access email with Globus link
    $ globus stop_daq       # end of experiment

**Past or future experiment**::

    $ globus init --set -1  # select from list of beamtimes in previous run
    $ globus email

**Commissioning / no proposal (first time)**::

    $ globus init --manual --manual-name BrainNoemi \
                  --manual-title "Commissioning: Brain samples for Noemi" \
                  --manual-badges 49734,218262,293228,324083,329663
    $ globus list_users
    $ globus add_user --badge 51803     # add a user after the fact
    $ globus email

**Backdated manual experiment (e.g. forgot to run init in December)**::

    $ globus init --manual --manual-date 2025-12 --manual-name BrainNoemi \
                  --manual-title "Commissioning: Brain samples for Noemi" \
                  --manual-badges 49734,218262,293228,324083,329663
    $ globus email

**Commissioning / no proposal (experiment already exists, adding a user)**::

    $ globus add_user --badge 51803
    $ globus init                       # re-run to see updated user list and confirm
       *** Yes or No (Y/N): y
    $ globus email


Command Reference
-----------------

For a full list of options::

    $ globus -h


show
~~~~

Display the current configuration without touching EPICS PVs or the scheduling system::

    $ globus show

Example output::

    2026-02-28 10:00:45,359 - Globus status start
    2026-02-28 10:00:45,359 -   beamline         2-BM-A,B
    2026-02-28 10:00:45,359 -   globus_server_uuid 054a0877-97ca-4d80-947f-47ca522b173e
    ...
    2026-02-28 10:00:45,359 - Globus status end


init
~~~~

Create a DM experiment on Sojourner and add users to it. Experiments are named
``YYYY-MM-<PIlastname>-<GUP#>`` (e.g. ``2026-02-Li-1018528``).

``globus init`` operates in one of four mutually exclusive modes:

+---------------------------+------------------------------------------+-------------------------------------------+
| Mode                      | Command                                  | Source of experiment info                 |
+===========================+==========================================+===========================================+
| Current experiment        | ``globus init``                          | EPICS PVs (TomoScan)                      |
+---------------------------+------------------------------------------+-------------------------------------------+
| Past/future experiment    | ``globus init --set -1``                 | APS scheduling system (date offset)       |
+---------------------------+------------------------------------------+-------------------------------------------+
| Manual (no proposal)      | ``globus init --manual``                 | Command-line arguments                    |
+---------------------------+------------------------------------------+-------------------------------------------+
| Manual with past date     | ``globus init --manual --manual-date``   | Command-line arguments                    |
+---------------------------+------------------------------------------+-------------------------------------------+

The user list is sourced as follows:

+-----------------------+------------------------------------------------------+
| Mode                  | Source of users                                      |
+=======================+======================================================+
| ``--manual``          | Beamline contacts + ``--manual-badges`` list         |
+-----------------------+------------------------------------------------------+
| All others            | APS scheduling system (experimenter list for GUP)    |
+-----------------------+------------------------------------------------------+

----

**Current experiment** — reads ``year_month``, ``pi_last_name``, ``gup_number``, and ``gup_title``
from the EPICS PVs served by TomoScan (prefix configured via ``--tomoscan-prefix``)::

    $ globus init

Requirements:

- The TomoScan EPICS IOC must be running
- The PVs ``ExperimentYearMonth``, ``UserLastName``, ``ProposalNumber``, ``ProposalTitle`` must be set
- The GUP number must correspond to a beamtime in the APS scheduling system

**Error: EPICS IOC is down or PVs are empty**::

    ERROR - Required argument 'year_month' is missing or empty.
            Check that tomoscan with prefix 2bmb:TomoScan: is up and running

**Error: GUP number not found in the scheduling system** (e.g. commissioning with GUP=0)::

    ERROR - GUP number is empty — the EPICS PVs are not set for a scheduled experiment.
    ERROR - To create a manual experiment (e.g. for commissioning) run:
    ERROR -   globus init --manual --manual-name <LastName> --manual-title <Title> --manual-badges <badge1,badge2,...>

**Special case: commissioning experiment already exists in DM**

If a manual experiment was previously created and the EPICS PVs still point to it,
``globus init`` detects the existing experiment, shows its user list, and prompts::

    WARNING -    GUP 0 not found in the scheduling system.
    WARNING -    However, DM experiment '2026-02-BrainNoemi-0' already exists with these users:
    INFO    -    Pavel D. Shevchenko, badge 218262
    INFO    -    Francesco De Carlo, badge 49734
    INFO    -    Alberto Mittone, badge 329663
    WARNING -    Do you want to use its existing users?
       *** Yes or No (Y/N): y

Answering ``y`` confirms the existing user list and adds any missing users.
Answering ``n`` exits and prints the command to add a new user::

       *** Yes or No (Y/N): n
    INFO -    To add a user run: globus add_user --badge <badge#>

----

**Past or future experiment** — retrieves experiment info from the APS scheduling system.
The ``--set`` value shifts the lookup date by that many days from today::

    $ globus init --set -1     # previous run
    $ globus init --set 30     # run ~30 days from now

If multiple beamtimes are found, an interactive menu is shown::

    Found 14 beamtimes in past run 2026-1:
      [0] GUP 1008279 - PI: Pickering - A Partner User Proposal...
           2026-03-05T08:00:00-06:00 to 2026-03-07T08:00:00-06:00
      [1] GUP 1011300 - PI: Morris - Assessing fungal-mineral...
           2026-04-15T09:00:00-05:00 to 2026-04-17T10:00:00-05:00
      ...
    Select beamtime [0-13] or 'q' to quit: 6

Enter ``q`` to exit without creating an experiment.

Note: ``--set`` is a one-time flag and is not saved to ``globus.conf``.

----

**Manual experiment** — creates a DM experiment without a scheduling system entry.
Useful for commissioning, staff tests, or internal work::

    $ globus init --manual --manual-name <LastName> --manual-title "<Title>" --manual-badges <badge1,badge2,...>

Example::

    $ globus init --manual --manual-name BrainNoemi --manual-title "Commissioning: Brain samples for Noemi" \
                  --manual-badges 49734,324083,293228,329663

- Experiment name: ``YYYY-MM-<manual-name>-0`` (e.g. ``2026-02-BrainNoemi-0``)
- Start date: today (or ``--manual-date`` if provided); end date: 14 days later
- Users: beamline contacts (always added) + ``--manual-badges`` list
- If the experiment already exists, users are re-confirmed and any new ones added

To backdate a manual experiment to a specific month, use ``--manual-date`` in ``yyyy-mm`` format::

    $ globus init --manual --manual-date 2025-12 --manual-name BrainNoemi \
                  --manual-title "Commissioning: Brain samples for Noemi" \
                  --manual-badges 49734,324083,293228,329663

This creates experiment ``2025-12-BrainNoemi-0`` with start date ``01-Dec-25``.
An invalid format (e.g. ``12/2025``) produces an error and exits.

Note: ``--manual``, ``--manual-date``, ``--manual-name``, ``--manual-title``, ``--manual-badges``
are one-time flags and are not saved to ``globus.conf``.


list_users
~~~~~~~~~~

List the users currently on the DM experiment (name and badge number)::

    $ globus list_users

Example output::

    User Pavel D. Shevchenko, badge 218262 is on the DM experiment
    User Francesco De Carlo, badge 49734 is on the DM experiment
    User Alberto Mittone, badge 329663 is on the DM experiment

If no DM experiment exists, falls back to listing users from the APS scheduling system proposal.
Supports ``--set`` for past/future experiments::

    $ globus list_users --set -1


add_user
~~~~~~~~

Add a user to the current DM experiment by badge number::

    $ globus add_user --badge 51803

Badge numbers can be found from ``globus list_users`` output or the APS people directory.

Running without ``--badge`` shows the last used badge (stored in ``globus.conf``) and asks for
confirmation::

    $ globus add_user
       No --badge entered, using last stored badge: Kamel Fezzaa, badge 51803
       *** Confirm? Yes or No (Y/N): y
       Added user Kamel Fezzaa to the DM experiment

If the user is already on the experiment::

    $ globus add_user
       Kamel Fezzaa, badge 51803 is already on the experiment.
       To add a different user run: globus add_user --badge <badge#>


remove_user
~~~~~~~~~~~

Remove a user from the current DM experiment. Running the command shows a numbered list of current
users and prompts for a selection::

    $ globus remove_user

Example output::

    Users on experiment 2026-02-BrainNoemi-0:
      [0] Pavel D. Shevchenko, badge 218262
      [1] Alberto Mittone, badge 324083
      [2] Songyuan Tang, badge 329663
      [3] Viktor Nikitin, badge 293228
      [4] Francesco De Carlo, badge 49734
      [5] Kamel Fezzaa, badge 51803

    Select user to remove [0-5] or 'q' to quit: 5
    Removing user Kamel Fezzaa from experiment 2026-02-BrainNoemi-0
       User Kamel Fezzaa successfully removed

Enter ``q`` to exit without removing anyone.


email
~~~~~

Send an email to all users on the DM experiment with data access instructions and a direct Globus
link to their data::

    $ globus email

The email includes:

- Instructions for creating a Globus account
- A direct Globus file-manager link to the experiment data directory, e.g.::

    https://app.globus.org/file-manager?origin_id=054a0877-97ca-4d80-947f-47ca522b173e&origin_path=%2F2026-02%2F2026-02-BrainNoemi-0%2F

- Links to beamline documentation, reconstruction tools, and data viewers

The email template is specified by ``--globus-message-file`` in the config (e.g. ``message-2bm.txt``).
The ``Data link:`` line in the template is automatically replaced with the correct Globus URL at send
time. A preview of the full email is shown before sending and confirmation is requested.


start_daq
~~~~~~~~~

Start automated real-time file transfer from the analysis computer to Sojourner::

    $ globus start_daq

What it does:

1. Builds the data directory path on the analysis machine from the experiment name and
   ``analysis_top_dir`` (e.g. ``/local/data/2026-02-Li-1018528``)
2. SSHes into the analysis machine and creates the directory if it does not exist
3. Registers a DAQ with the DM system pointing to that directory
4. The DM system watches the directory in real time and transfers new files to Sojourner as they appear

If a DAQ for the same experiment and directory is already running, exits without starting a duplicate.

Prerequisites:

- SSH access to the analysis machine must be configured (key-based, no password prompt)
- ``analysis``, ``analysis_top_dir``, and ``analysis_user_name`` must be set in ``~/globus.conf``


stop_daq
~~~~~~~~

Stop all running automated file transfers for the current experiment::

    $ globus stop_daq

Queries the DM system, finds all DAQs matching the current experiment in ``running`` state, stops
each one, and reports how many were stopped. Logs a warning if no active DAQs are found.


Troubleshooting
---------------

+---------------------------------------------------+---------------------------------------------------------------+
| Symptom                                           | Cause / Fix                                                   |
+===================================================+===============================================================+
| ``Required argument 'year_month' is missing``     | TomoScan IOC is down or PVs not set. Start the IOC or use    |
|                                                   | ``--manual`` / ``--set``.                                     |
+---------------------------------------------------+---------------------------------------------------------------+
| ``GUP number is empty``                           | ``ProposalNumber`` PV is empty. Load a proposal into the      |
|                                                   | control system or use ``--manual``.                           |
+---------------------------------------------------+---------------------------------------------------------------+
| ``No beamtime from proposal X found``             | GUP is set but not scheduled at this beamline for this run.   |
|                                                   | Check the GUP or use ``--manual``.                            |
+---------------------------------------------------+---------------------------------------------------------------+
| ``globus init --set`` shows stale manual info     | ``--manual`` flag was saved to config. Fixed: one-time flags  |
|                                                   | are now always reset after each run.                          |
+---------------------------------------------------+---------------------------------------------------------------+
| Globus link in email points to wrong path         | ``globus_server_top_dir`` should be the filesystem path only; |
|                                                   | it is not included in the Globus URL.                         |
+---------------------------------------------------+---------------------------------------------------------------+
