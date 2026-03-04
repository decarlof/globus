==========
EXPERIMENT
==========

`experiment <https://github.com/xray-imaging/globus>`_ is a CLI tool for managing beamline experiments at the
`Advanced Photon Source (APS) <https://www.aps.anl.gov/>`_. It bridges two systems:

- **APS scheduling system** — looks up proposals, PI names, GUP numbers, and experimenter lists
- **APS Data Management (Sojourner) + Globus** — creates DM experiments, manages users, starts automated file transfers, and sends data-access emails

Optionally, after selecting an experiment it can write the PI and proposal metadata directly to
the beamline `TomoScan <https://tomoscan.readthedocs.io/en/latest/tomoScanApp.html#user-information>`_
EPICS process variables (replacing a separate ``dmagic tag`` step).

CLI parameters are saved to ``~/experiment.conf`` after each run and reused as defaults.


How experiment identity works
------------------------------

Every command (except ``show``) begins by identifying *which* experiment to act on.
There are two modes:

.. list-table::
   :header-rows: 1
   :widths: 20 30 50

   * - Mode
     - Flag
     - How the experiment is identified
   * - **Scheduled**
     - *(default)*
     - Queries the APS scheduling system for all beamtimes in the run that contains
       today (``--set 0``) or today ± N days (``--set N``). If more than one beamtime
       is found an interactive menu lets you pick one.
   * - **Manual**
     - ``--manual``
     - You supply ``--name``, ``--title``, and ``--badges`` directly. No scheduling
       system lookup is performed. Use this for commissioning runs or any experiment
       without a GUP proposal.

After identification, the DM experiment name is built as ``YYYY-MM-<PIlastname>-<GUP#>``
(e.g. ``2026-02-Li-1018528`` or ``2026-02-BrainNoemi-0`` for manual).


Commands at a Glance
--------------------

.. list-table::
   :header-rows: 1
   :widths: 22 78

   * - Command
     - What it does
   * - ``experiment show``
     - Display current configuration (reads ``~/experiment.conf`` only — no network calls)
   * - ``experiment create``
     - Select an experiment → create it on Sojourner → add users from the scheduling
       system (or from ``--badges`` for manual). Optionally writes metadata to tomoScan PVs.
   * - ``experiment list-users``
     - Select an experiment → list users currently on its Sojourner DM experiment
   * - ``experiment add-user --badge N``
     - Select an experiment → add badge N to its Sojourner DM experiment
   * - ``experiment remove-user``
     - Select an experiment → interactively remove a user from its Sojourner DM experiment
   * - ``experiment email``
     - Select an experiment → send a data-access email with Globus link to all users
   * - ``experiment daq start``
     - Select an experiment → start automated real-time file transfer to Sojourner
   * - ``experiment daq stop``
     - Select an experiment → stop all running file transfers

**"Select an experiment"** means: query the APS scheduling system for the run containing
today (or today + ``--set`` days), display the beamtime list, and prompt you to pick one.
For manual mode it means: use the ``--name`` / ``--title`` / ``--badges`` you supply.


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

**Scheduled experiment (current run)**::

    $ experiment create           # pick from today's beamtimes, create DM experiment, add users
    $ experiment list-users       # verify user list
    $ experiment add-user --badge 123456    # add a user not on the proposal
    $ experiment remove-user      # interactively remove a user
    $ experiment daq start        # begin automated data transfer
    $ experiment email            # send data-access email with Globus link
    $ experiment daq stop         # end of experiment

Each command independently asks you to select the beamtime. If there is only one
beamtime in the run it is selected automatically.

**Past or future experiment**::

    $ experiment create --set -1  # select from beamtimes in the run containing yesterday
    $ experiment email --set -1   # same run offset applies to any command

**Commissioning / no proposal**::

    $ experiment create --manual --name BrainNoemi \
                        --title "Commissioning: Brain samples for Noemi" \
                        --badges 49734,218262,293228,324083,329663
    $ experiment list-users --manual --name BrainNoemi
    $ experiment add-user  --manual --name BrainNoemi --badge 51803

**Backdated manual experiment (e.g. forgot to run create in December)**::

    $ experiment create --manual --date 2025-12 --name BrainNoemi \
                        --title "Commissioning: Brain samples for Noemi" \
                        --badges 49734,218262,293228,324083,329663


Command Reference
-----------------

For a full list of options::

    $ experiment -h


show
~~~~

Display the current configuration without touching the scheduling system::

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

After the experiment is identified, a summary is shown and confirmation is requested before
anything is created. After creating the experiment you are also asked whether to write
the PI and proposal metadata to the tomoScan EPICS PVs (equivalent to running ``dmagic tag``).

