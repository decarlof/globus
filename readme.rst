======
GLOBUS
======


`globus <https://github.com/xray-imaging/globus>`_ is a Python script that interfaces with the APS Data Management System (e.g. Sojourner) and a generic `Globus server <https://www.globus.org/>`_ (e.g. Petrel). It reads beamline PVs to set up a Data Management experiment, manage users for the experiment, send e-mails to users with information on how to access their data, and manage automated data transfer (termed DAQs) from the analysis machine to Sojourner.

For the current experiment, year-month, pi_last_name and proposal information are read from the EPICS PVs served by `TomoScan <https://tomoscan.readthedocs.io/en/latest/tomoScanApp.html#user-information>`_. For past experiments, the ``--set`` option retrieves experiment information directly from the APS scheduling system. For manual experiments (e.g., commissioning, staff tests), the ``--manual`` option allows creating DM experiments without a scheduling system entry.

CLI parameters are saved to ``~/globus.conf`` after each run, so they only need to be specified once.


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

- Create a default configuration file with ``globus config``
- Customize the email to the user by editing the `message <https://github.com/xray-imaging/globus/blob/master/globus/message.txt>`_
- All CLI parameters are saved to ``~/globus.conf`` and reused as defaults on subsequent runs
- On first use, pass the beamline-specific parameters to save them::

    $ globus show --tomoscan-prefix 2bmb:TomoScan: --globus-server-name sojourner --beamline 2-BM-A,B --experiment-type 2BM


Usage
-----

::

    globus -h
        Show help and list available commands


config
~~~~~~

Create a ``globus.conf`` default configuration file::

    $ globus config


show
~~~~

Show the current configuration::

    $ globus show

On first use, pass the beamline-specific parameters. These are saved to ``~/globus.conf`` and used as defaults for all subsequent commands::

    $ globus show --tomoscan-prefix 2bmb:TomoScan: --globus-server-name sojourner --beamline 2-BM-A,B


init
~~~~

Initialize data management by creating a DM experiment and adding users.

**Current experiment** — reads experiment info (year-month, PI last name, GUP number, title) from EPICS PVs::

    $ globus init

**Past experiment** — retrieves experiment info from the APS scheduling system. The ``--set`` option shifts the date by the specified number of days. If multiple beamtimes are found in that run, an interactive menu lets you select the correct one::

    $ globus init --set -60

Example output::

    Found 14 beamtimes in past run 2026-1:
      [0] GUP 1008279 - PI: Pickering - A Partner User Proposal...
           2026-03-05T08:00:00-06:00 to 2026-03-07T08:00:00-06:00
      [1] GUP 1011300 - PI: Morris - Assessing fungal-mineral...
           2026-04-15T09:00:00-05:00 to 2026-04-17T10:00:00-05:00
      ...
    Select beamtime [0-13]: 6

**Manual experiment** — creates a DM experiment without a scheduling system entry. Useful for commissioning, staff tests, or internal experiments::

    $ globus init --manual

This creates an experiment named ``YYYY-MM-Staff-0`` with today's date as start and two weeks from today as end. The beamline contacts are added automatically.

Customize the manual experiment name and title::

    $ globus init --manual --manual-name DeCarlo --manual-title "Alignment test"

Add specific users by badge number (comma-separated). Beamline contacts are always added automatically::

    $ globus init --manual --manual-name AI-testing --manual-title "AI centering test" --manual-badges 49734,324083,293228,329663

If the experiment already exists, ``init`` detects it and skips creation, then ensures all specified users are added.


list_users
~~~~~~~~~~

List the users on the current DM experiment. Shows name and badge number for each user::

    $ globus list_users

For a past experiment, use ``--set`` to select the run::

    $ globus list_users --set -60

If the DM experiment exists, it lists users from the DM system. If no DM experiment is found, it falls back to listing users from the scheduling system proposal.

Example output (DM experiment exists)::

    User Justin P. Miner, badge 332286 is on the DM experiment
    User Francesco De Carlo, badge 49734 is on the DM experiment
    User Anthony D. Rollett, badge 203861 is on the DM experiment

Example output (no DM experiment, falls back to scheduling system)::

    No DM experiment found for: 2026-03-Li-1018528
    Listing users from the scheduling system proposal (GUP 1018528)
       User Li, Jingjing, badge 242722, jul572@engr.psu.edu (PI)


add_user
~~~~~~~~

Add a user to the current DM experiment by badge number::

    $ globus add_user --badge 332286

The badge number can be found from ``globus list_users`` output or from the APS people directory.


remove_user
~~~~~~~~~~~

Remove a user from the current DM experiment by badge number::

    $ globus remove_user --badge 332286


email
~~~~~

Send an email to all users on the current experiment with information on how to access their data on Sojourner::

    $ globus email

The email message can be customized by editing the message file specified in the configuration.


start_daq
~~~~~~~~~

Start automated file upload from the analysis computer to the DM server (Sojourner). The DM system monitors the specified data directory on the analysis machine for incoming files and transfers them automatically::

    $ globus start_daq

This is useful for real-time data transfer during an experiment. The analysis machine directory and credentials are configured in the ``[local]`` section of ``~/globus.conf``.


stop_daq
~~~~~~~~

Stop all running automated file uploads (DAQs) for the current experiment::

    $ globus stop_daq


Typical Workflow
----------------

Current experiment::

    $ globus init
    $ globus list_users
    $ globus add_user --badge 123456
    $ globus remove_user --badge 987654
    $ globus start_daq
    $ globus email
    $ globus stop_daq

Past experiment::

    $ globus init --set -60
    $ globus list_users --set -60

Manual experiment (commissioning/staff)::

    $ globus init --manual --manual-name AI-testing --manual-title "AI centering test" --manual-badges 49734,324083,293228,329663
    $ globus list_users
