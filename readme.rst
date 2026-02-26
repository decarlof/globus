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


Usage
-----

::

    globus -h
        Show help and list available commands

    globus config
        Create a globus.conf default configuration file

    globus show
        Show the current configuration

    globus init
        Initialize data management.
        Creates an experiment in the DM system and adds users.
        For current experiment (reads from EPICS PVs):
            $ globus init
        For past experiment (retrieves from APS scheduling system):
            $ globus init --set -60
        For manual experiment (no scheduling system entry):
            $ globus init --manual
            $ globus init --manual --manual-name Staff --manual-title "Commissioning" --manual-badges 49734,324083

    globus list_users
        Lists the users (name and badge numbers) on the DM experiment.
        Falls back to the scheduling system if no DM experiment exists.
            $ globus list_users
            $ globus list_users --set -60

    globus add_user --badge 123456
        Adds the user with badge 123456 to the current DM experiment

    globus remove_user --badge 123456
        Removes the user with badge 123456 from the current DM experiment

    globus email
        E-mails all users on the experiment with information on how to access their data

    globus start_daq
        Starts automated file upload from the analysis computer to the DM server.
        Monitors the analysis machine directory for incoming files and transfers
        them automatically to Sojourner.

    globus stop_daq
        Stops automated file uploads for this experiment


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
