==========
EXPERIMENT
==========

`experiment <https://github.com/xray-imaging/globus>`_ is a CLI tool for managing beamline experiments at the
`Advanced Photon Source (APS) <https://www.aps.anl.gov/>`_. It bridges three systems:

- **EPICS** — reads experiment metadata from beamline `TomoScan <https://tomoscan.readthedocs.io/en/latest/tomoScanApp.html#user-information>`_ process variables
- **APS scheduling system** — looks up proposals, PI names, GUP numbers, and experimenter lists
- **APS Data Management (Sojourner) + Globus** — creates DM experiments, manages users, starts automated file transfers, and sends data-access emails

CLI parameters are saved to ``~/experiment.conf`` after each run and reused as defaults, so they only need to be specified once.


Commands at a Glance
--------------------

+----------------------+-------------------------------------------------------------+
| Command              | Purpose                                                     |
+======================+=============================================================+
| ``show``             | Display current configuration                               |
+----------------------+-------------------------------------------------------------+
| ``create``           | Create a DM experiment on Sojourner and add users           |
+----------------------+-------------------------------------------------------------+
| ``list-users``       | List users on the current DM experiment                     |
+----------------------+-------------------------------------------------------------+
| ``add-user``         | Add a user to the DM experiment by badge number             |
+----------------------+-------------------------------------------------------------+
| ``remove-user``      | Remove a user from the DM experiment                        |
+----------------------+-------------------------------------------------------------+
| ``email``            | Send data-access email with Globus link to all users        |
+----------------------+-------------------------------------------------------------+
| ``daq start``        | Start automated real-time file transfer to Sojourner        |
+----------------------+-------------------------------------------------------------+
| ``daq stop``         | Stop all running file transfers for the current experiment  |
+----------------------+-------------------------------------------------------------+


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

    $ experiment config

On first use, pass beamline-specific parameters. These are saved to ``~/experiment.conf`` and used as
defaults for all subsequent commands::

    $ experiment show --tomoscan-prefix 2bmb:TomoScan: --beamline 2-BM-A,B --experiment-type 2BM \
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

    $ experiment create           # create DM experiment, add users from scheduling system
    $ experiment list-users       # verify user list
    $ experiment add-user --badge 123456    # add a user not on the proposal
    $ experiment remove-user
    $ experiment daq start        # begin automated data transfer
    $ experiment email            # send data-access email with Globus link
    $ experiment daq stop         # end of experiment

**Past or future experiment**::

    $ experiment create --set -1  # select from list of beamtimes in previous run
    $ experiment email

**Commissioning / no proposal (first time)**::

    $ experiment create --manual --name BrainNoemi \
                        --title "Commissioning: Brain samples for Noemi" \
                        --badges 49734,218262,293228,324083,329663
    $ experiment list-users
    $ experiment add-user --badge 51803     # add a user after the fact
    $ experiment email

**Backdated manual experiment (e.g. forgot to run create in December)**::

    $ experiment create --manual --date 2025-12 --name BrainNoemi \
                        --title "Commissioning: Brain samples for Noemi" \
                        --badges 49734,218262,293228,324083,329663
    $ experiment email

**Commissioning / no proposal (experiment already exists, adding a user)**::

    $ experiment add-user --badge 51803
    $ experiment create                     # re-run to see updated user list and confirm
       *** Yes or No (Y/N): y
    $ experiment email


Command Reference
-----------------

For a full list of options::

    $ experiment -h


show
~~~~

Display the current configuration without touching EPICS PVs or the scheduling system::

    $ experiment show

Example output::

    2026-02-28 10:00:45,359 - Experiment status start
    2026-02-28 10:00:45,359 -   beamline         2-BM-A,B
    2026-02-28 10:00:45,359 -   globus_server_uuid 054a0877-97ca-4d80-947f-47ca522b173e
    ...
    2026-02-28 10:00:45,359 - Experiment status end


create
~~~~~~

Create a DM experiment on Sojourner and add users to it. Experiments are named
``YYYY-MM-<PIlastname>-<GUP#>`` (e.g. ``2026-02-Li-1018528``).

``experiment create`` operates in one of four mutually exclusive modes:

+---------------------------+----------------------------------------------+-------------------------------------------+
| Mode                      | Command                                      | Source of experiment info                 |
+===========================+==============================================+===========================================+
| Current experiment        | ``experiment create``                        | EPICS PVs (TomoScan)                      |
+---------------------------+----------------------------------------------+-------------------------------------------+
| Past/future experiment    | ``experiment create --set -1``               | APS scheduling system (date offset)       |
+---------------------------+----------------------------------------------+-------------------------------------------+
| Manual (no proposal)      | ``experiment create --manual``               | Command-line arguments                    |
+---------------------------+----------------------------------------------+-------------------------------------------+
| Manual with past date     | ``experiment create --manual --date``        | Command-line arguments                    |
+---------------------------+----------------------------------------------+-------------------------------------------+

The user list is sourced as follows:

+-----------------------+------------------------------------------------------+
| Mode                  | Source of users                                      |
+=======================+======================================================+
| ``--manual``          | Beamline contacts + ``--badges`` list                |
+-----------------------+------------------------------------------------------+
| All others            | APS scheduling system (experimenter list for GUP)    |
+-----------------------+------------------------------------------------------+

----

**Current experiment** — reads ``year_month``, ``pi_last_name``, ``gup_number``, and ``gup_title``
from the EPICS PVs served by TomoScan (prefix configured via ``--tomoscan-prefix``)::

    $ experiment create

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
    ERROR -   experiment create --manual --name <LastName> --title <Title> --badges <badge1,badge2,...>

**Special case: commissioning experiment already exists in DM**