----

**Scheduled experiment** — select from all beamtimes in today's run::

    $ experiment create

If multiple beamtimes are found, an interactive menu is shown::

    Found 14 beamtimes in run 2026-1:
      [0] GUP 1008279 - PI: Pickering - A Partner User Proposal...
           2026-03-05T08:00:00-06:00 to 2026-03-07T08:00:00-06:00
      [1] GUP 1011300 - PI: Morris - Assessing fungal-mineral...
           2026-04-15T09:00:00-05:00 to 2026-04-17T10:00:00-05:00
      ...
    Select beamtime [0-13] or 'q' to quit: 6

    Write experiment metadata to tomoScan PVs? (Y/N): y

Enter ``q`` to exit without creating an experiment.

----

**Past or future experiment** — ``--set N`` shifts the lookup date by N days from today::

    $ experiment create --set -1     # run containing yesterday
    $ experiment create --set 30     # run containing ~30 days from now

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

Optional PI detail flags for the tomoScan PV write::

    --first-name    PI first name  (default: empty)
    --institution   PI institution (default: empty)
    --email         PI email       (default: empty)

To backdate a manual experiment to a specific month, use ``--date`` in ``yyyy-mm`` format::

    $ experiment create --manual --date 2025-12 --name BrainNoemi \
                        --title "Commissioning: Brain samples for Noemi" \
                        --badges 49734,324083,293228,329663

This creates experiment ``2025-12-BrainNoemi-0`` with start date ``01-Dec-25``.

Note: ``--manual``, ``--date``, ``--name``, ``--title``, ``--badges``, ``--first-name``,
``--institution``, and ``--email`` are one-time flags and are not saved to ``experiment.conf``.


list-users
~~~~~~~~~~

Select an experiment, then list the users currently on its Sojourner DM experiment::

    $ experiment list-users

Example output::

    User Pavel D. Shevchenko, badge 218262 is on the DM experiment
    User Francesco De Carlo, badge 49734 is on the DM experiment
    User Alberto Mittone, badge 329663 is on the DM experiment

If no DM experiment exists yet, falls back to listing users from the APS scheduling system proposal.


add-user
~~~~~~~~

Select an experiment, then add a user to it by badge number::

    $ experiment add-user --badge 51803

Badge numbers can be found from ``experiment list-users`` output or the APS people directory.

Running without ``--badge`` shows the last used badge (stored in ``experiment.conf``) and asks for
confirmation::

    $ experiment add-user
       No --badge entered, using last stored badge: Kamel Fezzaa, badge 51803
       *** Confirm? Yes or No (Y/N): y
       Added user Kamel Fezzaa to the DM experiment

If the user is already on the experiment::

       Kamel Fezzaa, badge 51803 is already on the experiment.
       To add a different user run: experiment add-user --badge <badge#>


remove-user
~~~~~~~~~~~

Select an experiment, then interactively remove a user from it::

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

Select an experiment, then send an email to all users on its Sojourner DM experiment
with data access instructions and a direct Globus link to their data::

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

Select an experiment, then start automated real-time file transfer from the analysis computer
to Sojourner::

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

Select an experiment, then stop all running automated file transfers for it::

    $ experiment daq stop

Queries the DM system, finds all DAQs matching the current experiment in ``running`` state, stops
each one, and reports how many were stopped. Logs a warning if no active DAQs are found.


Troubleshooting
---------------

+---------------------------------------------------+---------------------------------------------------------------+
| Symptom                                           | Cause / Fix                                                   |
+===================================================+===============================================================+
| ``No beamtimes found for the current run``        | The scheduling system returned no results. Check network      |
|                                                   | access to beam-api.aps.anl.gov and your credentials file.     |
+---------------------------------------------------+---------------------------------------------------------------+
| ``No beamtime from proposal X found``             | GUP is set but not scheduled at this beamline for this run.   |
|                                                   | Check the GUP or use ``--manual``.                            |
+---------------------------------------------------+---------------------------------------------------------------+
| ``Could not write to tomoScan PVs``               | pyepics not installed, or the tomoScan IOC is offline.        |
|                                                   | The rest of the command completes normally.                    |
+---------------------------------------------------+---------------------------------------------------------------+
| ``experiment create --set`` shows stale info      | ``--manual`` flag was saved to config. Fixed: one-time flags  |
|                                                   | are now always reset after each run.                          |
+---------------------------------------------------+---------------------------------------------------------------+
| Globus link in email points to wrong path         | ``globus_server_top_dir`` should be the filesystem path only; |
|                                                   | it is not included in the Globus URL.                         |
+---------------------------------------------------+---------------------------------------------------------------+
