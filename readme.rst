======
GLOBUS
======


`globus <https://github.com/xray-imaging/globus>`_ is a Python script that interfaces with the APS Data Management System (e.g. Sojourner) and a generic `Globus server <https://www.globus.org/>`_ (e.g. Petrel). It reads beamline PVs to set up a Data Management experiment, manage users for the experiment, send e-mails to users with information on how to get their data from Sojourner or Petrel, and manage automated data transfer (termed DAQs) from the analysis machine to Sojourner.

For the current experiment, year-month, pi_last_name and proposal information are read from the EPICS PVs defined in the 'epics' section of the `globus config file <https://github.com/xray-imaging/globus/blob/master/globus/config.py>`_. By default these PVs are served by `TomoScan <https://tomoscan.readthedocs.io/en/latest/tomoScanApp.html#user-information>`_ and can be automatically updated for the current user using `dmagic tag <https://dmagic.readthedocs.io/en/latest/source/usage.html>`_.

For past experiments, the ``--set`` option shifts the date lookup into the past, retrieving experiment information directly from the APS scheduling system. For manual experiments (e.g., commissioning, staff tests), the ``--manual`` option allows creating DM experiments without a scheduling system entry.


Dependencies
------------

`globus` dependencies are listed in the envs/requirements.txt file. 


Installation
------------

Install from `Anaconda <https://www.anaconda.com/distribution/>`_ python3.x, then install globus::

    $ git clone https://github.com/xray-imaging/globus.git
    $ cd globus
    $ pip install .


Environment configuration
-------------------------

There are also several environment variables that must be set for the DM API to work properly. They can be found in the /home/dm_bm/etc/dm.conda.setup.sh script. Copy everything in this script to your account's ~/.bashrc file.


Configuration
-------------

On first run, globus saves the CLI parameters to ``~/globus.conf`` so they become the new defaults for subsequent runs. This means you only need to pass parameters like ``--tomoscan-prefix`` and ``--globus-server-name`` once.

- Create a default configuration file::

    $ globus config

- Customize the email to the user by editing the `message <https://github.com/xray-imaging/globus/blob/master/globus/message.txt>`_
- For automatic retrieval of user information from the APS scheduling system see `dmagic tag <https://dmagic.readthedocs.io/en/latest/source/usage.html>`_.


Usage
-----

::

    $ globus -h

    Commands:
        config       Create configuration file
        show         Show status
        init         Initialize data management
        list_users   List the users on the current DM experiment
        add_user     Add a user to the current DM experiment by badge number
        remove_user  Remove a user from the current DM experiment by badge number
        email        Send email with link to all users on the proposal
        start_daq    Start DM DAQ
        stop_daq     Stop DM DAQ


show
~~~~

Show the current configuration::

    $ globus show

On first use, pass the beamline-specific parameters::

    $ globus show --tomoscan-prefix 2bmb:TomoScan: --globus-server-name sojourner

These values are saved to ``~/globus.conf`` and used as defaults for all subsequent commands.


init
~~~~

Initialize data management by creating a DM experiment and adding users.

**Current experiment** (reads experiment info from EPICS PVs)::

    $ globus init

**Past experiment** (retrieves info from the APS scheduling system). The ``--set`` option shifts the date by the specified number of days. If multiple beamtimes are found in that run, an interactive menu lets you select the correct one::

    $ globus init --set -60

Example output::

    Found 14 beamtimes in past run 2026-1:
      [0] GUP 1008279 - PI: Pickering - A Partner User Proposal to Continue...
           2026-03-05T08:00:00-06:00 to 2026-03-07T08:00:00-06:00
      [1] GUP 1011300 - PI: Morris - Assessing fungal-mineral interfaces...
           2026-04-15T09:00:00-05:00 to 2026-04-17T10:00:00-05:00
      ...

    Select beamtime [0-13]: 6

**Manual experiment** (no scheduling system entry required, e.g., commissioning or staff tests)::

    $ globus init --manual

This creates an experiment named ``YYYY-MM-Staff-0`` with today's date as start and two weeks from today as end. The beamline contacts are added automatically.

Customize the manual experiment::

    $ globus init --manual --manual-name DeCarlo --manual-title "Alignment test"

Add specific users by badge number::

    $ globus init --manual --manual-name AI-testing --manual-title "AI centering test" --manual-badges 49734,324083,293228,329663

If the experiment already exists, ``init`` detects it and skips creation, then ensures all users are added.


list_users
~~~~~~~~~~

List the users on the current DM experiment::

    $ globus list_users

For a past experiment, use ``--set`` to select the run. If the DM experiment exists, it lists users from the DM system. If not, it falls back to listing users from the scheduling system proposal::

    $ globus list_users --set -60

Example output (DM experiment exists)::

    User Justin P. Miner, badge 332286 is on the DM experiment
    User Francesco De Carlo, badge 49734 is on the DM experiment
    User Anthony D. Rollett, badge 203861 is on the DM experiment

Example output (no DM experiment, falls back to scheduling)::

    No DM experiment found for: 2026-03-Li-1018528
    Listing users from the scheduling system proposal (GUP 1018528)
       User Li, Jingjing, badge 242722, jul572@engr.psu.edu (PI)


add_user
~~~~~~~~

Add a user to the current DM experiment by badge number::

    $ globus add_user --badge 332286


remove_user
~~~~~~~~~~~

Remove a user from the current DM experiment by badge number::

    $ globus remove_user --badge 332286


email
~~~~~

Send an email to all users on the current experiment with information on how to access their data::

    $ globus email


start_daq / stop_daq
~~~~~~~~~~~~~~~~~~~~

Start or stop automated file upload from the analysis computer to the DM server::

    $ globus start_daq
    $ globus stop_daq


Typical Workflow
----------------

Current experiment::

    $ globus init
    $ globus list_users
    $ globus add_user --badge 123456
    $ globus remove_user --badge 987654
    $ globus email
    $ globus start_daq

Past experiment::

    $ globus init --set -60
    $ globus list_users --set -60

Manual experiment (commissioning/staff)::

    $ globus init --manual --manual-name AI-testing --manual-title "AI centering test" --manual-badges 49734,324083,293228,329663
    $ globus list_users

For Globus server (Petrel)::

    $ globus init
    $ globus email