If a manual experiment was previously created and the EPICS PVs still point to it,
``experiment create`` detects the existing experiment, shows its user list, and prompts::

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
    INFO -    To add a user run: experiment add-user --badge <badge#>

----

**Past or future experiment** — retrieves experiment info from the APS scheduling system.
The ``--set`` value shifts the lookup date by that many days from today::

    $ experiment create --set -1     # previous run
    $ experiment create --set 30     # run ~30 days from now

If multiple beamtimes are found, an interactive menu is shown::

    Found 14 beamtimes in past run 2026-1:
      [0] GUP 1008279 - PI: Pickering - A Partner User Proposal...
           2026-03-05T08:00:00-06:00 to 2026-03-07T08:00:00-06:00
      [1] GUP 1011300 - PI: Morris - Assessing fungal-mineral...
           2026-04-15T09:00:00-05:00 to 2026-04-17T10:00:00-05:00
      ...
    Select beamtime [0-13] or 'q' to quit: 6

Enter ``q`` to exit without creating an experiment.

Note: ``--set`` is a one-time flag and is not saved to ``experiment.conf``.

----

**Manual experiment** — creates a DM experiment without a scheduling system entry.
Useful for commissioning, staff tests, or internal work::

    $ experiment create --manual --name <LastName> --title "<Title>" --badges <badge1,badge2,...>

Example::

    $ experiment create --manual --name BrainNoemi --title "Commissioning: Brain samples for Noemi" \
                        --badges 49734,324083,293228,329663

- Experiment name: ``YYYY-MM-<name>-0`` (e.g. ``2026-02-BrainNoemi-0``)
- Start date: today (or ``--date`` if provided); end date: 14 days later
- Users: beamline contacts (always added) + ``--badges`` list
- If the experiment already exists, users are re-confirmed and any new ones added

To backdate a manual experiment to a specific month, use ``--date`` in ``yyyy-mm`` format::

    $ experiment create --manual --date 2025-12 --name BrainNoemi \
                        --title "Commissioning: Brain samples for Noemi" \
                        --badges 49734,324083,293228,329663

This creates experiment ``2025-12-BrainNoemi-0`` with start date ``01-Dec-25``.
An invalid format (e.g. ``12/2025``) produces an error and exits.

Note: ``--manual``, ``--date``, ``--name``, ``--title``, ``--badges`` are one-time flags and are
not saved to ``experiment.conf``.


list-users
~~~~~~~~~~

List the users currently on the DM experiment (name and badge number)::

    $ experiment list-users

Example output::

    User Pavel D. Shevchenko, badge 218262 is on the DM experiment
    User Francesco De Carlo, badge 49734 is on the DM experiment
    User Alberto Mittone, badge 329663 is on the DM experiment

If no DM experiment exists, falls back to listing users from the APS scheduling system proposal.
Supports ``--set`` for past/future experiments::

    $ experiment list-users --set -1


add-user
~~~~~~~~

Add a user to the current DM experiment by badge number::

    $ experiment add-user --badge 51803

Badge numbers can be found from ``experiment list-users`` output or the APS people directory.

Running without ``--badge`` shows the last used badge (stored in ``experiment.conf``) and asks for
confirmation::

    $ experiment add-user
       No --badge entered, using last stored badge: Kamel Fezzaa, badge 51803
       *** Confirm? Yes or No (Y/N): y
       Added user Kamel Fezzaa to the DM experiment

If the user is already on the experiment::

    $ experiment add-user
       Kamel Fezzaa, badge 51803 is already on the experiment.
       To add a different user run: experiment add-user --badge <badge#>


remove-user
~~~~~~~~~~~

Remove a user from the current DM experiment. Running the command shows a numbered list of current
users and prompts for a selection::

    $ experiment remove-user

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

    $ experiment email

The email includes:

- Instructions for creating a Globus account
- A direct Globus file-manager link to the experiment data directory, e.g.::

    https://app.globus.org/file-manager?origin_id=054a0877-97ca-4d80-947f-47ca522b173e&origin_path=%2F2026-02%2F2026-02-BrainNoemi-0%2F

- Links to beamline documentation, reconstruction tools, and data viewers

The email template is specified by ``--globus-message-file`` in the config (e.g. ``message-2bm.txt``).
The ``Data link:`` line in the template is automatically replaced with the correct Globus URL at send
time. A preview of the full email is shown before sending and confirmation is requested.


daq start
~~~~~~~~~

Start automated real-time file transfer from the analysis computer to Sojourner::

    $ experiment daq start

What it does:

1. Builds the data directory path on the analysis machine from the experiment name and
   ``analysis_top_dir`` (e.g. ``/local/data/2026-02-Li-1018528``)
2. SSHes into the analysis machine and creates the directory if it does not exist
3. Registers a DAQ with the DM system pointing to that directory
4. The DM system watches the directory in real time and transfers new files to Sojourner as they appear

If a DAQ for the same experiment and directory is already running, exits without starting a duplicate.

Prerequisites:

- SSH access to the analysis machine must be configured (key-based, no password prompt)
- ``analysis``, ``analysis_top_dir``, and ``analysis_user_name`` must be set in ``~/experiment.conf``


daq stop
~~~~~~~~

Stop all running automated file transfers for the current experiment::

    $ experiment daq stop

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
| ``experiment create --set`` shows stale info      | ``--manual`` flag was saved to config. Fixed: one-time flags  |
|                                                   | are now always reset after each run.                          |
+---------------------------------------------------+---------------------------------------------------------------+
| Globus link in email points to wrong path         | ``globus_server_top_dir`` should be the filesystem path only; |
|                                                   | it is not included in the Globus URL.                         |
+---------------------------------------------------+---------------------------------------------------------------+
